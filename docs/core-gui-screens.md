# Core: GUI screens

Status: Approved · Last verified: 2026-10-06, 9d6e6bf6b

## Purpose

Full-screen dialog GUIs are written as JSON screen files, or built in Java, and run on the dialog canvas library
(`docs/core-dialogs.md`). The plugin and the pack generator read the same files, so art, hover spots and animations
always match the code. PRD: Outline, "GUI: screen definition files".

## Files

Each plugin keeps its files in `src/main/resources/gui/`:

| Path | Holds | Schema |
| --- | --- | --- |
| `gui/<id>.json` | one screen, opened as `<namespace>:<id>` | `screen.schema.json` |
| `gui/components/*.json` | components shared by the namespace | `components.schema.json` |
| `gui/assets/*.json` | art for screens built in Java | `assets.schema.json` |

The schemas live in `core/src/main/resources/gui/schema/`. `.vscode/settings.json` maps the three folders to them, so
VS Code autocompletes and validates every file. Other editors pick them up from `"$schema"` at the top of a file.
`theme.schema.json` lists the styles, hover styles and sprites the pack can draw. The pack generator rewrites it with
`--schema-out`.

A plugin loads its files once at startup with `guiScreens.load("<namespace>", <PluginClass>.class)`. The namespace
is the module's folder name (`core`, `clans`, `champions`), since the pack generator finds the files by module folder.
Core loads `core`. On `ServerLoadEvent` every screen is checked and problems are logged with the screen and element named.

## A screen

```json
{
  "$schema": "schema/screen.schema.json",
  "canvas": { "width": 300, "height": 120 },
  "name": { "key": "shop.name" },
  "state": { "tab": "items", "items": [], "error": null },
  "actions": ["buy"],
  "backdrop": [ { "box": "panel", "width": 300, "height": 120 } ],
  "elements": [
    { "text": { "key": "shop.name" }, "y": 4, "width": 300, "align": "center", "style": "title" },
    { "column": { "x": 8, "y": 22, "cell": [64, 18], "gap": 5 }, "children": [
      { "button": "tab", "selected_style": "tab_selected", "selected": "{tab == 'items'}", "width": 64, "height": 18,
        "label": { "key": "shop.items" }, "on_click": { "set": { "tab": "items" } } } ] },
    { "switch": "{tab}", "cases": { "items": [
      { "repeat": "items", "max": 4, "layout": { "grid": { "x": 84, "y": 24, "cell": [100, 24], "gap": 4, "columns": 2 } },
        "children": [ { "button": "normal", "width": 100, "height": 24, "label": "{item.name}", "hover": "rim", "pressed": true,
                        "on_click": { "call": "buy", "args": { "id": "{item.id}" } } } ] } ] } },
    { "when": "{error}", "then": [ { "text": "{error}", "x": 84, "y": 100, "style": "error" } ] }
  ],
  "exit": { "label": { "key": "shop.close" }, "width": 80 }
}
```

Positions are GUI pixels from the canvas top-left, or from the cell a layout gives the element. A canvas of up to
460 x 189 fits a 480 x 270 screen (GUI scale 4 at 1080p) without scrolling, with its art drawn as `box` elements, which
move with the canvas. Taller canvases scroll on small screens, and hover art cannot follow a scrolled body. A screen with a
`backdrop` stays within 174 px tall, since backdrop art only lines up while the body starts 63 px down.

A button's `"width": "auto"` is its label's width in the menu font plus `padding` on each side (6 by default) and the
outline. It needs a fixed label (a key without arguments, or literal text). A row with `"cell": ["auto", h]` places
its children one after another, `gap` apart. The plugin and the pack generator resolve these per language, so each
player sees buttons sized to their own language, and the pack holds the art of every language.

## Elements

| Key | Draws | Notes |
| --- | --- | --- |
| `text` | text in a text style | `align` and `width` centre or right-align it |
| `box` | style art at a size | in `backdrop` it draws in the title, behind the canvas |
| `button` | style art with a centred label | `selected`, `selected_style`, `label_style`, `selected_label_style`, `hover`, `selected_hover`, `pressed`, `tooltip`, `on_click` |
| `icon` | a sprite | `frames` and `fps` loop it on the client |
| `row`, `column`, `grid` | children in cells | `cell`, `gap`, `columns` |
| `repeat` | children once per list entry | `max` copies at most, entry bound as `as` (default `item`) and `index` |
| `switch` | the case a binding names | `default` when none matches |
| `when` | `then` or `else` | |
| `use` | a component | `with` binds its params |
| `custom` | a Java element type | `assets` declares the art it may draw |

Fields (`text_field`, `toggle`, `slider`, `choice`) sit below the canvas and write their value into the state key they
name. `buttons` adds vanilla buttons in a grid, and `exit` is the footer button.

## Bindings

`{...}` reads state: names, dotted paths, `list[0]`, literals, `+ - * /` (where `+` joins text), comparisons,
`&& || !`, and formatters such as `{coins | short}` or `{name | default:'Nobody'}`. A text that is exactly one binding
keeps the value's type. Translated text is `{"key": "...", "args": ["{coins}"]}`.

## Actions and results

`on_click` takes a string (calls that named action), an object, or an array (runs in order):

| Action | Does |
| --- | --- |
| `{"set": {"tab": "items"}}` | sets state, re-renders |
| `{"open": "detail", "state": {"id": "{item.id}"}}` | opens a screen on top |
| `{"back": true}` | returns to the screen below |
| `{"close": true}` | closes |
| `{"sound": "minecraft:ui.button.click"}` | plays a sound |
| `{"call": "buy", "args": {"id": "{item.id}"}}` | runs Java |

A Java handler returns an `ActionResult`: `update()` or `update(state -> ...)`, `open(screen, state)`, `back()`,
`close()`, `error(translationKey)` (sets `error` in state and plays the error sound) or `none()`.

## Java

Open a screen with its state and the actions it lists:

```java
screens.open(player, "shop:market", Map.of("items", items), Map.of(
        "buy", context -> {
            if (!economy.charge(context.getPlayer(), price(context.arg("id")))) {
                return ActionResult.error("shop.too_poor");
            }
            return ActionResult.update(state -> state.set("owned", owned(context.getPlayer())));
        }));
```

- Build a screen in code with `ScreenDefinition.builder()` and the `Node` builders, then `screens.register(screen)`.
- Extend a file screen with `screens.definition("shop:market").toBuilder()`, add or replace elements, and open the
  result with `screens.open(player, definition, state, bindings)`.
- `screens.state(player)` and `screens.refresh(player)` change a screen from outside an action.

`GuiRegistry` holds what every screen can use, namespaced by plugin. Bare names look in the screen's namespace, then
in `core`:

```java
registry.action("clans", "invite", handler);
registry.component("clans", "member_row", component);
registry.elementType("clans", "territory_map", new TerritoryMapElement());
registry.textStyle("clans", "ally", text -> text.color(NamedTextColor.AQUA));
registry.sound("clans", "open", "betterpvp:ui.open");
registry.formatter("percent", (value, args) -> ...);
```

An `ElementType` draws through its `RenderContext`: `art(asset, x, y)`, `glyph(asset)`, `text(...)`, `styled(...)`,
`click(action)` and `evaluate(binding)`. It can only draw art its node declared in `assets`.

## Pack generation

The pack must contain every piece of art before anyone opens a screen. The generator reads the screen folders:

```bash
python tools/gui/build_gui.py --screens core=../BetterPvP/core/src/main/resources --schema-out ../BetterPvP/core/src/main/resources/gui/schema/theme.schema.json --previews ../previews
```

- It checks every file against the schemas, then writes glyphs to `textures/font/gui/<namespace>/`, the font
  `betterpvp:gui/<namespace>` and its `down_1..8` copies. All of it is gitignored.
- `pack_processor.py pack` runs it before packing, for every module of the BetterPvP checkout with a
  `src/main/resources/gui/` folder. It asks for the checkout once and keeps it in the pack repo's `.env`
  (`BETTERPVP_DIR`). `--betterpvp <folder>` or `--gui-screens <ns>=<folder>` override that. It does nothing when no
  input changed.
- Art sources live in the pack under `assets/betterpvp/textures/gui/`. Styles are `styles/<name>.png` (nine-slice,
  with `<name>.json` `{"border": 3}` and an optional `<name>.pressed.png`). The theme's styles are `panel`, `panel_header` (a panel with a 22 px header band), `header`,
  `well`, `raised`, `selected`, `normal`, `primary`, `disabled`, `tab`, `tab_selected`, `track` and `fill`, each
  stretched to the size a screen asks for. Hover styles are `hover/<name>.png`: the theme has `light` (a white ring,
  for normal buttons and tabs) and `rim` (a green ring, for primary buttons). Icons are
  `icons/<name>.png`, animated ones with their frames stacked top to bottom. Not `gui/sprites/`, which the game
  stitches into the GUI atlas.
- `python .claude/shared/deploy.py --pack` builds the pack from the current checkout and unpacks it into Nexo's pack
  folder on ClansTest-1 before the restart.
- `--previews` writes a PNG of each screen at GUI scale 3 with English text, for review without logging in.

The plugin and the generator assign glyph codes by the same rule (`ScreenAssets`, `build_gui.py`).
`core/src/test/resources/gui-golden/` holds a fixture and its expected glyphs, and both test suites check it.

## Gotchas

- A position is always a number, so every hover spot is known to the pack. A `repeat` declares `max` for the same
  reason.
- A screen built in Java with art must declare that art in `gui/assets/*.json`. Undeclared art fails validation and
  names the asset.
- After changing a screen's art, rerun the generator and redeploy the pack, or the client shows the wrong glyphs.
- Buttons are at most 254 px wide. Art is at most 256 px tall. Wider boxes split into glyphs automatically.
- Hover art replaces an element's tooltip. Clicks re-render the screen, which clears the focus outline. While a
  button shows its pressed art, its hover art is dropped so the press shows.
- An image inside a panel is an `icon` placed over a `box`. Tabs that show images put both in the tab's `switch` case.
- Arabic, Chinese, Japanese and Korean text snaps to 9 px rows.
- The client draws each 9 px row as one text run and batches its glyphs by texture, so pieces that overlap within one
  row draw in no fixed order. Lower rows draw over higher ones. Anything drawn over a box starts on a later row than
  the box, and backdrop boxes (one run) never overlap. `build_gui.py` fails the pack build on a layout that breaks this.
- Art glyphs draw without the text shadow, so styles look the same in game as in the Design System.
- The body is always as tall as the canvas, so hover art knows where the body sits. The pack's text shader places it
  the way the client lays the dialog out: centred on whole pixels, 63 px down or higher when the body would not fit
  above the footer. Hover spots on screens with inputs or a button grid below the canvas sit too low on small screens.
