# Working in this repo

Read `README.md` first for what the project is and where things live. This file
is only the things that are easy to get wrong.

## Don't rebuild the VIBES block for presentation work

`index.html` has exactly one generated region, between the `VIBES:START` and
`VIBES:END` markers, written by `vibes/build_vibes.py`. Layout, CSS, copy and
JS changes never require a rebuild, and running one anyway puts a large
unrelated diff in the commit. Rebuild only when you have changed the scorer or
`vibes/vibes-manual.json`.

## Verify in a browser, not by reasoning

Nearly every bug found in this repo's review was a geometry or layout problem
that reading the code would not have caught, and several "obvious" fixes turned
out to be wrong when measured. Before claiming something works:

- **Serve it over http**, not `file://`. The preview pane renders local files as
  `data:` URLs, where `history.replaceState` throws and service workers never
  register — so URL state, presets and the offline shell all appear broken or
  appear to work when they don't. Use `.claude/launch.json` (`python -m
  http.server 8123`).
- **Check both themes and both widths.** `data-theme` `light` and `dark`, and
  375px as well as desktop. Three real collisions in this app only appeared at
  375px.
- **Measure, don't eyeball.** `getBoundingClientRect()` in the console finds
  overlaps and clipping that a screenshot at a glance does not. Compare against
  a known-good element rather than an absolute threshold — an SVG `<text>` bbox
  is the em box, so its corners poke past where the glyphs actually are, and a
  strict test flags working layouts.
- **Screenshot in its own call.** A screenshot in the same `browser_batch` as
  the JS that changes the page tends to capture the previous frame.
- **A hash-only navigation does not reload.** Going from `/` to `/#p=4` fires
  `hashchange` and re-runs nothing at load scope. To test load behaviour, change
  the path or query too.

## Style

Dense and comment-light, with single-letter idioms (`$`, `S`, `g`, `v`). Match
it — don't reformat, don't add JSDoc, don't rename for clarity. Comments are
reserved for *why*, especially where a value was chosen by measurement or a
simpler approach was rejected; the existing ones are worth reading before you
add any.

Two things that are load-bearing rather than stylistic:

- **Escape BGG strings.** Everything is built with template literals, which do
  not escape. Any name, description, note, video title, mechanic or theme going
  into `innerHTML` goes through `esc()`. Eight teach-video titles already carry
  a bare `&`.
- **Check a new CSS class name against the stylesheet.** The file is one big
  sheet with no scoping, and a generic name silently inherits. `.vbval alt`
  picked up an unrelated `.alt` chip rule and clipped the numbers it was meant
  to show.

## Environment notes

- `convert` on this machine is the **Windows disk utility**, not ImageMagick.
  Image work uses Pillow via `tools/make_icons.py`.
- Shell heredocs mangle `\uXXXX`: a literal escape in your script body can
  arrive as the character it denotes. Assemble the backslash at runtime
  (`chr(92)`) or use the Edit tool. `norm()` and `sortName()` were fixed for
  exactly this and can regress the same way.
- BGG cover-art URLs are signed. You cannot edit `fit-in/246x300` to a bigger
  size — every variant 400s.
