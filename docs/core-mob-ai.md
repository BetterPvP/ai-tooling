# Core: mob AI

Status: Approved · Last verified: 2026-10-08, 9276a60b9

## Purpose

`core/scene/mob/` runs code-driven mobs. A `SceneMob` is an NPC whose behaviour is a stack of `AIComponent`s that
an `AIController` arbitrates each tick, much like vanilla goals but in code we own. The body is a vanilla mob with
its vanilla goals removed, optionally hidden under a ModelEngine model. Logical animation states map to model clips
through providers. Settlers (`SettlerNPC`) are the one user on `camps` today.

## Main types

Root package:

| Type | What it is |
|---|---|
| `SceneMob` | The mob. Owns the AI, navigator, animations, sounds, threat, target, home and activation gate |
| `Disposition` | The coarse default stance: `FRIENDLY`, `NEUTRAL`, `HOSTILE` |

`ai/`:

| Type | What it is |
|---|---|
| `AIComponent` | One piece of behaviour: the controls it claims, `canStart`, `shouldContinue`, `start`, `tick`, `stop`, `replan` |
| `AIControl` | The slots components compete for: `MOVE`, `LOOK`, `TARGET`, `JUMP` |
| `AIController` | The ordered component list. Priority is position, index 0 highest |
| `Navigator` | Pathing over the body's `Pathfinder`, plus trips that search again and give up |

`ai/component/`, the built-in components:

| Type | Controls | What it does |
|---|---|---|
| `WanderComponent` | MOVE | Strolls around home while the mob has no target. Optional rest and floor check |
| `ReturnHomeComponent` | MOVE | Leash. Drops the target and walks home once too far |
| `FollowOwnerComponent` | MOVE | Follows the online owner, teleports when far. Yields while targeting |
| `TargetingComponent` | TARGET | Sets the target from a `TargetSelector` every tick |
| `RetaliateComponent` | TARGET | Targets whoever holds the most threat, decaying threat each tick |
| `MeleeAttackComponent` | MOVE | Chases the target and swings on a cooldown |
| `LookAtTargetComponent` | LOOK | Faces the target's eyes |
| `PostComponent` | MOVE | Walks to a supplied post and holds WORK there |
| `LookAtNearbyPlayerComponent` | LOOK | Faces the nearest player in a radius while not pathing |
| `AttendComponent` | MOVE, LOOK | Stops and faces one player for a set time |
| `OrderToSpotComponent` | MOVE | Walks to a point near an ordered spot, rests, then lets go |

`animation/`:

| Type | What it is |
|---|---|
| `MobAnimation` | Logical states. Looping: `IDLE`, `WALK`, `WORK`. One-shot: `ATTACK`, `HURT`, `DEATH` |
| `AnimationProvider` | Resolves a state to a clip id against the mob's live state |
| `AnimationProviders` | `fixed`, `random`, `sequential`, `when`, `whenTargeting` |
| `AnimationController` | Holds the looping state, swaps clips, plays one-shots and raw clips |

Related, only as far as the AI uses them:

- `listener/MobLifecycleListener`: death sound, no drops, and tearing a mob out on removal.
- `listener/MobCombatListener`: feeds threat on damage, plays HURT.
- `target/ThreatTable`, `target/TargetSelector`, `target/TargetSelectors`: threat by attacker UUID and target picking.
- `faction/Faction`, `faction/FactionRelation`, `faction/FactionService`, `faction/FactionRelationListener`: mob vs mob
  relations, bridged into `GetEntityRelationshipEvent`.
- `sound/MobSound`, `sound/MobSoundBehavior`, `sound/SoundProvider`, `sound/SoundProviders`: the audio twin of the
  animation types.

## How it works

### Spawning: eager or chunk-managed

A `SceneMob` gets its body in one of the two ways every `SceneObject` does.

- Eager: the caller spawns an entity and calls `SceneObjectFactory.spawn(mob, entity)`. The mob is never chunk-cycled.
  The encounter or spawner that made it decides when it comes back.
- Chunk-managed: `SceneObjectFactory.spawn(mob, anchor, entityFactory)`. `SceneMaterializationController` spawns the
  body when the anchor chunk's entities load and takes it away when they unload. Only safe for mobs that stay near
  their anchor, such as settlers.

`SceneTicker` ticks materialized objects only, so a dormant mob costs nothing.

### Init

`onInit` runs on every spawn, so a chunk-managed mob starts from scratch each time. It:

1. Clears the components, target and threat, and resets the activation state.
2. With a `modelId`, binds that ModelEngine model, turns on the hurt tint when `damageTint` is set, and hides and
   silences the host.
3. Removes every vanilla goal from the body.
4. Makes a new `Navigator` and `AnimationController`, sets `homeAnchor` to where the body stands, and attaches the
   sound behaviour.
5. Calls `registerComponents()`, then puts `OrderToSpotComponent` and then `AttendComponent` on top with `addFirst`.
   Attend is always highest, orders second.

### Activation and the body's AI

Each tick `SceneMob.tick` decides if the mob is active. It is inactive when the body is gone or dead, or while any
model plays its `death` clip. Otherwise it is active while a player is within `activationRadius` (48 by default).
That proximity check is sampled once every 20 ticks. A mob that was dead or playing its death clip wakes on the next tick it is alive, if the last check found a player in range.

- First active tick: the runtime starts. The body's AI is switched on if it was off (and remembered), vanilla goals
  are removed again, and `FOLLOW_RANGE` is raised to `pathRange` (48 by default) so the pathfinder can plan long trips.
- Each active tick: `AIController.tick`, then `Navigator.tick`, then `AnimationController.tick`.
- First inactive tick: the runtime stops. Every component stops, pathing stops, target and threat clear, and the
  body's AI goes back off if the runtime turned it on.

Scene behaviours such as the sound timer and nameplates tick either way.

### Removal and respawn

`onDematerialize` stops the runtime and marks the model removed. It runs on a chunk unload and on `remove()`.

`MobLifecycleListener.onRemove` watches `EntityRemoveEvent` and ignores removals the framework causes
(`isDespawning`). An eager mob whose body is removed for any other reason is removed for good. A chunk-managed mob is
removed only when the cause is `DEATH`. Any other removal leaves it registered, and the materialization controller
spawns it again. On `EntityDeathEvent` the listener plays the DEATH sound and clears drops and experience.

### Arbitration

`AIController` keeps components in a list. `add` appends at the lowest priority and `addFirst` inserts at the
highest. `addBefore` and `addAfter` splice next to a registered component, or append when it is not registered.

Each tick:

1. Every running component whose `shouldContinue` is false stops. `shouldContinue` defaults to `canStart`.
2. Each component not running, from highest to lowest priority, starts if `canStart` and every control it claims is
   free or held by a lower-priority component. Starting stops those holders first.
3. Every running component ticks, highest priority first.

A component never takes a control from one of equal or higher priority. Components that claim no controls never
conflict. `stopAll` stops everything running. `replan` stops everything and calls each component's `replan`, so every
component decides again next tick. `clear` stops and unregisters all.

### SceneMob controls

| Call | Effect |
|---|---|
| `startMoving(point or entity, speed)` | `Navigator.moveTo` and hold WALK |
| `travelTo(point, speed, onGiveUp)` | `Navigator.travelTo` and hold WALK |
| `stopMoving()` | Stop pathing and play IDLE |
| `attend(player)` | Feed `AttendComponent` |
| `orderTo(spot)` | Feed `OrderToSpotComponent` |
| `replan()` | `AIController.replan` |
| `setAnimation(state, clip or provider)` | Map a state. Works after spawn, a held state picks it up next tick |

`isValidTarget` checks alive, valid and same world. `getActiveOwner` is the owner when online and in the mob's world.

### Navigator and trips

`moveTo` asks the pathfinder once and ends any trip. `stop` ends the trip and stops pathfinding. `isNavigating` is
true while the pathfinder has a path. Every call does nothing when the body is not a `Mob`.

`travelTo` starts a trip to a fixed point, driven by `Navigator.tick`:

- Arrived means within 1.5 blocks across and 2.5 blocks up or down (`hasArrived`).
- With no current path it searches again, at most once every 10 ticks.
- A body that moves less than 0.05 blocks over 100 ticks searches again.
- After 20 searches it gives up, ends the trip and runs `onGiveUp` once.

### Built-in components

Wander runs while there is no target. Without rest it waits until the mob is not pathing, plays IDLE once on the way
out of movement, and picks a new point at most every `repathCooldownMillis` (3000). The point is random within
`wanderRadius` (8) of home at home's height, walked at `wanderSpeed` (0.8). With `rest(min, max)` it takes each trip
to the end as a `travelTo`, then rests for a random time holding IDLE. Giving up or finding no point also rests. With
`checkFloor(minRadius)` it picks a spot between `minRadius` and `wanderRadius` where a solid block has two passable,
non-liquid blocks above. It scans floor blocks from 6 below to 3 above home's height, prefers the feet height
closest to home's, and tries 8 columns.

Return home starts beyond `leashRange` (30) or in another world. Each tick it clears the target and walks home at
`returnSpeed` (1.0) until within `leashRange * arrivalFactor` (half). Stopping plays IDLE.

Follow owner never runs with a target. It follows an owner more than `followRange` (5) away at `followSpeed` (1.0),
and teleports to them beyond `teleportRange` (25).

Targeting drops an invalid target and sets whatever `TargetSelector.select` returns, or none.

Retaliate runs while the `ThreatTable` is not empty. Each tick it decays every entry by `threatDecay` (0.5),
dropping those at zero, and targets the highest valid attacker. A living attacker that is no longer valid is
removed. Stopping clears the target.

Melee attack starts with a target and runs while it is valid. Out of reach it chases at `chaseSpeed`. Reach is the mob's box grown
by `attackRange` (2.5) overlapping the target's. In reach it swings once per `cooldownMillis`, playing ATTACK and the
ATTACK sound. After a swing it stays rooted for `freezeMillis`, which defaults to the cooldown, and 0 turns it off.
The hit lands at once, after `windupMillis`, or when the model fires the `betterpvp:<strikeKeyframe>` script keyframe
through `ModelEngineScriptDispatcher`. A late hit misses if the target died or left reach. Stopping drops the pending
hit and plays IDLE.

Look at target faces the target's eyes each tick while there is one.

Post takes a `Supplier<Optional<Location>>`. It asks only when deciding: on first start, after a rest, after a
replan, and after a preempted trip. With a post it travels there, and on arrival stops pathing and holds WORK until
replanned or preempted. When the trip gives up it rests (5 to 15 seconds by default) and asks again. With no post
it does not start, and asks again after a rest, leaving lower components free.

Look at nearby player runs while the mob is not pathing. Every 5 ticks it looks for players within `radius` (5) and
keeps the current one until it leaves the radius, the world or the server.

Attend starts once `attend(player)` is called and lasts `durationMillis` (4000). It stops pathing, plays IDLE and
faces the player. Calling again restarts the time. When it ends, whatever it preempted decides again.

Order to spot picks a random point 1 to 3 blocks from the spot, so several mobs sent together spread out. It travels
there at `orderSpeed`, rests 5 to 15 seconds, then lets go. A trip that gives up rests too. An order preempted by
Attend resumes afterwards. A new order while running restarts the trip.

### Animation

`AnimationController.play(state)` holds a looping state and re-resolves it every tick. Switching into a different
looping state is a fresh entry. Asking again for the held state is a refresh. When the resolved clip changes, the old
clip is stopped before the new one plays, so two locomotion clips never layer. Clips play with a 0.2 second blend in
and out.

A one-shot state is forced, so it replays on every request and layers over the loop. An unmapped ATTACK sends entity
status 4 (the vanilla swing) to every player tracking the body. Other unmapped states do nothing.

`force(state)` restarts the clip and holds it if it loops. `play(clipId)` plays a raw clip without restarting one
already playing, and `force(clipId)` restarts it. With no model bound, clip calls do nothing and `hasModel` is false.

`AnimationProvider.resolve(mob, reentry)` carries the fresh-entry flag. `fixed` always returns its clip. `random`
and `sequential` pick again only on a fresh entry and return the last pick on a refresh, so a held loop is not
restarted. `sequential` starts at the first clip. `when` tests its condition on every call and passes the flag to
the chosen branch. `whenTargeting` picks its first branch while the mob has a target. A null id or empty list is
refused.

`MobCombatListener` plays HURT and the HURT sound and marks the model hurt whenever uncancelled damage from a living
entity, or a projectile it shot, reaches the mob. The attacker gains threat equal to the final damage.

## Extending it

A new mob:

1. Extend `SceneMob`. In the constructor set the entity type and `Disposition`, then `modelId`, `activationRadius`,
   `pathRange`, animations and sounds as needed.
2. Override `registerComponents` and add components in priority order with `getAi().add`. Attend and orders go on
   top automatically.
3. Spawn it eagerly with `SceneObjectFactory.spawn(mob, entity)`, or chunk-managed with
   `spawn(mob, anchor, entityFactory)` if it stays near its anchor.

A new component:

1. Implement `AIComponent`. Claim only the controls it really drives, MOVE for movement and LOOK for the head.
2. Move through `startMoving`, `travelTo` and `stopMoving` so the WALK and IDLE clips follow. Call `stopMoving` in
   `stop` if it moved.
3. Take a `LongSupplier` clock for any timing, so tests can drive it.
4. Override `replan` if it caches a decision that should be taken again.

From outside, `replan()` makes a mob reconsider (settlers do it when an assignment changes), and `attend` and
`orderTo` hand it a short task.

## Gotchas

- Priority is list position. `registerComponents` runs before Attend and orders are added on top, so a subclass can
  never outrank them.
- A chunk-managed mob loses its whole AI state on every chunk load: pending orders, threat, rest timers and home are
  reset. Home becomes wherever the body spawns.
- `attend` and `orderTo` do nothing before the first `onInit`, since their components do not exist yet.
- Stopping a held clip sets its lerp-out to 0.2 s first, through the playing clip, since ModelEngine's stop call takes no blend time.
- Retaliate forgets an attacker it can no longer find, such as one that logged out, and drops it as the target.
- `WanderComponent` without `rest` uses `moveTo`, which never searches again. Only `travelTo` trips recover from no
  path or a stuck body.
