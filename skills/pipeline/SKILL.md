---
name: pipeline
description: >
  The BetterPvP delivery pipeline every code change follows, from a GitHub issue to a small PR merged into the base
  branch. Also the cleanup loop for existing code and the docs standard. Use at the start of any code task, when asked
  which step a branch is on, when slicing a feature into issues, writing a spec or acceptance criteria, writing tests,
  opening or updating a PR, deploying for a playtest, running a cleanup of existing code, or writing docs.
---

# Delivery pipeline

These files live in the `BetterPvP/ai-tooling` repo, linked into `.claude/`. Commit changes there and keep the
diagram (https://draw.brauw.dev/editor/1402245d-a973-49f7-b884-d83ee368f510) in step.

## How a session runs

The user starts it with `/pipeline` and an idea, an issue number, or nothing. Nothing runs on its own.

1. Run `python .claude/pipeline/pipeline.py status` (or `overview` when not on a task branch). Say which step the
   work is on.
2. Read that step's file and do only that step.
3. Stop at the end of the step, even when the next one is yours.
4. End every reply with:

   ```
   Step <n> <name>: done | in progress | waiting on <who>
   Next: step <n> <name>, <who>. <what starts it>
   ```

5. Whenever the work waits on the user, ask with the AskUserQuestion tool, never with a question in the text. That
   covers approving tests, choosing between options, opening the PR, deploying, reporting playtest results and
   starting the next step. Give concrete options, with the recommended one first, and keep any question in the text
   out of the reply.

## Steps

| # | Step | Who | Done when |
|---|---|---|---|
| 1 | [Slice](steps/1-slice.md) | Claude proposes, user picks | each slice is an issue |
| 2 | [Spec](steps/2-spec.md) | user, Claude drafts | the issue has numbered ACs |
| 3 | [Tests first](steps/3-tests.md) | Claude | failing tests committed as `test:` |
| 4 | Approve tests | user | the user approved, and you ran `approve-tests` |
| 5 | [Implement](steps/5-implement.md) | Claude | tests pass, PR open |
| 6 | [Gates](steps/6-gates.md) | CI | checks green |
| 7 | AI review | review routine | advisory comment on the latest commit |
| 8 | [Deploy](steps/8-deploy.md) | Claude, when asked | ClansTest-1 runs the branch |
| 9 | Playtest | user | the user reported every `[play]` AC passing, and you ticked them in the PR |
| 10 | Review | user | user reviewed and is ready to merge |
| 11 | [Merged](steps/11-merged.md) | user merges, Claude cleans up | card Done, worktree gone |

On steps 4, 9 and 10, say what is waiting on the user and ask with AskUserQuestion.

## Rules

- One task is one issue, one branch `<issue>-<slug>` from `origin/<base>` in its own worktree, and one PR into
  `<base>`. A second PR needs a second issue. `<base>` is in `.claude/pipeline/config.json`.
- At most 400 changed non-test lines per PR. Past that, propose a split.
- `test:` commits come before implementation commits.
- Approved tests are locked. If one is wrong, stop and explain. Never weaken a test.
- Never approve or merge a PR. Record a test approval only after the user gives it (see Approvals).
- Docs and translations go in the same PR as the code.
- Deploy only when asked. Playtesting is the user's.

## Approvals

Nothing is approved until the user says so. Ask with AskUserQuestion, for example "Approve these tests?" with the
options Approve, Change something, Not yet. If they answer in their own words instead, read it the way a colleague
would: "looks good, go ahead" approves, "fine but rename X" does not yet. When unsure, ask again.

When they approve the tests, run `python .claude/pipeline/pipeline.py approve-tests`. That locks the tests. If a
locked test turns out to be wrong, explain why and ask. Only when they agree, run
`python .claude/pipeline/pipeline.py unlock-tests`. Never run either on your own judgement.

## Acceptance criteria

```
## Acceptance criteria
- [ ] AC1 [auto] A builder with no wood stops working.
- [ ] AC2 [play] The builder shows the "needs wood" tag.
```

`[auto]`: a unit test can check it. `[play]`: only a person in game can. One sentence of observable behaviour each.

## Pausing and resuming

When the user stops, save what is unsaved, then end with `Resume: /pipeline #<issue>`.

| What | Saved in |
|---|---|
| Draft spec | the issue body, marked `Status: Draft` |
| Code in progress | pushed commits on the task branch (`wip:` is fine) |
| Test approvals | `.claude/pipeline-state.json`, written by `approve-tests` |
| Cleanup findings | the tracking issue |
| Open questions | a comment on the issue |

## Other flows

- [cleanup.md](cleanup.md): bringing existing code up to standard
- [slop-checklist.md](slop-checklist.md): what to flag in reviews and cleanups
- [docs-standard.md](docs-standard.md): where docs live and how they are written
