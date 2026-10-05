---
name: pipeline
description: >
  The BetterPvP delivery pipeline every code change follows, from a GitHub issue to a small PR merged into the base branch.
  Also the cleanup loop for existing code and the docs standard. Use at the start of any code task, when asked which step a
  branch is on, when slicing a feature into issues, writing a spec or acceptance criteria, writing tests, opening or
  updating a PR, deploying for a playtest, running a cleanup of existing code, or writing or reorganising docs.
---

# Delivery pipeline

The diagram for people is at https://draw.brauw.dev/editor/1402245d-a973-49f7-b884-d83ee368f510. This file and the
files it links are the source of truth. When they change, update the diagram too.
They live in the `BetterPvP/claude-pipeline` repo, linked into `.claude/`. Commit changes there.

Where a branch stands: `python .claude/pipeline/pipeline.py status`. A SessionStart hook prints the same report, so
you usually already have it in context. Read the step file it names before acting.

## How a session runs

The user drives. Nothing here runs on its own. The user starts with `/pipeline` plus an idea, a PRD, an issue number,
or nothing (continue the current branch).

1. Run the status script. Tell the user in one or two lines which step the work is on and what that step produces.
2. Do that one step, working with the user where it needs their decisions.
3. Stop at the end of the step. Never carry on into the next step in the same turn, even when it is yours.
4. End every reply with a short block:

   ```
   Step <n> <name>: done (or: in progress, waiting on ...)
   Next: step <n> <name>, <who>. <what the user says or does to start it>
   ```

   For example: `Next: step 4 Approve tests, you. Read the tests above, then reply "approve tests".`

## Pausing and resuming

Sessions are disposable. Everything a later session needs lives outside the chat:

| What | Where it is saved |
|---|---|
| Spec and ACs, even half done | the issue body, with `Status: Draft` at the top until the user is happy |
| Code in progress | commits on the task branch, pushed. A `wip:` commit is fine, the PR is squashed |
| Test approval | `.claude/pipeline-state.json`, written by the user's `approve tests` |
| Findings and decisions for a cleanup | the subsystem's tracking issue |
| Open questions for the user | a comment on the issue |

When the user says they are stopping, save whatever is not saved yet to those places, then end with
`Resume: /pipeline #<issue>` or `Resume: /pipeline`.

To resume, the user runs `/pipeline`:
- with an issue number: `cd` into that task's worktree and run `status` there.
- without one, from the main checkout: run `python .claude/pipeline/pipeline.py overview`, show the tasks in
  progress with their steps, and ask which to continue.

## Rules that always apply

- One task is one GitHub issue on `mykindos/BetterPvP`, one branch `<issue>-<slug>` cut from `origin/<base>` in its
  own worktree, and exactly one PR into `<base>`. `<base>` and the board are set in `.claude/pipeline/config.json`. Work that needs a second PR is a second issue.
- A PR changes at most 400 non-test lines. If it grows past that, stop and propose a split.
- Commits starting with `test:` come before the implementation commits.
- Once the user approves the tests, they are locked. A hook blocks edits under `src/test/`. If a test is wrong, stop
  and explain why. Never weaken a test to make it pass.
- You never approve, merge, or record approvals. The user replies `approve tests` or `unlock tests`, and merges.
- Docs and translations go in the same PR as the code.
- Playtesting is the user's. Deploy only when they ask.

## Steps

| # | Step | Who | Done when |
|---|---|---|---|
| 1 | Slice | Claude proposes, user picks | the slice is an issue with a size estimate. [steps/1-slice.md](steps/1-slice.md) |
| 2 | Spec | user, Claude drafts | the issue lists numbered ACs, each `[auto]` or `[play]`. [steps/2-spec.md](steps/2-spec.md) |
| 3 | Tests first | Claude | failing tests for every `[auto]` AC are committed as `test:`. [steps/3-tests.md](steps/3-tests.md) |
| 4 | Approve tests | user | the user replied `approve tests` |
| 5 | Implement | Claude | tests pass, docs and translations done, PR open. [steps/5-implement.md](steps/5-implement.md) |
| 6 | Gates | CI | every check is green. [steps/6-gates.md](steps/6-gates.md) |
| 7 | AI review | review routine | a comment ending `claude-review:<sha>` is on the latest commit. Advisory |
| 8 | Deploy | Claude, when asked | ClansTest-1 runs the branch. [steps/8-deploy.md](steps/8-deploy.md) |
| 9 | Playtest | user | every `[play]` AC is ticked in the PR body |
| 10 | Review | user | the user reviewed spec, tests, public API, then implementation |
| 11 | Merged | user merges, Claude cleans up | [steps/11-merged.md](steps/11-merged.md) |

Steps 4, 9 and 10 belong to the user. When the status says one of them, tell the user what is waiting and stop.

## Acceptance criteria format

In the issue body and the PR body:

```
## Acceptance criteria
- [ ] AC1 [auto] A builder with no wood in the camp store stops working.
- [ ] AC2 [play] The builder shows the "needs wood" tag above its head.
```

`[auto]` means a unit test can check it. `[play]` means only a person in game can. One sentence each, observable
behaviour, no implementation detail.

## Other flows

- Bringing existing code up to standard: [cleanup.md](cleanup.md)
- What slop looks like, for reviews and cleanup passes: [slop-checklist.md](slop-checklist.md)
- Where docs live and how they are written: [docs-standard.md](docs-standard.md)
