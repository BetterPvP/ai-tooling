# UI style

How player-facing text reads and how it is presented in chat and in menus. Other locales translate from the English and keep the same shape.

## Text

### Voice

- Plain game text. Say what happened or what something does.
- Themed wording stays in names only: structure stages (Longhouse, Hall, Keep), upgrade names (Surveyor's table, Great bell), NPC titles (Steward), trait names, and anything an NPC says out loud.
- Settlers are units the player manages. No "they wait", "new faces", "take them on".
- Name the subject. No "It" or "They" that points at nothing.
- No contractions anywhere. "cannot", "do not", "is not".
- No exclamation marks.

### Shape

- One idea per message. Two sentences where the second continues the first read wrong ("People arrived. They are waiting on your message."). Join them into one sentence or pick one of the reason treatments below.
- A reason can be dropped when the player can guess it, put on its own line as `Reason: X`, or moved into a hover behind the `?` hint.
- No colons or other separators (`·`, `-`) inside a sentence ("Construction started: Workshop"). Write "Started building the Workshop."

### By place

| Place | Rule | Example |
| --- | --- | --- |
| Error | Prefer "You cannot...". Drop the subject only when "You cannot" is awkward. Ends in a period. | `You cannot build outside a build zone.` |
| Confirmation | Past tense, subject first. Ends in a period. | `You hired Aldric.` `The Workshop was demolished.` |
| Alert | Flat and informative. What happened, nothing more. | `Settlers arrived at the Dock.` |
| Unavailable upgrade | "Requires an active X." | `Requires an active Job board.` |
| Menu lore | A sentence gets a period. A fragment or label does not. States the effect with real numbers. | `Members respawn here and pick their class.` |
| Button | Verb name, `Click to...` lore. | `Move` / `Click to get a move plan` |
| Warning lore | The mechanic, with numbers. | `Every settler loses 10 morale, fading over 2d.` |
| Upgrade description | Effect only. | `Laborers count as every specialty.` |
| Settler history | Factual, one clause. | `Arrived by boat.` `Rescued from {0}.` |
| Trait description | Mechanical. | `Workplace bonus +20%` |
| Structure label | A short state in title case, a time left in brackets. | `Building (2m 10s)` `Waiting on Crew` |

### Values

- Bounded values use `X/Y`: `200/500`, `Workforce: 3/5`, `Settlers: 12/20`.
- Percentages and multipliers as numbers: `+10%`, `1.5x`. Not "half" or "a while".
- Coins show as the number and the coin icon, never the word: `Wage: 300 (coin) per hour`, `Cost: 250 (coin)`. Rates read "per hour", not "an hour".

### Color

Every message has a base color from its kind. Highlighted parts, such as names and numbers, take a second color.

| Kind | Base | Highlight | Example |
| --- | --- | --- | --- |
| Success | Green | White | `Started building the` **`Workshop`** |
| Error, warning or alert | Red | Yellow. White for the part that matters most | `The` **`Workshop`** `needs` **`2`** `Workforce to continue.` |
| Notice | Yellow | White | `Settlers arrived at the Dock.` |
| Neutral | Gray | White | `Hourly cost:` **`300`** |

### Tags

Rarities and professions show as tag glyphs from the `betterpvp:tags` font in menu lore, not as words: `COMMON`, `UNCOMMON`, `RARE`, `LEGENDARY`, `BUILDER`, `FARMER`, `MASON`, `CARPENTER`, `SMITH`, `LABORER`. A display name keeps the word when the tag would replace the whole name. Chat keeps words.

## Channels

Every message picks the one channel that fits how long it matters and how often it changes. Always look for the balance between the four. Too much in chat buries what matters, and too much on screen gets in the way of play.

| Channel | Use it for | Avoid |
| --- | --- | --- |
| Chat | Things the player may want to read again: feedback on an action, alerts, tips, system messages | Anything that repeats every tick or while an action continues |
| Action bar | Live state while the player is doing something: placement details, a refusal during a held action, a short countdown | Anything the player must not miss, since it fades |
| Title and subtitle | Rare, big moments: entering a mode, discovering a place, a finished milestone. The subtitle carries the detail | Errors, anything frequent, anything long |
| Boss bar | State that lasts: a timer, progress over time, a status the player keeps an eye on | One-off events |

- One channel per event. Never send the same message to two channels.
- If an event can fire many times in a row, it belongs in the action bar or a boss bar, never chat.
- A title interrupts. Save it for moments that deserve it.

## Chat

### Message kinds

| Kind | When | Prefix | Leading icon | Blank lines |
| --- | --- | --- | --- | --- |
| System | Staff commands, command usage and errors, server and moderation state | Blue `Name> ` | None | None |
| Feedback | The result of something the player just did: a menu click, a blueprint, a deposit | None. Green when done, red when refused | None | None |
| Alert | Something happened in the player's clan or camp that they did not cause | None | `bell` for news, `exclamation_mark` for problems | None |
| Tip | Tutorial nudges and first-time hints | None | `info` | One above and one below |
| Summary | A block of related lines sent together, such as camp arrival notices | None | Per line, by severity | One above and one below the block |

The blue prefix is only for definitive system messages. Everything a player sees during normal play goes without it. Leading icons are `ChatIcon` sprites on the vanilla `gui` atlas, from `assets/betterpvp/textures/gui/sprites/icon/chat/`. That atlas loads every `gui/sprites` folder without an atlas file, so pack mergers cannot drop it. Do not draw chat icons from the `blocks` atlas.

```
System     Settlers> Added Aldric to Samito's camp.
Feedback   Deposited 64 Wood (200/500).
Alert      [bell] Settlers arrived at the Dock.
           [!] 3 settlers went on strike. ?
Tip
           [i] Crops grow faster with Farmers assigned.
               Assign them at the Steward. ≡

```

### Hint icons

`ChatHint` (core `utilities/model`) appends an icon from the `betterpvp:input/chat` font, drawn without a shadow. One icon per message, at the end.

| Icon | Glyph | Means | Behaviour |
| --- | --- | --- | --- |
| `?` keycap | `U+E0A4` | Why, the explanation | Hover shows the reason or rule |
| `...` pill | `U+E301` | There is more of this | Hover shows the cut part, a long list or full numbers |
| `≡` | `U+E269` | Open or choose | Click leads to a menu, a choice or an expanded view |

If the extra detail explains the message, use `?`. If it continues the message, use `...`. If the player can act on it, use `≡`.

## Lore

- No `frameLore`. No divider lines or padding lines around lore.
- Additional tooltips are always hidden. `ItemView` hides them by default.
- Order: description, a blank line, the fields, a blank line, then the click line. A warning sits right above the click line.
- Short by default. Most items carry a name, one line of description and the click line. Full detail only on items the player decides from, such as a structure to build, a candidate to hire or an upgrade to fit.
- A lore item with several fields uses `Field: value` lines. When the value would be the only lore, put both in the name instead, as `Morale: 12`.

```
Workshop
Unlocks advanced structures and speeds up construction.

Cost: 200 Wood, 100 Stone
Build time: 2h
Requires the Great Hall at stage 2

[click] Get a blueprint
```
