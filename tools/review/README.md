# Review

The "BetterPvP PR review" routine on claude.ai. It reviews a PR in a fresh cloud session on your subscription and
posts one comment ending in `claude-review:<sha>`. It never approves or pushes.

The repo's `.github/workflows/ai-review.yml` fires it through the routine's API trigger whenever a non-draft PR into
`camps` with the `pipeline` label opens, gets commits, is reopened, leaves draft, or gets the label. The trigger
token is the repo secret `CLAUDE_REVIEW_TOKEN`.

`prompt.md` is the routine's prompt. After changing it, update the routine on claude.ai to match.
