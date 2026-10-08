# Core: construction

Status: Approved · Last verified: 2026-10-08, 164ac7dab

## Purpose

`core/world/construction/` lets players raise, move, advance, upgrade, repair and demolish structures on a site.
Jobs run in real time, so work carries on while nobody is there and the world is not loaded. Core knows nothing of
what owns a site, what pays for building or who counts as a member. The module that owns a kind of site supplies
all of that through one interface. Camps are the one user today (see `clans-camps.md`).

## Main types

Root package, the rules and the data:

| Type | What it is |
|---|---|
| `ConstructionSite` | What a site's module supplies: holdings, ledger, permissions, membership, gates, job rules, refund share, contents |
| `ConstructionSites` | The `ConstructionSite` per site id. Finds the `Worksite` for a world and answers `canUse` and `demolishRefund` |
| `ConstructionService` | The actions only. Each one runs the checks, pays, changes the record and fires events |
| `ConstructionChecks` | Why an action would be refused. Menus and the preview ask it, and the service runs the same checks |
| `StructureStatusTracker` | Applies job rules, lets self-repairing structures come back, fires `StructureStatusChangeEvent` |
| `ConstructionAction` | The player actions a site permits or refuses |
| `ConstructionResult` | Done with the structure, or refused with a red translated reason |
| `StructureCatalogue` | Every `StructureType`, by id |
| `StructureType` | One kind of building, as code: tier, required structures, required zone tag, stages, flags, move, repair and upgrades |
| `StructureStage` | One step of the stage chain: schematic, cost, build time, Workforce |
| `StructureFlags` | `movable`, `demolishable`, `selfRepairing`, `publicUse`, `startsBroken`, `demolishRefund` |
| `StructureUpgrade` | One upgrade offered at a stage: cost, time, Workforce and an optional piece |
| `Holding` | Every structure one owner has in one place. Data only |
| `PlacedStructure` | One structure: type, stage, position, condition, job, `disabledAt`, storage, picked upgrades |
| `StructurePosition` | Anchor block and quarter turns |
| `StructureCondition` | The building itself: Under construction, Active, Disabled, Needs repair, Not placed |
| `StructureStatus` | What a player sees, worked out from condition and job. Only Active is usable |
| `Job` | Work under way, kept as a checkpoint so progress is read without ticking |
| `JobKind` | Build, Advance, Move, Repair, Fit upgrade |
| `JobRule` | Something outside a job that holds it or sets its rate |
| `ResourceCost` | An amount per resource id. Core never learns what the resources are |
| `ResourceLedger` | Whatever pays for construction on a site |
| `StructureContents` | Something a structure holds that drops itself on demolish |
| `StructureStorage` | Chest, trapped chest and barrel contents kept on the record, with its `Slot` per container |
| `StructureShapes` | Where a structure's build lands: placement, named points, upgrade pieces, cached footprints and bounds |
| `FitCheck` | Build zone and clearance check for a placement |
| `BuildZones` | World content turning Mapper cuboids named `build_zone` into zones |
| `Worksite` | One site's holding in its loaded world, with its `ConstructionSite` |
| `SiteHolding` | The same without a world, for checks that work while the world is unloaded. Package-private |

Events: `StructurePlacedEvent`, `StructureRemovedEvent`, `StructureClaimedEvent`, `StructureUpgradedEvent`,
`StructureStatusChangeEvent` and `StructurePieceUseEvent`.

`blueprint/`, placing by hand:

- `StructureBlueprintItem`: the `core:structure_blueprint` item, named after its structure as a build or a move.
- `StructureBlueprintComponent`: the structure type id, plus the placed structure it moves if it is a move blueprint.
- `StructureBlueprintSerializer`: writes both to the item's data. A move id that is not a UUID reads back as none.
- `BlueprintSessions`: the preview while a blueprint is held, and the build or move on right-click. It also hands out
  blueprints with `blueprintFor` and `blueprintToMove`.

`view/`, the structure in the world:

- `StructureViews`: world content that shows every structure of a loaded holding and keeps it current. It also guards
  clicks on structures and writes containers down on close.
- `StructureView`: one structure's blocks, label, claim flash, upgrade pieces and containers. Package-private.
- `StructureProp`: the label, a two-line text display that carries a hitbox while it asks for an action.
- `ClaimFlash`: gold glowing block displays over a structure waiting to be claimed. Package-private.
- `ConstructionPropFactory`: the scene factory that owns structure props. They are never spawned by command.

## How it works

### Sites

A module registers its `ConstructionSite` with `ConstructionSites.register(siteId, site)`. Construction then works on
every instance of that site whose holding is loaded. `ConstructionSites.worksite(world)` finds the instance a world
belongs to and asks the site for its holding. The holding is data, kept in whatever record the module writes, so it
survives the world closing or being rebuilt. The service calls `ConstructionSite.changed` after every change, and the
module writes the record down.

### Checks

`ConstructionChecks` holds every refusal. Each action runs its checks in a fixed order with cost last, so a menu shows
the same reason the action would give.

- Build: the site allows the player `BUILD`, required structures are built, the site's `blocked` gate passes, the
  stage 0 build fits, the ledger can afford stage 0.
- Move: allowed, the type is movable, no job, the new spot fits ignoring the structure itself, the move cost.
- Advance: a next stage, Active with no job, requirements and gate for that stage, the bigger stage fits, its cost.
- Upgrade: allowed, a known upgrade, its stage reached and not yet picked from, no job, Active, its cost.
- `unavailable` and `upgradeUnavailable` take a `SiteKey` and work while the world is unloaded. They skip the fit.

A required structure counts once it stands finished (`Holding.hasBuilt`). A world that is no site instance refuses a
build with `core.construction.cannot_build_here`. A site whose holding is not loaded refuses with
`core.construction.no_holding`.

### Fitting

`FitCheck` passes when every column of the footprint is inside a build zone at both its bottom and its top, and the
zone carries the type's required tag if it has one. The bounds must also keep `CLEARANCE` (5) blocks from every other
structure's bounds. Ground a move is heading to and the bigger stage an advance is growing into count as taken.
`clashes` gives the columns that fail, for anything that marks them out to the player. The same check serves the preview, a build, a
move and an advance.

### Jobs and time

A `Job` keeps its progress at a checkpoint and its rate since then. `progress(now)` is worked out from the clock, so a
job finishes while its world is unloaded. Each `JobRule` from the site can hold a job or set its rate. Holds are named,
and a job runs only with none. Rates from every rule multiply. Any change of pace takes a checkpoint first. Rules only
govern running jobs, so a finished job waits to be claimed whatever changes around it.

`StructureStatusTracker.refresh` applies the rules, brings back self-repaired structures and fires
`StructureStatusChangeEvent` for every status that changed since it last looked.

### Actions

`ConstructionService` is actions only. Player actions check the site's permission for their `ConstructionAction`.
Site-behalf actions check no permission.

- `build`: pays stage 0 and adds the structure Under construction with a Build job.
- `claim`: needs a finished job. A build becomes the type's initial condition (Needs repair if it `startsBroken`),
  an advance moves to its stage, a move to its target, a repair to Active, an upgrade job records the upgrade.
  Fires `StructureClaimedEvent`.
- `cancel`: refunds what the job spent while it is still running. A cancelled build leaves the holding. Any other job
  leaves the structure as it was.
- `move`: instant when the move time is zero or the structure is Not placed, which puts it back Active. Otherwise a
  Move job. Storage is kept either way.
- `advance`, `repair`: player and site-behalf forms. A zero repair time repairs at once.
- `upgrade`: one upgrade per reached stage. Zero time fits it at once, otherwise a Fit upgrade job. Picked upgrades stay
  through later advances.
- `demolish`: needs a demolishable, standing structure with no job. It refunds the site's share of what reaching its
  stage cost, leaves the holding, then drops every `StructureContents` and its stored items at its centre.
- `disable` (site-behalf): knocks an Active structure out and stamps `disabledAt`.
- `finish` (site-behalf): completes a running job at once and clears its holds. Nothing is paid.
- `grant`: adds a structure with no checks and nothing spent, such as a holding's starting structures.

### Status

`PlacedStructure.status(now)` derives the status. A held job is Paused and a done one is Ready to claim. A running
build or move is Under construction and a running advance is Advancing. A repair or upgrade job leaves the status of
the condition. Only Active is usable. A Disabled structure whose type is `selfRepairing` goes back to Active once its
repair time has passed since `disabledAt`, unless a repair job is on it.

`ConstructionSites.canUse` decides who may use a structure's features: anyone if its type is `publicUse`, otherwise
whoever the site's `isMember` counts.

### The structure in the world

The module binds `BuildZones` and `StructureViews.content()` to its site's worlds. `StructureViews` refreshes every
loaded worksite each second and syncs a `StructureView` per structure. It also syncs on placed and status events and
takes a view down on `StructureRemovedEvent`.

- A Build job raises the build layer by layer with its progress. Any other job leaves every layer standing.
- A new stage or a claimed move takes the old build down and puts the new one up.
- The label stands on the build's `label` point, or above the roof if it has none. Line one is the name. Line two is
  what is happening and the time left, Ready, Disabled or Needs repair. It is empty when there is nothing to report.
- While Ready to claim, the structure blinks with a `ClaimFlash` and the label carries a hitbox. Clicking it claims.
- Upgrade pieces stand on the finished build at each upgrade's `upgrade:<id>` point and come down before any of it.
- A Not placed structure has nothing in the world.

Right-clicks on a structure that is under construction or Ready to claim do nothing, so its containers stay shut. A
right-click on an upgrade piece of an Active structure fires `StructurePieceUseEvent` for a player `canUse` allows.
Anyone else gets `core.construction.not_yours`. A handled event stops the click.

### Storage

Every chest, trapped chest and barrel in a build is a `StructureStorage.Slot`, keyed by where it sits in the build.
Moves and rotations do not change the key. A container is filled from the record when its layer goes up, written down
on inventory close, and written down and emptied before its layer comes down. When a finished build no longer has a
container, its items move into the others and the overflow drops. Storage stays reachable while a structure is
Advancing, Disabled or being moved.

### Blueprints

Holding a blueprint opens a ghost of the build on the block above the one the player looks at, within 24 blocks.
A move blueprint shows the structure's current stage. The ghost starts facing the player and each sneak turns it a
quarter. `ConstructionChecks.problem` or `moveProblem` decides green or red, and the action bar shows the reason.
Right-click builds or moves there and uses one blueprint up. A refusal keeps the blueprint and says why.

## Extending it

A new kind of site:

1. Implement `ConstructionSite`. Return the loaded `Holding`, write it down in `changed`, and supply a
   `ResourceLedger`, `allows` and `isMember`.
2. Override `blocked` for the site's own gates, `jobRules` for holds and pace, `demolishRefund` for its share and
   `contents` for whatever else a structure holds.
3. Register it with `ConstructionSites.register` under the site id.
4. Bind `BuildZones` and `StructureViews.content()` to the site's worlds, and tag Mapper cuboids `build_zone`.

A new structure:

1. Implement `StructureType` and register it in `StructureCatalogue`. Keep the code to identity and rules, and read
   the numbers from the module's config.
2. Give each stage a schematic. Add a `label` point where the label should float, and an `upgrade:<id>` point for
   each upgrade with a piece.
3. React to `StructureClaimedEvent`, `StructureUpgradedEvent`, `StructureStatusChangeEvent` or
   `StructurePieceUseEvent` for what the structure does. Check `StructureStatus.isUsable` before a feature works.

Hand players a blueprint with `BlueprintSessions.blueprintFor` or `blueprintToMove`.

## Gotchas

- `StructureStatusTracker.refresh` runs from `StructureViews` once a second and from `CrewService` on crew changes, so
  only for loaded worlds. Self-repair and status
  events wait until the world is loaded again. Job progress does not.
- Status precedence: Not placed wins, then Paused, then Ready to claim. Next a Disabled condition reads as Disabled
  whatever job runs. Otherwise a build or move reads as Under construction and an advance as Advancing.
- `StructureShapes` caches footprints and bounds keyed by the schematic service's generation. A schematic reload
  drops the cache, so do not hold on to a footprint across reloads.
- `StructureStorage` reads only loaded chunks and only container blocks. A missing block means nothing is written.
- `canUse` gates upgrade pieces only. Who may open a structure's containers is the site's zone rules.
- Demolish removes the structure before it drops contents, so a `StructureContents` sees the holding without it.
- `ConstructionAction.ADVANCE` and `JobKind.ADVANCE` read `UPGRADE` from old records, and stage reads `version`.
