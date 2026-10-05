# Pipeline

Takes one GitHub issue to one merged PR, step by step. The steps are in
[skills/pipeline/SKILL.md](../../skills/pipeline/SKILL.md). The diagram is at
https://draw.brauw.dev/editor/1402245d-a973-49f7-b884-d83ee368f510.

## Setup

1. Run `install.py` (see the root README).
2. Add this under "How to work" in the checkout's `CLAUDE.md`:

   ```
   Code changes follow the delivery pipeline in the `pipeline` skill. A SessionStart hook reports which step the
   branch is on. Docs follow its `docs-standard.md`.
   ```

3. For deploys only: set `PTERODACTYL_API_KEY`, or sign in to the 1Password CLI with access to
   `op://Claude/pterodactyl-betterpvp/credential`.

Check it with `python .claude/pipeline/pipeline.py status` in the checkout.

On a new PC, also copy `.claude/pipeline-state.json` from the old checkout. It holds your test approvals.

## Config

`config.json` sets the repo, the base branch (`base`, change it when the season branch changes), the PR size limit,
the project board new issues go to, and the projects to take them off.
