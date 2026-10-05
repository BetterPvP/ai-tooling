"""Asks the PR review routine to review a pull request. Never blocks or fails a push.

    python .claude/review/fire.py <pr number>       review that PR now
    python .claude/review/fire.py --push            git pre-push hook: review the open PRs of the pushed branches

The routine and the place its token is kept are set in config.json next to this file.
"""
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))


def token():
    if os.environ.get("CLAUDE_REVIEW_TOKEN"):
        return os.environ["CLAUDE_REVIEW_TOKEN"]
    result = subprocess.run(["op", "read", CONFIG["token_ref"]], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def fire(pr):
    secret = token()
    if not secret:
        print(f"PR review: no routine token, skipped. Set CLAUDE_REVIEW_TOKEN or {CONFIG['token_ref']}.")
        return
    url = f"https://api.anthropic.com/v1/claude_code/routines/{CONFIG['routine']}/fire"
    request = urllib.request.Request(url, method="POST", data=json.dumps({"text": json.dumps({"pr": pr})}).encode(),
                                     headers={"Authorization": f"Bearer {secret}",
                                              "anthropic-beta": "experimental-cc-routine-2026-04-01",
                                              "anthropic-version": "2023-06-01",
                                              "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        response.read()
    print(f"PR review: requested for #{pr}.")


def open_prs(branch):
    result = subprocess.run(["gh", "pr", "list", "-R", CONFIG["repo"], "--head", branch, "--state", "open",
                             "--json", "number", "--jq", ".[].number"], capture_output=True, text=True)
    return [int(n) for n in result.stdout.split()] if result.returncode == 0 else []


def on_push():
    """Fires a minute after the push, from a detached process, so the review sees the pushed commits."""
    for line in sys.stdin.read().splitlines():
        local_ref, local_sha, _, _ = (line.split() + ["", "", "", ""])[:4]
        if not local_ref.startswith("refs/heads/") or set(local_sha) == {"0"}:
            continue
        for pr in open_prs(local_ref[len("refs/heads/"):]):
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            subprocess.Popen([sys.executable, __file__, str(pr), "--delay", "60"], creationflags=flags,
                             start_new_session=os.name != "nt", stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"PR review: will be requested for #{pr} in a minute.")


def main():
    try:
        if "--push" in sys.argv:
            on_push()
            return
        if "--delay" in sys.argv:
            time.sleep(int(sys.argv[sys.argv.index("--delay") + 1]))
        fire(int(sys.argv[1]))
    except Exception as e:
        print(f"PR review: not requested ({e}).")


if __name__ == "__main__":
    main()
