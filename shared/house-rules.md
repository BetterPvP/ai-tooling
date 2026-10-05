# House rules

## Code

- **Player-facing text is always translated**: `Translations.component("key", args...)`, with the key added to all 12
  locale files in the module's `src/main/resources/translations/`. Write the English to `docs/ui-style.md`.
- **Every log call ends in `.submit()`**, or nothing is emitted.
- **`@UpdateEvent` methods are public and live in a registered `Listener`.** The executor finds them with
  `getMethods()`, so non-public ones never run. `@Singleton` alone is never ticked.
- **Imports, not fully qualified names**, unless two imported types share a simple name.
- **Lombok `@Value`/`@Data`, never `record`.**
- **Composition over inheritance.** Capabilities are components (`ItemComponent`, `addBaseComponent`), not abstract
  base classes. No hidden wiring in base classes.
- **Class size.** A class earns a file if it holds state or owns a decision that varies. No interface plus two impls for
  a binary you control. Split long classes by responsibility.
- **Stores, orchestration and transfer go behind an interface** bound in a Guice module. No registries or config keys
  choosing an implementation.
- **Inline literals** used in fewer than 3 places. Font keys are always inline.
- **No loops over throwaway arrays** (`for (x : new double[]{a, b})`).
- **Leave shared listeners alone.** Make new code compatible through Bukkit events instead of editing an existing one.
- **Don't build on `PlayerDelayedActionEvent`**. It is being retired. Own the controller, tick and interrupts.
- **In-world features are managed in-world** through an NPC or prop with nested menus. Commands are for staff only.
- **Boss bars**: track viewers in your own `Set<Player>`. Never iterate `BossBar.viewers()` to remove them.

## Writing

- Comments are sparse and explain a non-obvious why. No banner or divider comments.
- Javadocs describe the end state in the present tense. No "replaces X" or "used to". Not every type needs one.
- Describe the mechanism, not the game fiction, including in log messages.
- No em-dashes or semicolons in docs. Don't explain a design decision unless asked.

## Boundaries

- The BetterPvP repo is public and squash-merges. Nothing from `private/` goes into it.
- Claude tooling, system docs and these rules live in the private `BetterPvP/ai-tooling` repo.
