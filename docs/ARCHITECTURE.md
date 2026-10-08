# BetterPvP architecture

A multi-module Minecraft plugin suite for a clan PvP network. Paper 1.21.11, Java 21, Kotlin 2.1.0, Gradle Kotlin DSL.

## Modules

| Gradle id | What it is |
|---|---|
| `:core` | Shared framework: DI, database, items, menus, scenes, sites, networking, utilities |
| `:clans` | Clans, territory, world content, sailing, camps, auction house UI |
| `:champions` | Roles and skills |
| `:progression` | Professions (fishing, mining, woodcutting) |
| `:shops` | NPC shops and auction house backend |
| `:game` | Mini-game framework (CTF, Domination) |
| `:hub` | Lobby server, routing into other servers |
| `:lunar` | Lunar Client API integration |
| `:orchestration`, `:orchestration-service` | Cross-server queueing: client API and the standalone service |
| `:proxy` | Velocity proxy plugin |
| `:private:*` | Private subrepo in `private/` (events, dungeons, store, store-proxy, compatability) |

`private/` is a separate git repository. `settings.gradle.kts` includes its modules only when the folder exists, so the
public modules build without it.

Each module has a `CLAUDE.md` with its package map. Larger subsystems have a write-up in `docs/` (see the map below).

## Build

```bash
./gradlew :clans:compileJava   # compile one module
./gradlew :clans:classes       # compile one module, Java and Kotlin
./gradlew shadowJar            # every module's fat JAR into $rootDir/build/
```

Shadow relocates Caffeine to `me.mykindos.betterpvp.caffeine` and MorePersistentDataTypes to
`me.mykindos.morepersistentdatatypes`. Paperweight userdev gives NMS access.

## Framework

### Plugins and dependency injection

Every module's main class extends `BPvPPlugin` (a `JavaPlugin`) and owns a Guice injector. Services take their
dependencies through `@Inject` constructors. Code outside Guice reaches a service with
`JavaPlugin.getPlugin(SomePlugin.class).getInjector().getInstance(SomeService.class)`.

### Listeners and ticks

A class annotated `@BPvPListener @Singleton` that `implements Listener` is found by the module's `ListenerLoader`
through classpath scanning and registered with Bukkit.

`@UpdateEvent(delay = ms)` marks a method to run periodically. `UpdateEventExecutor` only scans the registered listener
instances, so the method must live on a `@BPvPListener` class. The listener instance is the same singleton injected
elsewhere, so ticked state is shared.

### Config

```java
@Inject
@Config(path = "clans.energy.maxEnergy", defaultValue = "1000")
private double maxEnergy;
```

Values come from the module's YAML files under `src/main/resources/configs/`.

### Events

Custom events extend `CustomEvent`:

```java
@Data
@EqualsAndHashCode(callSuper = true)
public class MyEvent extends CustomEvent {
    private final Player player;
}
```

Use `@Getter @EqualsAndHashCode(callSuper = true)` with explicit constructors when `@Data` doesn't fit.

### Database

jOOQ over PostgreSQL through `database.getDslContext()`. Always give columns an explicit type,
`field(name("column"), Long.class)`, or jOOQ picks an ambiguous overload. Flyway migrations live in
`<module>/src/main/resources/<module>-migrations/postgres/` and are named `V{YYYYMMDD}_{n}__{Description}.sql`.

### Stores and networking

Persistence stores, server orchestration and player transfer sit behind interfaces bound in a Guice module, so another
network can swap an implementation without touching callers. `core/framework/net/` carries messages between servers
and `core/world/site/` models the places a player can be. See `docs/core-network.md` and `docs/core-sites.md`.

### Translations

Player-facing text goes through `Translations.component("key", args...)`. Keys live in
`core/src/main/resources/translations/core_<lang>.properties` for en, ar, de, es, fr, ja, ko, ms, nl, pl, ru and zh.
Values use MessageFormat (`{0}` arguments, apostrophes doubled) and carry no colour. Colour is applied in code. The files
are UTF-8 with CRLF line endings.

### Logging

`@CustomLog` gives a fluent logger. `log.warn("x {}", a)` builds a message and `.submit()` emits it.

### Boss bars

Show and hide with `BossBar.addViewer(Player)` and `removeViewer(Player)`. Keep your own `Set<Player>` of viewers,
because `BossBar.viewers()` returns `BossBarViewer`s, which are not `Audience`s.

A gamer's `BossBarOverlay` and `BossBarQueue` are cleared when the player quits (`GamerBossBarListener`). The
`Gamer` can outlive a quit when the player rejoins before the client unloads. Re-add per-player overlays on
`ClientJoinEvent`, not `AsyncClientLoadEvent`, and reuse one `DisplayObject` per feature (remove, then add) so a
double join still leaves one.

`PlayerHeadProvider.head(...)` always returns a painted head. It shows a bundled question-mark head until the
skin loads, and keeps the old head while a refresh runs. Key any memo on the exact `(scale, top)` you paint.

## Documentation map

| Where | What |
|---|---|
| `CLAUDE.md` (root) | How to work in this repo |
| `<module>/CLAUDE.md` | A module's package map and gotchas |
| `CONTEXT.md`, `<module>/CONTEXT.md` | Domain language and lifecycles |
| `docs/core-item-access.md` | Item capability gating by scope |
| `docs/core-cutscenes.md` | Camera and dialogue cutscenes |
| `docs/core-dialogs.md` | Full-screen custom dialogs: the dialog canvas library |
| `docs/core-gui-screens.md` | GUI screen files: JSON screens, schema, runtime, pack generation |
| `docs/core-sites.md` | Sites, instances, residency, crews, owned sites |
| `docs/core-construction.md` | Structures, jobs, checks, blueprints and structure views |
| `docs/core-network.md` | Message bus, site directory, player transfer, cross-server chat |
| `docs/clans-resource-nodes.md` | Resource-node POIs (ores, trees, fishing) authoring |
| `docs/clans-props.md` | Data-driven props authoring |
| `docs/clans-sailing.md` | Voyages, ships and crews |
| `docs/clans-camps.md` | Camps: records, structures, upgrades, settlers |
| `docs/SCENES.md` | Scene and world-content authoring |
| Outline, https://outline.betterpvp.net | Designs, PRDs and plans |
