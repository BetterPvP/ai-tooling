# Camps

`world/camp/` is a clan's own place, reached by ship like anywhere else. It is an `OWNED` site whose owner is the
clan id, so the site framework works in numbers throughout.

- `Camps`: the whole of what core is told: which clan a player belongs to, what their camp is built from, and the
  `clan` admission rule. Allies are admitted, because a crew sails as one party and is admitted or refused as one,
  so members-only would strand an ally at sea rather than merely turning them away.
- `Camp`: what is kept between visits: the skin, the `Holding` (core construction's structures and jobs), the
  Wood/Stone/Iron balance and the clan's own rank permissions (null until changed, then a copy of the defaults).
- `CampStore`: reads and writes those records through whatever `SiteStorage` is bound. A
  record is read once, on join. Anything that changes a camp calls `changed(clanId)`, `Camps` flushes changed records
  every 5 seconds, and `Clans.onDisable` waits for a final flush.
- `CampConstruction`: the camp's `ConstructionSite`: holding, ledger, permissions, the tier gate (tier N needs a
  Great Hall at version N, versions counting from 0) and the overflow drop after a demolish.
- `CampConfig`: `configs/camps.yml`: chest capacity, deposit values by item key, overflow items, claim layers and
  default rank permissions.
- `resource/`: `CampResources` (the ledger), `ResourceChests` (Mapper points named `resource_chest` in a structure's
  build), `ResourceChestDeposit` (right-click a resource chest to deposit everything it takes, refused whole if over
  capacity) and `ResourceOverflow`.
- `structure/`: `CampStructures` registers every camp structure (code: id, tier, requirements, flags) as a
  `CampStructure` whose numbers (versions with build, cost and time, move, repair, demolish refund, icon) come from
  `camps.yml` `structures.<id>`. `StartingCamp` seeds an empty holding from the skin's `camp_start` perspective
  markers tagged `structure:<id>` (the Dock starts broken).
- `menu/`: `ConstructionMenu` (availability via `ConstructionChecks.unavailable`, hands out blueprints) and
  `CampPermissionsMenu` (leader edits, leader row always allowed). Players reach both only through the Steward.
- `hall/`: the **Steward**, one NPC on the Great Hall's `steward` point. Right-click opens `GreatHallMenu`, the hub
  for everything a clan manages: Settlers (roster), Hiring, Wages, Crews, Farm, Construction, Upgrades and
  Permissions, nested with `BackButton`. **No player commands for camp management.** New features get a page under
  the Steward.
- `settler/`: the camp's settlers. See **Settlers** below.
- `protection/`: `CampGrounds` covers the camp world with one zone (priority 1, adventure) whose `CampGroundsRule`
  denies breaking and placing and lets only members open containers, plus one zone over `farm` cuboids (priority 2,
  survival for members) where members plant and harvest crops. Resource nodes and the dock sit above both and keep
  their own rules. `CampProtectionListener` stops explosions, fire, decay, mobs, trampling and bone meal changing the
  land, and sends the denial message.
- `CampRespawn`: every clan member respawns at their own camp's Barracks (the build's `respawn` point, broken or
  not), wherever they died. A camp loaded here takes them straight there. Otherwise they respawn normally and are
  sent with `Placement.send(player, handle, "barracks")`, a named landing core's `SiteLandings` resolves on the
  camp's server. `CampArrivalNotices` lists structures ready to claim, needing repair or disabled when a member
  arrives. Allies get their own row in the permissions menu (actions plus container access), stored on `Camp`.
- Structures, jobs, upgrades, item storage, the use gate, disabling and self-repair: see `core-construction.md`.
- `upgrade/`: each effect class declares its upgrade through `CampUpgrades.declare` and checks `CampUpgrades.has`.
  Numbers are in `camps.yml` `structures.<id>.upgrades.<id>`. `structure/UpgradePieces` handles piece clicks.
- `Camps.isMember` (the clan) is who may use a camp structure that is not public.
- `CampContent`: `CampGrounds`, the dock, core's `BuildZones` (Mapper cuboids named `build_zone`), `StartingCamp`,
  `StarterCrew`, core's `StructureViews`, core's `SettlerPresence`, the Steward, `DockArrivals` and the Deputy
  Steward, in that order.

**The world is derived, the record is not.** A camp world is built from a template and can be rebuilt from one at any
time, so nothing that has to survive that lives in its blocks.

## Settlers

`settler/` is the camp side of core's settler framework. Rosters, rolling, crews, wages, morale and bodies work as
`core-settlers.md` describes. The numbers are in `configs/settlers.yml`.

- `CampSettlers`: the camp's `SettlerSite`. The roster, wage fund and recruiting state live on the `Camp` record.
  - Population follows the Great Hall's highest standing stage (`population.by-hall-stage`, 6, 12, 20). A camp with no
    standing Great Hall has none. A disabled hall or one needing repair still counts.
  - Working caps per profession follow the hall the same way, plus `per-stage-of` for each stage of a standing
    structure (Builders get +1 per Workshop stage). A profession with no entry has no working cap.
  - Settlers gather at the Great Hall's `settler_home` point. Farmers work the middle of the first `farm` cuboid.
    Builders work at their structure's `settler_work` point. Both fall back to just above the structure.
  - A Builder's job is running while it is on the crew and the job is neither finished nor held.
  - Permissions are `CampPermissions` per rank (`camps.yml` `permissions.settlers`). The leader may do everything and
    allies nothing. Clicking a settler opens its card.
  - The look is `default`, overridden by the profession's (`none` for no profession), overridden by its rarity's. A
    look whose model or skin is not installed falls back to `default`.
- `CampProfessions`: Builder (Construction, trades Mason, Carpenter, Smith, Laborer) and Farmer (works at `farm`).
- `CampTraits`: who rolls each trait. Builder traits roll on Builders, resident traits on Farmers, camp-wide traits,
  Loyal and Content on anyone, Prodigy and Homesick on Builders and Farmers.
- `CampBuilders`: what a Builder brings. Its rarity's Workforce, Speed and efficiency, its trade's Workforce, and the
  trade's specialty on a job whose cost is mostly its resource (a tie is none). Builder traits add on top. The good
  part of a trait is times its trait strength, a trade-off's cost never is. Only the strongest Foreman speeds the
  others. `refund` hands back the best Frugal's share, plus the best Patcher's on a repair, when the crew finishes.
- `CampMorale`: the `MoraleModel`. The best food (a `FoodSource`, raised by the best Cook, up to `food-max`), the best
  Bard and every `MoraleBoost` add. Strikes anywhere, idle professionals past the grace time and fading dismissals take
  away. Beloved bounds idle time and dismissals together, Moody doubles the total, Content floors it, Homesick costs a
  little and Loyal never leaves.
- `CampWideTraits`: reads camp-wide traits. Only the strongest holder counts, at its trait strength.
- `CampWageFund`: the wage fund on the camp record, never below 0. `WageFundPaidEvent` fires when a member pays in.
  Only Builders are paid under both shipped wage models.
- `FarmWorkplace` and `FarmBonusListener`: each working Farmer adds growth and extra-drop shares, scaled by its stats,
  traits and morale and capped for the farm. A crop on the farm grows a stage per whole 100% and one more by chance,
  and a ripe harvest may drop one more of its first drop.
- `LookoutWatch`: with a Lookout in the roster, a non-member arriving in the camp world warns online members, once per
  visitor per camp every 5 minutes.
- `StarterCrew`: the first time the world opens with a standing Great Hall, the camp gets `starting-settlers` (two
  common Builders) and is marked. An unregistered profession there gives none and leaves it unmarked.
- `CrewNotices`: members in the camp are told when a job is placed or pauses waiting for a crew, with its threshold.
- `SettlerModels`: dresses NPCs that look like settlers without being on the roster, such as the Steward and Dock
  candidates.
- `recruit/`: `CampRecruitment` settles each minute. Boats land at a working Dock every `arrivals.every-hours`, and
  their candidates wait `wait-hours`. Milestone settlers wait at the Dock with no limit. The Steward's hiring board
  rolls again every `refresh-hours` or for a fee. Hiring checks the Hire permission and room, then takes the price
  after Haggler through `CampCoins`. `DockArrivals` stands candidates in a ring around the `settler_arrival` point,
  and only members can open their card. Events are `SettlerBoatEvent` and `SettlerHiredEvent`.
- `prosperity/`: `CampProsperity` is the sum of each settler's rarity value (`prosperity.values`), times 1 + average
  morale / 200, times 1 + the best Chronicler. `factors` breaks it down. It is written to the `ProsperityStore`
  (`DatabaseProsperityStore`, table `camp_prosperity`) every 10 minutes by the server holding the world, and deleted
  when the clan disbands. `ProsperityStanding` is a stored value with its daily snapshot. `ProsperityLeaderboard`
  ranks the top 10 from the store every 10 minutes, so unloaded camps rank too.
- `menu/`: `SettlerCards` opens a settler's `SettlerCardMenu` (identity, profession and wage, morale, work, traits) and
  a candidate's `CandidateMenu` (Hire, Reject). Farmers are sent to and taken off the farm there. Builders open their
  crew and are taken off it there. Dismiss needs a shift-click. `CrewMenus` opens `CrewJobsMenu` (every unfinished
  job) and `CrewMenu` (the crew, free Builders to add, Workforce against threshold, speed), only inside the camp.
  `SettlerItems` and `SettlerTags` are the shared items and tag glyphs. Every button checks the rank's action and
  shows gray with the not-allowed line without it.
- `command/`: `/settler list|grant|dismiss <clan>` for staff (admin by default). `grant` rolls through core's
  `SettlerGrants`. `dismiss` matches an id prefix and removes as a dismissal, even off a running job.

Design and phased plan in Outline under **Engineering**.
