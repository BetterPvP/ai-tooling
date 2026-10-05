---
name: slice
description: >
  Plans a feature or fix into small issues with acceptance criteria. Use when the user runs /slice, or asks to plan,
  slice, scope or spec a feature, turn a PRD into issues, or write acceptance criteria for an issue.
---

# /slice

Turns an idea, a PRD or an issue into one or more GitHub issues, each one slice of at most 400 changed non-test lines
that works end to end. Optional tooling: the user may also do all of this by hand.

Repo, base branch and board are in `.claude/shared/project.json`. Board commands are in `.claude/shared/board.py`.

## Steps

1. **Read.** The PRD in Outline if one is linked or exists, `CONTEXT.md` for the domain words, and only the code needed
   to know what already exists. If the feature is big and has no PRD, offer to draft one first with `/doc prd`.
2. **Grill.** Ask the questions whose answers change the spec, with AskUserQuestion, up to four per card: edge cases,
   restart and logout, two players at once, empty or full state, chunk unload, permissions, what staff need. Skip this
   step if the user says the idea is clear. Every answer becomes an acceptance criterion or an out-of-scope line.
3. **Propose.** List the slices in the chat: title, one-line goal, rough size, order. Each is playable or observable on
   its own and depends only on slices before it. Ask with a card: Accept · Change. Nothing is written yet.
4. **File.** For each accepted slice, write the body and run
   `python .claude/shared/board.py file-issue --title "<title>" --body-file <file>`. It files the issue, puts it on
   the board as TODO and takes it off boards that auto-add issues.

   ```
   ## Goal
   One or two sentences on what the player or staff member gets.

   ## Acceptance criteria
   - [ ] AC1 [auto] A builder with no wood stops working.
   - [ ] AC2 [play] The builder shows the "needs wood" tag.

   ## Out of scope
   - ...
   ```

   Each AC is one sentence of observable behaviour. Tag it `[auto]` when a unit test can check it, `[play]` when only
   a person in game can. Prefer `[auto]`: game logic kept outside Bukkit listeners can usually be tested.
5. **Hand off.** Ask with a card: "Build #<first issue> now?" Now · Later. On Now, continue with the `build` skill for
   that issue. On Later, tell the user they can run `/build #<issue>` any day.

## For an existing issue

`/slice #<n>` reads the issue, grills only what is missing, and rewrites its body with the user's approval instead of
filing a new one.
