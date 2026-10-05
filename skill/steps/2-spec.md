# Step 2: Spec

The spec says what the slice must do. The user owns it. You draft, they decide.

1. Draft the issue body:

   ```
   ## Goal
   One or two sentences on what the player or staff member gets.

   ## Acceptance criteria
   - [ ] AC1 [auto] ...
   - [ ] AC2 [play] ...

   ## Out of scope
   - ...
   ```

2. Each AC is one sentence of observable behaviour. Mark it `[auto]` when a unit test can check it, `[play]` when only
   a person in game can. Prefer `[auto]`: a rule that depends on game logic can usually be tested if the logic sits
   outside the Bukkit listener.
3. Use the `grill-me` skill on anything ambiguous: edge cases, what happens on restart, on logout, with two players,
   with no resources. Every answer becomes an AC or an out-of-scope line.
4. Check terms against `CONTEXT.md` and the PRD in Outline. Use the domain words, not new ones.
5. When the user is happy, write the body with `gh issue edit <n> -R mykindos/BetterPvP --body-file <file>`.

A design change found later comes back here first: edit the ACs, then the tests, then the code.
