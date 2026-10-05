# Full-screen dialogs

How a server dialog becomes a fully custom screen, from the 1.21.11 client source. Build screens as screen files
(`docs/core-gui-screens.md`), which apply everything below through the dialog canvas library (`docs/core-dialogs.md`). The raw research, with
sources and confidence tags, is in `research/`. Nothing here changes in 26.3 or 26.4 snapshot 2: the dialog codecs,
layout and sprites are identical there.

## The screen, as the client builds it

All sizes are GUI px. The screen is `window / GUI scale` px, so 1920x1080 is 960x540 at scale 2, 640x360 at scale 3 and
480x270 at scale 4. Scale 4 is what "Auto" picks at 1080p, so it is the smallest common case.

- **Header**, 33 px: the title and the 20x20 warning button 10 px to its right, centred together. The title is never
  wrapped or clipped and is not clickable. Its hover events work.
- **Body**: bodies, then inputs, then (for `multi_action`) the button grid, stacked with 10 px gaps and centred. It
  starts at `y = min(63, height - footer - bodyHeight)` and scrolls if too tall. **Everything in the body is clipped to
  the scroll rectangle**, which is exactly the content height and content width + 20 when it does not scroll.
- **Footer**, 33 px, bottom: notice and confirmation buttons in a row 8 px apart, or the list `exit_action`. Not
  clipped.
- Background: the player's menu blur, then `textures/gui/inworld_menu_background.png` tiled. Both are shared with every
  in-world menu.
- Wider than the screen: starts at x=0 and runs off the right edge. No horizontal scroll.
- Re-sending a dialog builds a new screen: scroll to top, inputs back to `initial`, focus cleared. The mouse stays put.
  Window resizes keep state.

## Building blocks

### Title: the backdrop

The only place art is never clipped. Build the backdrop from zero-advance glyph strips (`.split`, 256 px atlas cap)
with `shadow_color: 0`, positioned with the space font and `ascent`. It anchors top-centre, so art that should fill the
screen hangs down from the header. Not interactive.

### A wide `plain_message`: the interactive canvas

The free-positioning tool. One `plain_message` as wide as the layout acts as a canvas:

- Lines are a fixed 9 px apart whatever the font. Text wraps at `width - 8`. Height is `9 * lines + 8`. **Each line is
  centred on its own width**, so a left-aligned layout pads every line to the full width.
- Glyphs draw outside their line (large `ascent`, `height`, negative space) but are clipped to the body scroll
  rectangle. Pad with blank lines above and below so art on the first or last line is not cut.
- **Every text segment can carry its own `click_event` and `hover_event`.** The hit area is each glyph's drawn
  rectangle (ascent and height honoured), and for space glyphs an advance-wide, 9 px strip. The mouse must also be inside
  the `plain_message` box, so art drawn outside the box is not interactive.
- Clicks use any action (`custom` for the server, `show_dialog`, `run_command`) and follow `after_action`.
- Side tabs, cards, invite slots and similar are glyph segments placed with negative space, each with its own click.
- Size the canvas to fit the smallest target screen, or it scrolls (see Scale below).
- Gotcha: a `plain_message` is focusable. Clicking non-clickable text in it draws a white 1 px outline around the whole
  box, and no pack can restyle it. Re-sending the dialog after each click clears it.

### Native buttons

- 20 px tall, width 1 to 1024 (default 150). Hitbox is the button rectangle.
- A label whose net width fits in `width - 4` draws centred and unclipped, so a zero-advance glyph label can be art
  larger than the button. Labels ignore their own click and hover events.
- `tooltip` takes any text, shows on hover with no delay, wraps at 170 px.
- Placement: footer (notice, confirmation, list exit) or the `multi_action` grid in the body (`columns`, 2 px gaps,
  each column as wide as its widest button, a short last row centred). No free placement.
- Sprites `widget/button`, `button_highlighted`, `button_disabled` are shared with every vanilla button in the game. A
  pack can restyle them to the theme, or make them transparent so the label art is the button, but either changes all
  buttons everywhere. Per-button looks only come from the label.

### Item body

Always a 16x16 item at the box's top-left, with count, durability and cooldown. Hover shows its tooltip with the item's
`tooltip_style`. Clicking plays the click sound and draws the white outline. Models marked `oversized_in_gui` can draw
larger.

### Inputs

`text`, `boolean`, `single_option`, `number_range`, using the shared `widget/text_field`, checkbox, slider and scroller
sprites. Values come back on the action that submits them. Re-sending loses typed values unless the server sends them
back as `initial`.

## Hover feedback

There is no hover event to the server. What exists:

- Native buttons switch to `button_highlighted` (global sprite).
- `hover_event` tooltips on text segments and the title, `tooltip` on buttons. A tooltip can be glyph art.
- From 1.21.9 the cursor turns into a hand over clickable segments.
- Hover art pinned over an element: the hover tooltip is an item with an invisible `tooltip_style` whose name is the
  art, and the pack's text shader moves it from the mouse onto the element using screen coordinates stored in its
  corner pixels. Screen files do this with `"hover": "<hover style>"`. Each spot needs its own generated glyph.

## The warning button

It always shows and no dialog field hides it. A pack can make it invisible:

- Transparent 20x20 PNGs for `textures/gui/sprites/dialog/warning_button.png`, `_highlighted` and `_disabled`. Only
  dialogs use these.
- `"menu.custom_screen_info.tooltip": ""` in the pack's lang files to drop its tooltip.

It stays an invisible 20x20 click target that opens the disconnect prompt, and it is first in Tab order. It sits 10 px
right of the title. If that is off screen it moves to `(width - 40, 5)`. Control where it lands through the title's net
width so it falls over a dead area of the art.

## Scale

Art is in GUI px, and the screen in GUI px changes with GUI scale. Two options, decide per theme:

- **Design for 480x270** (scale 4 at 1080p): header 33 + footer 33 leaves about 174 px of body. Larger screens show the
  same layout centred with more backdrop around it.
- **Shader scaling**: a colour signature on the art glyphs that `rendertype_text` scales and anchors to `ScreenSize`,
  like the HUD trick. Shaders move pixels, never hitboxes, so only the non-interactive backdrop can scale this way.
  The current shader gate (`guiY < 120`) does not cover dialogs, so art needs its own signature.

## Live data

Re-send the dialog. Use `after_action: none` only when nothing on screen changes, and `wait_for_response` when the
server needs time (it shows "Waiting for Server").

## Versions and the pack

- `pack.mcmeta` says `pack_format` 81, which is a 26.1 snapshot format. Paper 1.21.11 is 75.
- 26.2 replaced `rendertype_text*` with `core/text` and `core/text_background`. Our HUD shader stops applying there.
  Ship per-version overlays before migrating.
- The 256 px glyph cap is vanilla. ImmediatelyFast raises it only for players who have that mod.

## Spike checklist

Prove these on ClansTest-1 with a throwaway staff command before a design depends on them, and move each answer into
the sections above:

1. Title backdrop from split strips at GUI scale 2, 3 and 4.
2. A full-width `plain_message` canvas with clickable glyph segments at known positions, and the hit areas lining up
   with the art.
3. Transparent warning button sprites and the empty tooltip key.
4. Button labels as zero-advance glyph art, with the restyled button sprites.
5. Re-send speed on a click (any flicker).
