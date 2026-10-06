# Core: dialog canvas

Status: Draft · Last verified: 2026-10-05, 85eaeca4e

## Purpose

Screens are normally written as definition files on top of this library: see `docs/core-gui-screens.md`. This doc
covers the library underneath.

`core/menu/dialog/` builds full-screen custom screens out of vanilla server dialogs. A feature places art, text and
click regions at any position in GUI pixels, and the library turns that into the dialog title and one body text block.
How the client lays dialogs out, and what it cannot do, is in the `/gui` skill's `references/dialogs.md`.

## Main types

| Type | Role |
| --- | --- |
| `DialogScreen` | One screen: a backdrop canvas, the body canvas, fields, grid buttons, the footer exit button |
| `DialogCanvas` | Absolute layout. `text`, `art` and `place` return a `CanvasElement` that takes a tooltip and a click |
| `DialogField` | Inputs: `Text`, `Toggle`, `Slider`, `Choice` |
| `DialogButton` | A native button. Its label can be glyph art |
| `DialogSessions` | Opens screens, routes clicks, re-renders with typed values kept |
| `DialogCompiler` | Canvas to components, package-private |
| `VerticalOffsets` | Maps a font and a 0 to 8 px shift to its generated copy |

```java
final DialogCanvas canvas = new DialogCanvas(300);
canvas.art(8, 22, '', 64, 18).tooltip(tooltip).onClick((player, inputs) -> select(player, 0));
canvas.text(14, 27, name).onClick((player, inputs) -> select(player, 0));

sessions.open(player, DialogScreen.builder()
        .name(title)
        .backdrop(backdrop)
        .canvas(canvas)
        .exit(DialogButton.builder().label(closeArt).width(40).build())
        .build());
```

`DialogTestCommand` (`/dialogtest`, staff) is a complete example.

## How it works

- **Body.** Each element sits on the 9 px text line that holds its top. The compiler reaches its x with space-font
  advances and shifts it down the rest of the way with a generated font (`betterpvp:rpg/down_N`, `betterpvp:ui/down_N`).
  Lines draw left to right, lower lines over higher ones. The body gets enough lines for the lowest element. The
  client centres every line of a `plain_message`, so each line is padded to the full canvas width.
- **Backdrop.** Compiled into the title with zero net advance and no shadow, so the client draws it from 15 px left of
  the screen centre. The title is never clipped. Backdrop art carries its height in its glyph ascent: the title sits
  54 px above the first body line (measured in game), so art whose top meets the body top has ascent `7 - 54`.
- **Clicks.** Every send gives the screen a new id. Regions and buttons get the custom click key
  `betterpvp:dialog/<id>/<slot>`, and `PlayerCustomClickEvent` routes it to the callback. Keys from an older send are
  ignored. Body text clicks carry no inputs. Native buttons carry every field.
- **Re-render.** `rerender` sends the screen again with the last input values as initial values. Clicks keep the screen
  open (`after_action: none`), and the exit button closes it after its own callback. After any click the screen
  re-renders unless the callback already re-rendered, opened another screen or closed it.
- **Background clicks.** Clicking the body focuses it and the client outlines it in white. The whole body carries a
  background click, so any click re-renders the screen and clears the outline.
- **Tall clickable elements.** The client checks the body line by line and takes the last clickable text under the
  mouse, so blank space on a lower line would steal clicks from an element that starts above it. Space crossing a
  clickable element from an earlier line carries that element's click.
- **Pack.** `Resourcepack/tools/gui/`: `build_gui.py` generates the art screens use (`docs/core-gui-screens.md`),
  `theme_art.py` draws the replaced vanilla button and tooltip sprites and encodes hover glyphs, `offset_fonts.py` writes the shifted fonts. The warning button is hidden by transparent `dialog/warning_button*`
  sprites and an empty `menu.custom_screen_info.tooltip` in every language file.

## Extending it

- New art: declare it in a screen file or `gui/assets/*.json` and let `build_gui.py` generate it. Never hand-place
  glyphs at fixed codepoints.
- A new shiftable font: add it to `VerticalOffsets` and to `FONTS` in `offset_fonts.py`.
- Translated text: render it for the viewer before placing it, or it measures as zero.

## Gotchas

- `art` takes the image size. The advance is one pixel more, which the canvas adds.
- Placement throws when an element does not fit the canvas or uses a font without shifted copies below a line top.
  Long translations can trip the fit check, so leave room.
- Arabic, Chinese, Japanese and Korean come from the vanilla fallback, which cannot be shifted. Text holding them snaps
  to the nearest line top.
- Keep the body above the footer at the smallest target screen (480x270 at GUI scale 4). A taller body moves up and
  stops lining up with the backdrop.
- The white focus outline still flashes for a round trip after a click, until the re-render arrives.
