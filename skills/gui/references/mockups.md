# Mockups

Mockups live on a Claude Design canvas, one per screen, titled `GUI: <screen>`. Start it with `Artifact` quickstart
(intent `design`), then follow the Design type's instructions. Link the theme's Design System so its tokens show in
the Theme menu. Record the canvas URL in `docs/ui-theme.md` under Screens.

## Scale

Draw in Minecraft GUI pixels at GUI scale 3, so 1 GUI px is 3 CSS px.

- Screen artboard: 1920x1080 (640x360 GUI px). Fill the backdrop with a blurred, darkened game scene placeholder, the
  way a dialog or menu sees the world behind it.
- Vanilla chest: 176 GUI px wide, slots 18 GUI px apart with a 16 px item, slot 0 inner corner at (8, 18), title at
  (8, 6). Rows: 6-row chest is 222 GUI px tall.
- Snap everything to whole GUI px. Borders and bevels are 1 or 2 GUI px, never a fraction.
- Add a second artboard at GUI scale 2 (1 GUI px = 2 CSS px) for the hi-fi, since many players run it.
- Dialog wireframes: draw the real dialog frame from `dialogs.md`: the 33 px header with the title, the body
  starting at y 63, the 33 px footer with the exit button, the blur behind. Name the screen-file element each part
  becomes and mark every click target. Check the layout fits 640x360 (GUI scale 3 at 1080p): header 33, footer 33, body at y 47 for a 280 px canvas.
- Dialog hi-fi mockups are not drawn by hand: the screen file is written and `build_gui.py --previews` renders it with
  the real art and font (`docs/core-gui-screens.md`).

## Wireframes

- Greys only, one accent at most to mark the primary action. Real labels and real data at the largest realistic size
  (the longest name, a full list, the highest number).
- Each alternative is its own artboard, named for its idea ("Tabs left, hero centre", "Single list"), not "Option A".
- Note on the canvas, as a sticky, what each layout gives up.

## Hi-fi

- Tokens from the theme's Design System, nothing invented. New tokens go back into the system at step 8.
- Textures: upload the real pack PNGs as assets and draw them with `image-rendering: pixelated` at whole multiples.
  New art that does not exist yet is drawn with CSS at GUI px precision so it can be rebuilt as a texture.
- Font: the theme's font from the Design System (`fonts/`), loaded with `@font-face` from an asset upload, at 8 CSS px
  per GUI scale step (24px at scale 3). It is built from the pack's bitmap font with
  `Resourcepack/tools/gui/bitmap2ttf.py`. Rebuild and re-upload it when the pack font changes.
- Item icons: real item renders where the pack has them, otherwise a labelled 16x16 placeholder.
- Draw hover, pressed, disabled and selected states for every control type on screen.

## Review

The user comments on artboards. Before each revision, read the comments with the `ArtifactComments` tool, answer each
in its thread, and resolve the ones you addressed. Summarise what changed in one line per artboard.
