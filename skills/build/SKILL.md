---
name: build
description: >
  Implements one issue: tests first, the user's approval, implementation here or by a background agent, an automatic
  slop review, then docs and PR. Use when the user runs /build, says to build or implement an issue, or picks "Now"
  at the end of /slice. Resumes an issue that is already in progress.
---

# /build #<issue>

Optional tooling: the user may also build by hand. Every decision goes to the user on an AskUserQuestion card. Read
`.claude/shared/house-rules.md` before writing code. Repo, base branch and board are in `.claude/shared/project.json`.

## 1. Pick up the issue

- Read the issue. If it has no acceptance criteria, draft them in the `/slice` format, tag each `[auto]` or `[play]`,
  and ask with a card: Use these · Change. Write them to the issue only after the user accepts.
- Find the work: a branch named `<issue>-*` and its worktree under `.claude/worktrees/`. If they exist, this is a
  resume. Read the commits and the PR, say where the work stands, and continue from there.
- Otherwise create them from `origin/<base>`:
  `git worktree add .claude/worktrees/<issue>-<slug> -b <issue>-<slug> origin/<base>`.
  Move the card to In progress: `python .claude/shared/board.py status <issue> in_progress`.

## 2. Tests first

- Write at least one test per `[auto]` AC in the module the code will live in, named after it
  (`ac3_builderStopsWithoutWood`). Add only the production signatures needed to compile.
- Run them. They must compile and fail for the right reason.
- Commit only tests and signatures: `test: AC1-AC4 for #<issue>`.
- Show which test covers which AC and ask with a card: Approve · Change · Let me read first.

## 3. Implement

Ask with a card: Stay here · Finish in the background.

- **Stay:** implement here. Never change an approved test without explaining why and getting a yes. If one must
  change, put it in its own `test:` commit.
- **Background:** start the `implementer` agent in the background with the issue number, the worktree path and the
  base branch. Tell the user they can keep working. When it reports, check its summary and continue at step 4. If it
  stopped on a wrong test, bring that to the user.

Either way the result is: tests pass (`./gradlew :<module>:test`), the changed modules compile, player-facing text is
translated in all 12 locales.

## 4. Slop review

Always run the `slop-reviewer` agent on the branch against `origin/<base>`. Show its findings and ask with a card
(multi-select) which to fix. Fix the chosen ones, rerun the tests, commit.

## 5. Docs

Ask with a card: Update docs · No docs needed. On update, use the `doc` skill. A system doc lives in ai-tooling
`docs/`, so commit it there with a message naming the issue.

## 6. PR

Ask with a card: Open the PR · Not yet.

- Push the branch. Open the PR against `<base>` filling the repo's PR template: `Closes #<issue>`, what changes, and
  the AC table naming the test for each `[auto]` AC and "playtest" for each `[play]` AC.
- Run `python .claude/shared/board.py tidy <pr>` and `python .claude/shared/board.py status <issue> in_review`.
- If there are `[play]` ACs, ask with a card: Deploy to ClansTest-1 now · Later. To deploy, run `./gradlew shadowJar`
  in the worktree, then `python .claude/shared/deploy.py`, with `--pack` when screen files or pack art changed. Never
  playtest yourself. When the user reports results,
  tick the passing `[play]` ACs in the PR body with
  `gh api -X PATCH repos/<repo>/pulls/<pr> -F body=@<file>`.

## After the merge

When the user says it merged: close the issue (merges into a non-default base do not close it), set the card to Done,
then remove the worktree and branch (`git worktree remove`, `git branch -D`, after removing any `private/` junction).
