# Step 5: Implement

Make the approved tests pass. They are locked: a hook blocks edits under `src/test/`. If a test is wrong or
impossible, stop and tell the user why. They can reply `unlock tests`.

1. Write the smallest code that passes the tests and meets the `[play]` ACs. Follow `CLAUDE.md` and the module's
   `CLAUDE.md`. Check your diff against [../slop-checklist.md](../slop-checklist.md) before committing.
2. Run the module's tests: `./gradlew :<module>:test`.
3. Player-facing text goes through `Translations` with keys in all 12 locale files, and the English in
   `docs/ui-style.md`.
4. Update the subsystem's system doc if behaviour or structure changed (see [../docs-standard.md](../docs-standard.md)).
5. Check the size: `python .claude/pipeline/pipeline.py status` warns past 400 non-test lines.
6. Run the `convention-reviewer` agent on the branch and fix what it finds.
7. Commit and push the branch. CI only runs on PRs, so ask the user to open one unless they already said to. Open it
   against `<base>` with the `commit-and-pr` skill and the `pipeline` label (`--label pipeline`), which starts the
   AI review. Fill in the repo's PR template: `Closes #<issue>`, the acceptance criteria table with the test that
   checks each `[auto]` AC, and a playtest checkbox for each `[play]` AC.

8. Move the card to In review with the `backlog` skill.
