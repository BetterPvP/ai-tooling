"""Delivery pipeline state for BetterPvP.

Works out which pipeline step a branch is on from git and GitHub, so no session has to remember it. Also backs the
hooks: the session-start report and the guard that locks tests during implementation.

    python .claude/pipeline/pipeline.py status          print the current step
    python .claude/pipeline/pipeline.py overview        list every task in progress
    python .claude/pipeline/pipeline.py session-start   SessionStart hook
    python .claude/pipeline/pipeline.py approve-tests   record the user's approval of the tests, locking them
    python .claude/pipeline/pipeline.py unlock-tests    record the user's agreement to change approved tests
    python .claude/pipeline/pipeline.py guard           PreToolUse hook
    python .claude/pipeline/pipeline.py file-issue --title T --body-file F [--label L ...]

The base branch, repo and board live in config.json next to this file.
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
BASE = CONFIG["base"]
REPO = CONFIG["repo"]
DIFF_LIMIT = CONFIG["diff_limit"]
SKILL = ".claude/skills/pipeline"
# Modules whose src/test holds tooling, such as the convention checker, rather than tests
TOOLING_DIRS = CONFIG.get("tooling_dirs", [])


def main_checkout():
    """The main checkout, also from inside a worktree, so every worktree shares one approvals file."""
    common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                            capture_output=True, text=True).stdout.strip()
    return pathlib.Path(common).parent if common else pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))


state_file = main_checkout().resolve() / ".claude" / "pipeline-state.json"

BRANCH_ISSUE = re.compile(r"^(?:[\w.-]+/)?(\d+)-")
AC_LINE = re.compile(r"^\s*[-*]\s*\[( |x|X)\]\s*\**AC(\d+)\**\s*\[(auto|play)\]", re.M)
AC_ANY = re.compile(r"\bAC(\d+)\**\s*\[(auto|play)\]", re.I)
TESTS_REF = re.compile(r"^\s*Tests:\s*#(\d+)", re.M)

STEP_NAMES = {
    0: "No issue", 1: "Slice", 2: "Spec", 3: "Tests first", 4: "Approve tests", 5: "Implement", 6: "Gates",
    7: "AI review", 8: "Deploy", 9: "Playtest", 10: "Your review", 11: "Merged",
}
STEP_FILES = {1: "1-slice.md", 2: "2-spec.md", 3: "3-tests.md", 5: "5-implement.md", 6: "6-gates.md",
              8: "8-deploy.md", 11: "11-merged.md"}
WAITING = {
    4: "Waiting on the user to approve the tests. Ask them, and record a clear yes with approve-tests.",
    9: "Waiting on the user to playtest on ClansTest-1. Tick each [play] AC in the PR when they report it passing.",
    10: "Waiting on the user's review and merge.",
}


def run(args, cwd, ok_codes=(0,)):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode in ok_codes else None


def load_state():
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state):
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


def branch_issue(cwd):
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    if not branch:
        return None, None
    m = BRANCH_ISSUE.match(branch)
    return branch, int(m[1]) if m else None


def base_commit(cwd):
    return run(["git", "merge-base", "HEAD", f"origin/{BASE}"], cwd)


def test_commits(cwd, base):
    log = run(["git", "log", f"{base}..HEAD", "--format=%H %s"], cwd) or ""
    return [line.split(" ", 1)[0] for line in log.splitlines() if line.split(" ", 1)[-1].startswith("test:")]


def approved_in_history(cwd, issue):
    approved = load_state().get(str(issue), {}).get("tests_approved")
    return bool(approved) and run(["git", "merge-base", "--is-ancestor", approved, "HEAD"], cwd) is not None


def is_test_path(path):
    path = "/" + path.replace("\\", "/")
    return "/src/test/" in path and not any(f"/{d}/src/test/" in path for d in TOOLING_DIRS)


def mentions_tests(command):
    command = command.replace("\\", "/")
    for d in TOOLING_DIRS:
        command = command.replace(f"{d}/src/test", "")
    return "src/test" in command


def tests_locked(cwd):
    """True once this issue's tests, or the earlier issue its body names with `Tests: #n`, are approved."""
    _, issue = branch_issue(cwd)
    if issue is None:
        return False
    source = load_state().get(str(issue), {}).get("tests_from")
    return approved_in_history(cwd, issue) or (source is not None and approved_in_history(cwd, source))


def non_test_lines(cwd, base):
    total = 0
    for line in (run(["git", "diff", "--numstat", base], cwd) or "").splitlines():
        added, removed, path = (line.split("\t") + ["", ""])[:3]
        if is_test_path(path) or "/translations/" in path or not added.isdigit():
            continue
        total += int(added) + int(removed)
    return total


def status(cwd):
    """Returns (step, branch, issue, notes)."""
    branch, issue = branch_issue(cwd)
    if branch is None:
        return None
    if issue is None:
        return 0, branch, None, [f"Branch `{branch}` has no issue number. Pipeline branches are `<issue>-<slug>` off `{BASE}`."]

    notes = []
    base = base_commit(cwd)
    if base:
        size = non_test_lines(cwd, base)
        if size > DIFF_LIMIT:
            notes.append(f"Diff is {size} non-test lines, over the {DIFF_LIMIT} limit. Propose a split to the user.")

    raw = run(["gh", "issue", "view", str(issue), "-R", REPO, "--json", "title,body,state"], cwd)
    if raw is None:
        return 1, branch, issue, notes + [f"Issue #{issue} not found on {REPO} (or gh is offline)."]
    data = json.loads(raw)
    notes.insert(0, f"Issue #{issue}: {data['title']}")
    acs = AC_ANY.findall(data["body"] or "")
    if not acs:
        return 2, branch, issue, notes + ["The issue has no `ACn [auto|play]` acceptance criteria yet."]
    play = sorted({int(n) for n, kind in acs if kind.lower() == "play"})

    ref = TESTS_REF.search(data["body"] or "")
    state = load_state()
    if ref and state.get(str(issue), {}).get("tests_from") != int(ref[1]):
        state.setdefault(str(issue), {})["tests_from"] = int(ref[1])
        save_state(state)

    tests = test_commits(cwd, base) if base else []
    approved = state.get(str(issue), {}).get("tests_approved")
    if not tests:
        if not tests_locked(cwd):
            if ref:
                notes.append(f"The issue reuses the tests of #{ref[1]}, but they aren't approved and on {BASE} yet.")
            return 3, branch, issue, notes
        if ref:
            notes.append(f"This task reuses the approved tests of #{ref[1]}.")
    elif approved != tests[0]:
        if approved:
            notes.append("Tests changed since the user approved them, so they need approving again.")
        return 4, branch, issue, notes + [f"Latest test commit: {tests[0][:8]}."]
    notes.append("Tests are approved and locked. Do not edit anything under src/test/.")

    raw = run(["gh", "pr", "list", "-R", REPO, "--head", branch, "--state", "all", "-L", "1",
               "--json", "number,state,body,headRefOid,url"], cwd)
    prs = json.loads(raw) if raw else []
    if not prs:
        return 5, branch, issue, notes
    pr = prs[0]
    notes.append(f"PR #{pr['number']}: {pr['url']}")
    if pr["state"] == "MERGED":
        return 11, branch, issue, notes
    if pr["state"] == "CLOSED":
        return 5, branch, issue, notes + ["The PR is closed without merging. Ask the user what happened."]

    raw = run(["gh", "pr", "checks", str(pr["number"]), "-R", REPO, "--json", "name,bucket"], cwd, ok_codes=(0, 1, 8))
    checks = json.loads(raw) if raw else []
    failing = [c["name"] for c in checks if c["bucket"] in ("fail", "cancel")]
    pending = [c["name"] for c in checks if c["bucket"] == "pending"]
    if failing:
        return 6, branch, issue, notes + [f"Failing checks: {', '.join(failing)}."]
    if pending:
        return 6, branch, issue, notes + [f"Checks still running: {', '.join(pending)}."]

    comments = run(["gh", "pr", "view", str(pr["number"]), "-R", REPO, "--json", "comments", "--jq", ".comments[].body"], cwd) or ""
    if f"claude-review:{pr['headRefOid'][:7]}" not in comments:
        notes.append("No AI review routine comment on the latest commit yet.")

    ticked = {int(n) for box, n, kind in AC_LINE.findall(pr["body"] or "") if kind == "play" and box.lower() == "x"}
    unticked = [n for n in play if n not in ticked]
    if unticked:
        return 8, branch, issue, notes + [f"[play] ACs not ticked in the PR: {', '.join(f'AC{n}' for n in unticked)}."]
    return 10, branch, issue, notes


def overview(cwd):
    """Every task in progress: worktrees on pipeline branches with their step, and open cleanup tracking issues."""
    lines = []
    path = None
    for line in (run(["git", "worktree", "list", "--porcelain"], cwd) or "").splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.startswith("branch refs/heads/") and BRANCH_ISSUE.match(line[len("branch refs/heads/"):]):
            result = status(path)
            if result:
                step, branch, issue, notes = result
                title = notes[0].split(": ", 1)[-1] if notes and notes[0].startswith("Issue #") else ""
                lines.append(f"- #{issue} {title}: step {step} {STEP_NAMES[step]} (worktree {path})")
    raw = run(["gh", "issue", "list", "-R", REPO, "--state", "open", "--search", "in:title Cleanup:",
               "--json", "number,title"], cwd)
    for issue in json.loads(raw) if raw else []:
        if issue["title"].startswith("Cleanup:"):
            lines.append(f"- #{issue['number']} {issue['title']} (tracking issue)")
    return lines


def report(result):
    step, branch, issue, notes = result
    lines = [f"Pipeline step {step}: {STEP_NAMES[step]} (branch `{branch}`)."] + notes
    if step in STEP_FILES:
        lines.append(f"Instructions: {SKILL}/steps/{STEP_FILES[step]}")
    if step == 8:
        lines.append(WAITING[9] + " Deploy only when the user asks.")
    elif step in WAITING:
        lines.append(WAITING[step])
    return "\n".join(lines)


def emit(event, context=None, deny=None):
    out = {"hookSpecificOutput": {"hookEventName": event}}
    if context:
        out["hookSpecificOutput"]["additionalContext"] = context
    if deny:
        out["hookSpecificOutput"]["permissionDecision"] = "deny"
        out["hookSpecificOutput"]["permissionDecisionReason"] = deny
    print(json.dumps(out))


def session_start(payload):
    result = status(payload.get("cwd") or os.getcwd())
    if result is None:
        return
    if result[0] == 0:
        tasks = overview(payload.get("cwd") or os.getcwd())
        open_work = ("\nPipeline work in progress:\n" + "\n".join(tasks)) if tasks else ""
        emit("SessionStart", f"{result[3][0]} For code work, load the pipeline skill ({SKILL}/SKILL.md) first."
             + open_work + "\nThis is context only. Act on it when the user asks.")
        return
    emit("SessionStart", "BetterPvP delivery pipeline. " + report(result) +
         "\nThis is context only. Act on it when the user asks, following the pipeline skill.")


def approve_tests(cwd):
    """Records the user's approval of the branch's latest test commit, which locks the tests."""
    _, issue = branch_issue(cwd)
    if issue is None:
        sys.exit("This branch has no issue number.")
    base = base_commit(cwd)
    tests = test_commits(cwd, base) if base else []
    if not tests:
        sys.exit("The branch has no `test:` commit to approve. Commit the tests with a `test:` message first.")
    state = load_state()
    state.setdefault(str(issue), {})["tests_approved"] = tests[0]
    save_state(state)
    print(f"Tests at {tests[0][:8]} approved for #{issue} and locked. Next: step 5, {SKILL}/steps/5-implement.md")


def unlock_tests(cwd):
    _, issue = branch_issue(cwd)
    if issue is None:
        sys.exit("This branch has no issue number.")
    state = load_state()
    state.get(str(issue), {}).pop("tests_approved", None)
    save_state(state)
    print(f"Tests for #{issue} unlocked. They need the user's approval again before implementation continues.")


WRITE_TOOLS = ("Edit", "MultiEdit", "Write", "NotebookEdit")
SHELL_TOOLS = ("Bash", "PowerShell")
SHELL_WRITES = re.compile(r"sed\s+-i|(?<![\d=-])>(?!&)|\btee\b|\brm\b|\bmv\b|\bcp\b|git\s+(checkout|restore|rm|mv)|"
                          r"Set-Content|Add-Content|Out-File|Remove-Item|Move-Item|Copy-Item|New-Item", re.I)


def guard(payload):
    tool = payload.get("tool_name", "")
    args = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    if tool in WRITE_TOOLS:
        path = str(args.get("file_path") or args.get("notebook_path") or "").replace("\\", "/")
        if path.endswith("/.claude/pipeline-state.json"):
            emit("PreToolUse", deny="Approvals are recorded only with pipeline.py approve-tests, after the user approves.")
        elif is_test_path(path) and tests_locked(cwd):
            emit("PreToolUse", deny="Tests are locked after the user approved them. If a test is wrong, stop and "
                                    "tell the user why. If they agree, record it with pipeline.py unlock-tests.")
    elif tool in SHELL_TOOLS:
        command = str(args.get("command") or "")
        if re.search(r"\bgh\s+pr\s+(merge|review\s+.*--approve)", command):
            emit("PreToolUse", deny="Approving and merging PRs is the user's step.")
        elif re.search(r"\bgh\s+issue\s+create\b", command):
            emit("PreToolUse", deny="File issues with `python .claude/pipeline/pipeline.py file-issue` so they land "
                                    "on the right board.")
        elif "pipeline-state.json" in command:
            emit("PreToolUse", deny="Approvals are recorded only with pipeline.py approve-tests, after the user approves.")
        elif mentions_tests(command) and SHELL_WRITES.search(command) and tests_locked(cwd):
            emit("PreToolUse", deny="Tests are locked after the user approved them. If a test is wrong, stop and "
                                    "tell the user why. If they agree, record it with pipeline.py unlock-tests.")


def file_issue(argv):
    """Creates an issue, puts it on the board as TODO, and takes it off the projects that auto-add new issues."""
    parser = argparse.ArgumentParser(prog="pipeline.py file-issue")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body-file", required=True)
    parser.add_argument("--label", action="append", default=[])
    args = parser.parse_args(argv)
    cwd = os.getcwd()
    board = CONFIG["board"]

    create = ["gh", "issue", "create", "-R", REPO, "--title", args.title, "--body-file", args.body_file]
    for label in args.label:
        create += ["--label", label]
    url = run(create, cwd)
    if not url:
        sys.exit("gh issue create failed.")
    url = url.splitlines()[-1]
    number = int(url.rstrip("/").rsplit("/", 1)[-1])

    item = run(["gh", "project", "item-add", str(board["number"]), "--owner", board["owner"], "--url", url,
                "--format", "json", "--jq", ".id"], cwd)
    if item:
        run(["gh", "project", "item-edit", "--project-id", board["id"], "--id", item,
             "--field-id", board["status_field"], "--single-select-option-id", board["status_todo"]], cwd)
    else:
        print(f"Could not add #{number} to project {board['number']}. Add it with the backlog skill.")

    owner, name = REPO.split("/")
    query = ("query($o:String!,$n:String!,$i:Int!){repository(owner:$o,name:$n){issue(number:$i){"
             "projectItems(first:20){nodes{id project{number}}}}}}")
    pending = set(CONFIG.get("remove_from_projects", []))
    for _ in range(10):
        raw = run(["gh", "api", "graphql", "-f", f"query={query}", "-f", f"o={owner}", "-f", f"n={name}",
                   "-F", f"i={number}", "--jq", ".data.repository.issue.projectItems.nodes"], cwd)
        for node in json.loads(raw) if raw else []:
            if node["project"]["number"] in pending:
                if run(["gh", "project", "item-delete", str(node["project"]["number"]), "--owner", board["owner"],
                        "--id", node["id"]], cwd) is None:
                    print(f"Could not remove #{number} from project {node['project']['number']}.")
                pending.discard(node["project"]["number"])
        if not pending:
            break
        time.sleep(2)
    print(f"#{number} {url}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    if mode == "status":
        result = status(os.getcwd())
        print("Not a git checkout." if result is None else report(result))
        return
    if mode == "file-issue":
        file_issue(sys.argv[2:])
        return
    if mode in ("approve-tests", "unlock-tests"):
        (approve_tests if mode == "approve-tests" else unlock_tests)(os.getcwd())
        return
    if mode == "overview":
        print("\n".join(overview(os.getcwd())) or "No pipeline work in progress.")
        return
    payload = json.load(sys.stdin)
    {"session-start": session_start, "guard": guard}[mode](payload)


if __name__ == "__main__":
    main()
