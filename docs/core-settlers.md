# Core: settlers

Status: Approved · Last verified: 2026-10-08, 5f976d8fd

## Purpose

`core/world/settler/` gives a site people who live there. A settler is data on its owner's record, with a profession,
traits, morale and a place to work. Core rolls settlers, keeps rosters within their caps, staffs construction jobs with
crews, pays wages, settles morale and shows every settler as a mob in its site's world. Core knows nothing of what owns
a site. The module that owns a kind of site supplies its rosters, caps, numbers and vocabulary through one interface,
the way construction does (see `core-construction.md`). Camps are the one user today (see `clans-camps.md`).

## Main types

Root package, the model and the service:

| Type | What it is |
|---|---|
| `SettlerSite` | What a site's module supplies: roster, caps, permissions, look, home, workplaces, click, crew, wage, table and morale hooks |
| `SettlerService` | The `SettlerSite` per site id, and every roster change: grant, remove, dismiss, assign, unassign |
| `SettlerResult` | Done with the settler, or refused with a red translated reason |
| `SettlerAction` | The player actions a site permits or refuses: Hire, Assign, Dismiss, Pay |
| `Roster` | Every settler one owner has at one site, the wage clock and the recent departures. Data only |
| `Settler` | One person: name, history line, rarity, profession, specialty, traits, morale, assignment, state, jobs finished |
| `SettlerState` | Idle, Working or Striking |
| `SettlerRarity` | Common, Uncommon, Rare, Legendary, each with its name colour |
| `SettlerDeparture` | A settler who left: name, rarity, reason and when, kept for a week |
| `SettlerLeaveReason` | Dismissed, Unhappy or Unpaid |
| `Profession` | What a settler does: its `WorkplaceKind`, its workplace and its specialties |
| `WorkplaceKind` | Construction (staffs jobs) or Workplace (works at one named place) |
| `ProfessionRegistry` | Every `Profession`, by id |
| `Trait` | Something that sets one settler apart: group, trade-off flag, least rarity, professions that roll it |
| `TraitGroup` | When a trait acts: Builder, Resident, Site-wide or Personal |
| `TraitRegistry` | Every `Trait`, by id |
| `SettlerTable` | What new settlers are rolled from: `RarityNumbers` per rarity, name lists, history lines per source |
| `RarityNumbers` | What a rarity means: trait count, trait strength, profession stats, trade-off chance |
| `SettlerTemplate` | What a new settler must be: rarity, profession, source and history arguments |
| `SettlerGenerator` | Rolls a `Settler` from a template and a table |
| `SettlerLook` | Model, optional skin, idle, walk and work clips, and size |
| `WorkplaceBonus` | What the settlers working at a workplace add to it together |

Events: `SettlerJoinedEvent`, `SettlerLeftEvent` (with its reason) and `SettlerAssignedEvent` (with the previous
assignment).

`crew/`, Builders on construction jobs:

- `CrewRule`: the `crew` job rule. It holds a job short of Workforce and sets its rate to the crew's speed.
- `CrewService`: joins Builders to crews and lets crews go.
- `CrewSpeed`: a crew's speed, each Builder's share of it and the Speed it wastes.
- `BuilderStats`: what one Builder brings to one job: Workforce, Speed, efficiency, trade and compatible trades.
- `CrewLimits`: a site's caps on one crew: size, speed, per rarity, and the compatible bonus. `NONE` has none.
- `CrewTally`: who did how much of one job, sampled while it runs. `CrewTally.Share` is one Builder's part.
- `CrewTallies`: a `CrewTally` for each running job on a loaded site, and the last finished one per structure.

`wage/`, paying settlers:

- `WageModel`: coins an hour for a settler, working or not. `FixedWageModel` pays one rate per profession and rarity.
  `IdleWorkingWageModel` pays an idle rate and a higher working rate.
- `CoinAccount`: where a site's wages come from.
- `Payroll`: settles wages each minute, starts and ends strikes, and lets go of strikers past the limit.
- `SettlerStrikeEvent`: paid settlers stopped work, or went back to it.

`morale/`, how settlers feel:

- `MoraleModel`: the site's morale for each settler, the leave line, the leave time, and who never leaves.
- `MoraleEngine`: settles morale each minute and lets go of settlers unhappy for too long. Its `multiplier` is what
  resident bonuses are scaled by.

`recruit/`, getting settlers:

- `SettlerCandidate`: a rolled settler who could join, its asking price and when it stops waiting.
- `SettlerOdds`: weighted rarity and profession odds. `pick` rolls any weighted map.
- `SettlerGrants`: how content outside the framework gives a site a settler, rolled from the site's own table.

`presence/`, settlers in the world:

- `SettlerPresence`: world content that gives every settler of a loaded site a body and keeps the bodies current.
- `SettlerNPC`: one settler's body, a `SceneMob` (see `core-mob-ai.md`).
- `SettlerFactory`: the scene factory that owns settler bodies. They are never spawned by command.

## How it works

### Sites and rosters

A module registers its `SettlerSite` with `SettlerService.register(siteId, site)`. Settlers then live at every
instance of that site whose roster is loaded. Where the site id is unknown or the roster is not loaded, every action
is refused with `core.settler.not_loaded`, lookups are empty and the population cap is 0. The roster is data, kept in
whatever record the module writes. The service calls `SettlerSite.changed` after every change, and a refused action
writes nothing.

### Joining and leaving

- `grant` adds a settler while the roster is below `populationCap`. It joins Idle with no assignment and fires
  `SettlerJoinedEvent`. A settler already on the roster is refused. The working cap never stops a join, so a
  professional over it wanders.
- `remove` takes a settler off at once for a reason and fires `SettlerLeftEvent`. It records a `SettlerDeparture` and
  drops departures older than a week. There is no leaving state.
- `dismiss` is `remove` for Dismissed, refused while `SettlerSite.jobRunning` says the settler is on a running job.

### Assignment

An assignment is a workplace id. For a Workplace profession it is the profession's workplace. For a Construction
profession it is the id of the structure whose crew it is on (see Crews).

- `assign` makes a settler Working there and fires `SettlerAssignedEvent`. It refuses a settler with no profession, the
  wrong workplace, a striker, a move off a running job, and a profession at its `workingCap`. A settler already
  assigned is not counted against the cap twice. Assigning it where it already is does nothing.
- `unassign` makes a Working settler Idle and leaves a striker Striking. It is refused on a running job.
- The forms that take a `Player` check `SettlerSite.allows` for Assign or Dismiss first and refuse with
  `core.settler.not_allowed`. `grant`, `remove` and the forms without a player check no permission.

### Crews

A Builder is a settler whose profession is `WorkplaceKind.CONSTRUCTION`. A job's crew is its `Job.staff`. A Builder is
on a crew only while it is on the staff and assigned to that structure.

`CrewService.enlist` puts a Builder on a structure's job. It refuses, in order: not loaded, no job (none, or its time
is up), not found, not a Builder, already on this crew, busy (assigned anywhere else, even a paused job), the crew at
`CrewLimits.maxSize`, the crew at its `perRarity` limit for the Builder's rarity, and whatever `SettlerService.assign`
refuses. Strikers count toward both limits. On success the site is written down and the job's rules are applied again
at once, so a crew that now meets the threshold starts the job. `join` is `enlist` for a player in a world, after the
site `allows` them Assign. A paused job or one waiting for its first crew can be joined.

`CrewRule.threshold` is the Workforce a job needs. A build or advance needs the `workforce` of the stage it works
toward. A repair or move needs half the `workforce` of the stage the structure stands at, rounded up. A Fit upgrade
needs the upgrade's `workforce`. An unknown type, stage or upgrade needs 0, and a job needing 0 runs with no crew at
its listed time.

Each member's `BuilderStats` come from `SettlerSite.builderStats` for this job beside this crew. A striker, a settler no
longer on the roster and a Builder the site gives no stats for bring nothing. `holds` is true while the summed
Workforce is below the threshold. `rate` is the crew's speed, or 1 with no working crew.

`CrewSpeed.of` ranks the crew by Speed. The fastest counts its full Speed and every other one its Speed times its
efficiency. A Builder whose compatible trades include another member's trade counts fully whatever its rank, plus
`compatibleBonus`. The total stops at `maxSpeed`, and over the cap every share is scaled down alike. Three Builders at
1.0 Speed and 50% efficiency run a job at 2.0.

Leaving a crew:

- Unassigning a Builder takes it off the staff at once (on `SettlerAssignedEvent`), and the job pauses if the rest fall
  short. `SettlerService` refuses it while the job runs, through the site's `jobRunning`.
- A member that leaves the roster is dropped from the staff at the next sweep.
- When a job's time is up, its crew is let go once, before anyone claims the structure. Each member still on the roster
  gets one more `jobsFinished`, the site's `crewFinished` hears the crew, the staff is cleared and each Builder is
  unassigned and Idle.
- A cancelled job or a removed structure lets its crew go with no credit and no `crewFinished`.

`CrewService` releases on `StructureStatusChangeEvent`, `StructureRemovedEvent` and a 5 second sweep of every loaded
worksite. The sweep catches jobs that finished while their world was closed, and unassigns any Builder whose assignment
points at no job, a finished job or a job whose staff lacks it.

`CrewTallies` samples every loaded worksite every 5 seconds, and on `StructureClaimedEvent`. A tally starts when a job
is first seen unfinished and counts only progress from then on. Each sample splits the progress since the last between
the working members by `CrewSpeed.contributions`, and adds up each member's `CrewSpeed.wasted` over time. Time the job
is held counts for neither. Progress made after the whole crew left goes to those who worked, in the same proportions.
`tallies(site)` lists the running tallies, then the last finished one per structure.

### Rolling

`SettlerGenerator.roll` gives a new id, the template's rarity and profession, a name of a first name and a byname, a
history line picked from the source's lines, and one of the profession's specialties. Then it rolls as many traits as
the rarity's `RarityNumbers` say. Each trait is drawn from those whose least rarity it meets and whose professions
include its own (a trait with none listed rolls on anyone). It is a trade-off with the rarity's chance, and falls back
to the other kind when none of the wanted kind is left. No trait rolls twice. An unknown profession throws, so callers
check `knows` first. A rarity missing from the table rolls as `RarityNumbers.PLAIN`.

Trait strength and profession stats are never stored on the settler. Readers take them from the table by rarity, so a
table change reaches settlers who exist.

### Wages

`Payroll` settles each site whose world is loaded here every minute. A settler's hourly cost is the `WageModel` rate
times `wageMultiplier`. The idle and working model counts a settler as working while it is Working, or Striking with an
assignment.

1. With no `wageFund`, no `wageModel` or an hourly cost of 0, the clock moves to now and any strikers go back.
2. The first settlement only starts the clock.
3. Each later one charges the paid settlers who are not striking for the real time since the last. Whole coins come
   out of the fund and the part of a coin carries over, so a closed world is charged in full when it opens.
4. When the fund cannot pay, it pays what it holds and every paid settler strikes, dated to when the money ran out.
5. Strikers go back once the fund holds a minute of the site's hourly cost (at least 1 coin), never in the settlement
   that started the strike. They go back Working if still assigned, Idle if not.
6. A striker still striking past `strikeLimit` (72 hours by default) leaves as Unpaid.

### Morale

`MoraleEngine` settles each site whose world is loaded here every minute. It sets every settler's morale to what the
site's `MoraleModel` gives, kept between -100 and 100. A settler below `leaveBelow` starts an unhappy clock, and one
that stays below for `leaveAfter` leaves as Unhappy. A settler at or above the line, or one `mayLeave` exempts, clears
its clock. Closed-world time counts toward the clock.

`MoraleEngine.multiplier` is 1 + morale / 200. `WorkplaceBonus.total` adds each resident's share times that multiplier
and caps the sum. Its residents are the settlers assigned there and Working, so strikers bring nothing.

### Recruiting

`SettlerGrants.grant` rolls a settler from the caller's template with the site's `table` and adds it through
`grant`, refused when the site has no table or no room. `SettlerOdds` and `SettlerCandidate` are building blocks for a
site's own recruiting. `SettlerOdds.NONE` means no profession, and no weight above 0 rolls Common with no profession.

### Presence

The module binds `SettlerPresence.content()` to its site's worlds. On install, and every 5 seconds after, it spawns a
`SettlerNPC` for each settler on the roster and removes bodies of settlers who left. Joins and departures act at once.

- A body is anchored at `SettlerSite.home`, or the world's spawn when the site gives none. It is chunk-managed and is
  dressed again each time it spawns: the look's clips, the model at its size with a 1.5 hitbox, the skin when it is
  installed, a nameplate of name and profession on the head bone, and an end rod particle for a Legendary.
- A missing model is logged once and the body shows no model.
- Its AI is Post (speed 0.6 to `SettlerSite.workplace` while Working with an assignment), Wander (radius 12, rests of
  5 to 15 seconds, floor check) and Look at nearby player (5 blocks).
- An assignment change or a strike replans a spawned body. A right-click attends the player, then calls
  `SettlerSite.interact`.
- `gather` orders every spawned body of a site in a world to a spot.

## Extending it

A new kind of site:

1. Implement `SettlerSite`. Return the loaded `Roster`, write it down in `changed`, and supply `populationCap`,
   `workingCap`, `allows` and `look`.
2. Override `home`, `workplace` and `interact` for the world, `table` for rolling, `wageModel`, `wageFund`,
   `wageMultiplier` and `strikeLimit` for pay, and `moraleModel` for morale.
3. Register it with `SettlerService.register` under the site id.
4. Bind `SettlerPresence.content()` to the site's worlds.

A construction site with Builders:

1. Register a Construction `Profession`, and give `StructureStage` and `StructureUpgrade` a `workforce`.
2. In the `SettlerSite`, return `BuilderStats` from `builderStats` for Builders and limits from `crewLimits`. Report
   `jobRunning` for a Builder on its crew while the job runs and is not held.
3. Return the `CrewRule` from the `ConstructionSite`'s `jobRules`.
4. Use `crewFinished` for anything a finished crew earns, such as a refund.

A new profession or trait: register it in `ProfessionRegistry` or `TraitRegistry` before anything rolls. Its effect is
read by the system it affects, from its id.

Give a site a settler from content with `SettlerGrants.grant`.

## Gotchas

- Wages and morale settle only on the server holding the site's world, so two servers never charge one fund. Morale is
  not back-filled while closed. It is worked out once the world opens.
- `Payroll` and `MoraleEngine` call `changed` every settlement, so a loaded site's record is marked each minute.
- Departures older than a week are dropped only when someone else leaves. `departedSince` filters by time anyway.
- `SettlerGenerator.roll` throws on an unregistered profession. Use `knows` or route through a caller that checks.
- A crew is let go when the time is up, not when the structure is claimed. A job Ready to claim has no crew.
- Moving a Builder between crews is two steps: take it off, then join. Joining refuses a busy Builder.
- Strikers stay on the staff and are credited with the job, but bring no Workforce or Speed.
- Tallies live in memory. A restart starts each one again from where its job stands, and a cancelled job loses its
  tally.
- A settler's body is the factory's invulnerable backing entity and its model never flashes hurt, so settlers cannot
  be harmed.
- Presence never moves a body whose chunk is not loaded. It asks for the post again when the body spawns.
