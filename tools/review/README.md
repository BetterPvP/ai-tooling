# Review

The "BetterPvP PR review" routine on claude.ai. It reviews a PR in a fresh cloud session on your subscription and
posts one comment ending in `claude-review:<sha>`. It never approves or pushes.

The repo's `.github/workflows/ai-review.yml` fires it through the routine's API trigger whenever a non-draft PR into
`camps` gets the `pipeline` label, gets commits, is reopened, or leaves draft. Events wait a minute so a burst gives
one review. The trigger token is the repo secret `CLAUDE_REVIEW_TOKEN`.

`prompt.md` is the routine's prompt. After changing it, update the routine on claude.ai to match.
