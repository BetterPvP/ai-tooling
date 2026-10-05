---
name: cleanup
description: >
  Guides bringing existing code up to standard, one subsystem at a time: inventory, triage, specs, pin tests, slop
  findings and refactor issues. Use when the user runs /cleanup, or asks to clean up, de-slop, audit or certify
  existing code, a module or everything a branch adds.
---

# /cleanup <scope>

The scope is a feature, a module, a package, or what one branch adds over another. Every decision goes to the user on
an AskUserQuestion card. Repo, base branch and board are in `.claude/shared/project.json`.

The work is tracked on GitHub, so a cleanup resumes any day: find the open `Cleanup: <scope>` index issue and continue
from its checklist.

## Once per cleanup

1. Inventory the scope, grouped by package into subsystems: files, lines, test count, last change. For a branch scope
   use `git diff --stat origin/<from>...origin/<to>`.
2. Triage with cards, a few subsystems per card: Keep · Rework · Delete. Ask the order too. The default is foundations
   first: shared frameworks, then the features built on them, then player-facing text.
3. File the index issue `Cleanup: <scope>` with one checklist line per subsystem and its decision, and a tracking issue
   `Cleanup: <scope> / <subsystem>` for each Keep or Rework, using `python .claude/shared/board.py file-issue`.
4. File one removal issue per Delete subsystem. Those come first, through `/build`.

## Per subsystem

1. **Spec.** Draft what the subsystem should do from its PRD in Outline, not from the code. Where code and PRD
   disagree, or there is no PRD, ask. File it as a `Pin: <subsystem>` issue whose ACs are that behaviour.
2. **Pin.** The pin issue goes through `/build`. Its tests may pass straight away.
3. **Findings.** After the pin PR merges, run the `slop-reviewer` agent on the subsystem's files, and read its Sonar
   issues. Post one findings list on the tracking issue, each with `file:line`.
4. **Choose.** Ask with a card (multi-select) which findings to fix and how to group them.
5. **Refactor issues.** File one issue per group, at most 400 lines each, with `Tests: #<pin issue>` in the body, plus
   one issue to rewrite the subsystem's system doc with `/doc system`. Each goes through `/build`.
6. **Certify.** When they are merged, check the exit criteria: every AC has a passing test or a playtest tick, CI is
   green with no open Sonar issues in the subsystem, no code without a caller, every public type justified in one
   line, the system doc matches the code. If met, tick the subsystem in the index issue. If not, back to step 3.

When every Keep and Rework subsystem is ticked, close the index issue.
