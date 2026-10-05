# Cleanup

Brings code that already exists up to the pipeline's standard, one subsystem at a time. A cleanup has a scope the
user names: a feature, a module, a package, or everything a branch adds over another (for example the base branch
over `master`). New features in that scope only land through the normal pipeline while the cleanup runs.

`<base>` below is the base branch in `.claude/pipeline/config.json`.

## Once per cleanup

1. Inventory. List the code in scope, grouped by package into subsystems, with files, lines, test count and last
   change for each. For a branch scope use `git diff --stat origin/<from>...origin/<base>`. Put the table in an index
   issue titled `Cleanup: <scope>`, one checklist line per subsystem.
2. Triage each subsystem with the user as Keep, Rework or Delete, written into the index issue. Each Keep or Rework
   subsystem gets a tracking issue `Cleanup: <scope> / <subsystem>`, linked from its checklist line.
3. Delete first, one task issue and one removal PR per deleted subsystem. That shrinks what is left to review.

Ask the user for the order. The default is foundations first: shared core frameworks, then the features built on
them, then player-facing text.

The index issue is where the cleanup stands overall. Tick a subsystem's line when it is certified.

## Per subsystem

The tracking issue holds the findings list and links its tasks. It never gets a branch. Every PR is its own task
issue, one PR each:

1. Pin task (`Pin: <subsystem>`). Spec: the ACs say what the subsystem should do, taken from its PRD in Outline, not
   read off the code. Where the code and the PRD disagree, or there is no PRD, ask the user. Tests: pin tests for
   that behaviour. They may pass straight away. The PR adds only tests, plus fixes where the code breaks an AC.
2. Findings. After the pin PR merges, collect the CI findings and a pass with [slop-checklist.md](slop-checklist.md)
   into one list on the tracking issue, each with `file:line`. The user ticks which to fix and how to group them.
3. Refactor tasks, one issue per group, each at most 400 lines. The issue body has the line `Tests: #<pin issue>`.
   The pinned tests are already approved and on `<base>`, so these start at step 5 and must keep them green.
4. Doc task: the subsystem's system doc rewritten to [docs-standard.md](docs-standard.md). Then close the tracking
   issue.

## Certified when

- every AC has a passing test or a playtest tick
- CI is green with no duplication or convention findings left in the subsystem
- no code without a caller, and no public type that cannot be justified in one line
- its system doc matches the code

When every Keep and Rework subsystem is certified, close the index issue.
