# BetterPvP Claude pipeline

A Claude Code kit that runs BetterPvP work through a fixed delivery pipeline: one GitHub issue, one small branch,
one PR into the base branch. Claude guides each step and stops at every hand-off. You approve the tests, playtest
and merge.

Diagram: https://draw.brauw.dev/editor/1402245d-a973-49f7-b884-d83ee368f510

## What is in here

| Path | Installed as | What it does |
|---|---|---|
| `skill/` | `.claude/skills/pipeline` | The `/pipeline` skill: the steps, the cleanup loop, the slop checklist and the docs standard |
| `scripts/pipeline.py` | `.claude/pipeline/pipeline.py` | Works out which step a branch is on, lists work in progress, files issues, backs the hooks |
| `scripts/deploy.py` | `.claude/pipeline/deploy.py` | Uploads the built jars to ClansTest-1 and restarts it |
| `scripts/config.json` | `.claude/pipeline/config.json` | Base branch, repo and project board |
| `hooks.json` | merged into `.claude/settings.json` | The hooks and permissions below |
| `install.py` | | Sets all of this up in a checkout |

The hooks:

- SessionStart: tells each new session which step the branch is on, or lists the work in progress.
- UserPromptSubmit: a message starting with `approve tests` approves and locks the branch's tests. `unlock tests`
  reverses it. Only your own message can do this.
- PreToolUse: blocks edits to locked tests, `gh pr merge`, approving PRs, `gh issue create` (issues go through
  `pipeline.py file-issue`) and writes to the approvals file.

Every hook lets the command through if the script is missing, so a broken install never blocks Claude.

## Requirements

- Claude Code, with the BetterPvP repo cloned
- Python 3.12 or newer on `PATH` as `python`
- GitHub CLI `gh`, logged in as an account with write access to `mykindos/BetterPvP` and to the Network Expansion
  project. Check with `gh auth status`
- For step 8 (deploy) only: a Pterodactyl client API key that can manage ClansTest-1, either in the environment as
  `PTERODACTYL_API_KEY` or in 1Password at `op://Claude/pterodactyl-betterpvp/credential` with the `op` CLI signed in

## Install

Clone this repo next to the BetterPvP checkout, then run the installer against the checkout:

```bash
git clone https://github.com/BetterPvP/claude-pipeline.git
python claude-pipeline/install.py <path to BetterPvP>
```

It is safe to run again, for example after pulling changes to `hooks.json`. It does four things:

1. Links `.claude/skills/pipeline` and `.claude/pipeline` in the checkout to this clone. Junctions on Windows,
   symlinks elsewhere. Edits made through either path land in this repo.
2. Merges the hooks and permissions from `hooks.json` into the checkout's `.claude/settings.json`, keeping any other
   hooks there.
3. Adds the links and the approvals file to the checkout's `.git/info/exclude`, so none of it shows up in the
   public repo.
4. Leaves your `CLAUDE.md` alone. Add the lines below yourself.

### CLAUDE.md

Add this under "How to work" in the checkout's `CLAUDE.md`:

```
Code changes follow the delivery pipeline in the `pipeline` skill (`.claude/skills/pipeline/`). A SessionStart hook
reports which step the branch is on. Docs follow its `docs-standard.md`.
```

### Check it works

Open a new Claude Code session in the checkout. The first context should mention the pipeline. Then:

```bash
python .claude/pipeline/pipeline.py status
```

On the base branch it reports step 0. On a branch named `<issue>-<slug>` it reports the issue's step.

## Moving to a new PC

1. Clone BetterPvP and this repo side by side.
2. Install the requirements above and log in to `gh`.
3. Run `install.py` against the checkout and add the `CLAUDE.md` lines.
4. Copy `.claude/pipeline-state.json` from the old checkout if you have tests approved on branches that are still
   open. Without it, those branches ask for `approve tests` again.

Branches, issues, PRs and the board are on GitHub, so nothing else needs moving.

## Configuration

`scripts/config.json`:

| Key | Meaning |
|---|---|
| `repo` | GitHub repo the issues and PRs live in |
| `base` | Branch every task branches from and merges into. Change it when the season branch changes |
| `diff_limit` | Most non-test lines a PR may change before Claude proposes a split |
| `board` | The Network Expansion project and the ids of its Status field and TODO option |
| `remove_from_projects` | Project numbers that auto-add new issues and should not keep them (the Clans board) |

If the board's field ids change, refresh them with `gh project field-list 2 --owner Mykindos --format json`.

## Using it

| You type | What happens |
|---|---|
| `/pipeline <idea or PRD>` | Claude slices it into issues for you to pick from |
| `/pipeline #<issue>` | Continue that task in its worktree, at whatever step it is on |
| `/pipeline` | List every task in progress and pick one |
| `approve tests` | Lock the current tests and move to implementation |
| `unlock tests` | Let tests change again. They need approving again after |
| "stopping here" | Claude saves the work to the issue and branch and tells you how to resume |
| `/pipeline Start a cleanup of <scope>` | Run the cleanup loop on existing code |

Every Claude reply in a pipeline session ends with the current step and what comes next.

## Not built yet

- The CI checks (ArchUnit conventions, translation keys, CPD, PIT, Sonar, test-lock check). Until they exist,
  step 6 only has the unit tests.
- The AI review routine for step 7. The plan is a Claude Code cloud routine fired by a pre-push hook, posting one
  comment per commit that ends in `claude-review:<sha>`.
- A ruleset on the base branch that makes the checks required. Only the repo owner can add it.

## Uninstall

Delete the two links in the checkout's `.claude/`, remove the three pipeline hook entries and the two permissions
from `.claude/settings.json`, and remove the `# claude-pipeline` lines from `.git/info/exclude`.
