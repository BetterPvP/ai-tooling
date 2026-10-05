# Review

The "BetterPvP PR review" routine on claude.ai. It reviews a PR in a fresh cloud session on your subscription and
posts one comment ending in `claude-review:<sha>`. It never approves or pushes.

It runs on GitHub pull request events (opened, synchronize, reopened, labeled) for PRs into `camps` with the
`pipeline` label, not drafts. Adding the label to any PR requests a review.

`prompt.md` is the routine's prompt. After changing it, update the routine on claude.ai to match.
