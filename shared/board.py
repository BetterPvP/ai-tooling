"""Issues and the Network Expansion board, for the skills. Repo and board ids are in project.json next to this file.

    python .claude/shared/board.py file-issue --title T --body-file F [--label L ...]
    python .claude/shared/board.py status <number> todo|in_progress|in_review|done
    python .claude/shared/board.py tidy <number>
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

CONFIG = json.loads((pathlib.Path(__file__).resolve().parent / "project.json").read_text(encoding="utf-8"))
REPO = CONFIG["repo"]
BOARD = CONFIG["board"]
ITEMS_QUERY = ("query($o:String!,$n:String!,$i:Int!){repository(owner:$o,name:$n){issueOrPullRequest(number:$i){"
               "...on Issue{url projectItems(first:20){nodes{id project{number}}}}"
               "...on PullRequest{url projectItems(first:20){nodes{id project{number}}}}}}}")


def gh(*args):
    result = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip() if result.returncode == 0 else None


def item(number):
    """The issue or PR's url and its project items, as {project number: item id}."""
    owner, name = REPO.split("/")
    raw = gh("api", "graphql", "-f", f"query={ITEMS_QUERY}", "-f", f"o={owner}", "-f", f"n={name}", "-F", f"i={number}",
             "--jq", ".data.repository.issueOrPullRequest")
    data = json.loads(raw) if raw else {}
    return data.get("url"), {n["project"]["number"]: n["id"] for n in data.get("projectItems", {}).get("nodes", [])}


def set_status(number, status):
    url, items = item(number)
    item_id = items.get(BOARD["number"]) or gh("project", "item-add", str(BOARD["number"]), "--owner", BOARD["owner"],
                                                "--url", url, "--format", "json", "--jq", ".id")
    gh("project", "item-edit", "--project-id", BOARD["id"], "--id", item_id, "--field-id", BOARD["status_field"],
       "--single-select-option-id", BOARD["status"][status])
    print(f"#{number} -> {status}")


def tidy(number):
    """Takes an issue or PR off the projects that auto-add new items. They add it some seconds later, so this waits up
    to a minute for them."""
    pending = set(CONFIG.get("remove_from_projects", []))
    for _ in range(20):
        _, items = item(number)
        for project in [p for p in items if p in pending]:
            gh("project", "item-delete", str(project), "--owner", BOARD["owner"], "--id", items[project])
            pending.discard(project)
        if not pending:
            return
        time.sleep(3)


def file_issue(argv):
    parser = argparse.ArgumentParser(prog="board.py file-issue")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body-file", required=True)
    parser.add_argument("--label", action="append", default=[])
    args = parser.parse_args(argv)
    create = ["issue", "create", "-R", REPO, "--title", args.title, "--body-file", args.body_file]
    for label in args.label:
        create += ["--label", label]
    url = gh(*create)
    if not url:
        sys.exit("gh issue create failed.")
    number = int(url.splitlines()[-1].rstrip("/").rsplit("/", 1)[-1])
    set_status(number, "todo")
    tidy(number)
    print(f"#{number} {url}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "file-issue":
        file_issue(sys.argv[2:])
    elif mode == "status":
        set_status(int(sys.argv[2]), sys.argv[3])
    elif mode == "tidy":
        tidy(int(sys.argv[2]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
