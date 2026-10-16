---
name: cleanup
description: >
  Guides bringing existing code up to standard, one subsystem at a time: inventory, triage, specs, pin tests, slop
  findings and refactor issues. Use when the user runs /cleanup, or asks to clean up, de-slop, audit or certify
  existing code, a module or everything a branch adds.
---

# /cleanup <scope>

The scope is a feature, a module, a package, or what one branch adds over another. Every decision goes to the user on
an AskUserQuestion card. Repo and base branch are in `.claude/shared/project.json`.

The work is tracked in the Itsaplan CLANS project, so a cleanup resumes any day: find the `Cleanup: <scope>` index
issue with `search_issues` and continue from its checklist.

## Filing issues

File every issue with the Itsaplan MCP tools. Read the column, type and initiative ids from `get_project` and
`list_initiatives`.

- `create_issue` in the Backlog column, with no cycle. The Planner and the user schedule it.
- Type Slice when a person must check something in game, Chore when nothing player-visible changes, Bug for a defect
  the findings turn up.
- Set the initiative the subsystem belongs to. Ask when it is unclear.
- Description: a `## Goal` paragraph of one or two sentences, then `## Out of scope`.
- Add a checklist named `Acceptance criteria` with `create_checklist` and fill it with `create_checklist_item`. Each
  item is one sentence of observable behaviour, starting with `[auto]` when a unit test can check it or `[play]` when
  only a person in game can.
- Order the work with `link_issues` (`blocks`) from each issue to the ones that need it.

Leave every issue in Backlog. The user moves it to Todo and works it through the issue's Agent prompt. Never move an
issue between columns.

## Once per cleanup

1. Inventory the scope, grouped by package into subsystems: files, lines, test count, last change. For a branch scope
   use `git diff --stat origin/<from>...origin/<to>`.
2. Triage with cards, a few subsystems per card: Keep · Rework · Delete. Ask the order too. The default is foundations
   first: shared frameworks, then the features built on them, then player-facing text.
3. File the index issue `Cleanup: <scope>` as a Chore with a `Subsystems` checklist, one item per subsystem and its
   decision. File a tracking issue `Cleanup: <scope> / <subsystem>` as a Chore for each Keep or Rework, with the
   certify criteria below as its `Acceptance criteria`.
4. File one removal issue per Delete subsystem, with criteria that nothing still calls the removed code and the suite
   builds. Each blocks the first tracking issue, so removals come first.

## Per subsystem

1. **Spec.** Draft what the subsystem should do from its initiative's linked docs in Itsaplan
   (`list_initiative_documents`, then `get_document`), not from the code. Search the rest with `list_documents` when
   the initiative has none. Where code and docs disagree, or there is no doc, ask. File it as a `Pin: <subsystem>` issue
   whose `Acceptance criteria` are that behaviour. Link it to the tracking issue with `relates`.
2. **Pin.** The user works the pin issue through its Agent prompt. Its tests may pass straight away.
3. **Findings.** After the pin PR merges, run the `slop-reviewer` agent on the subsystem's files, and read its Sonar
   issues. Post one findings list as a comment on the tracking issue, each with `file:line`.
4. **Choose.** Ask with a card (multi-select) which findings to fix and how to group them.
5. **Refactor issues.** File one issue per group, at most 400 changed lines each, and one Chore to rewrite the
   subsystem's system doc in ai-tooling `docs/` to match the code. The pin issue blocks each of them, and they all link
   to the tracking issue with `relates`. Stop there and tell the user which issues wait in Backlog.
6. **Certify.** When they are merged, check the exit criteria: every pin criterion has a passing test or a ticked
   `[play]` item, CI is green with no open Sonar issues in the subsystem, no code without a caller, every public type
   justified in one line, the system doc matches the code. If met, tick the tracking issue's criteria and the
   subsystem in the index issue. If not, back to step 3.

When every Keep and Rework subsystem is ticked, tell the user the index issue is ready to close.
