# Review

A Claude Code cloud routine that reviews a PR and posts one comment ending in `claude-review:<sha>`. It runs on your
subscription in a fresh session, and never approves or pushes.

- `prompt.md` is the routine's prompt. After changing it, update the routine on claude.ai to match.
- `install.py` adds `git-hooks/pre-push`, which requests a review a minute after every push to a branch with an open
  PR.
- `python .claude/review/fire.py <pr>` requests one by hand.

## Setup

1. On claude.ai, open the "BetterPvP PR review" routine and create an API trigger token.
2. Save it in 1Password at `op://Claude/pr-review-routine/credential`, or set `CLAUDE_REVIEW_TOKEN`.

Without a token, pushes still work and the hook says it skipped the review.
