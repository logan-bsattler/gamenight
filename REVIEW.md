# Game Night — review handoff (4 Sep 2026)

Findings from a full read of `index.html` plus browser verification. Written so
a fresh session can act on it without the original conversation. Line numbers
are as of commit `fe1a940`; grep for the quoted code if they've drifted.

**Context you need:**
- Single-file app: `index.html` (CSS → markup → `GAMES` data at 351–497 →
  `VIBES` block at 498 → JS from 499). 143 games. No build step for the UI.
- `vibes/build_vibes.py` regenerates only the `VIBES:START`/`VIBES:END` block.
  Nothing below touches it — do **not** rebuild.
- Live at https://logan-bsattler.github.io/gamenight/ (GitHub Pages off
  `main`). `main` is 1 commit ahead of `origin` — push when you commit.
- Style: dense, comment-light, single-letter idioms (`$`, `S`, `g`). Match it.
- Verify visually: open the file in the in-app browser, run
  `S.vibe.cozy=70; render();` in the console to activate the vibe UI, and
  `$("#vtoggle").click()` to open the vibe panel. Test both themes
  (`document.documentElement.dataset.theme="light"|"dark"`) and the mobile
  preset (375px).

---

## Part 1 — Bugs (all reproduced in the browser)

> **DONE** — commit `998580a`. All eight fixed and verified in the browser.
> One deviation: #2 was fixed by stacking the two badges in a `.botleft`
> flex column rather than dropping the teach flag, which would have removed
> it from all 124 video games whenever a vibe was set. #8 also took the
> optional top-10 ranking, via a shared `rankByFit()` / `axesSet()`.

### 1. Vibe sliders are destroyed mid-drag
`index.html:867` — the `#vibe` `input` handler calls `render()`, which calls
`renderVibe()` (line 635), which replaces `#vibe`'s innerHTML. The range input
being dragged is removed from the DOM on the first `input` event, so the user
has to re-grab it every 5 points.

**Fix:** on slider input, set `S.vibe[a]`, update the sibling `.vval` text in
place, and call a render path that skips `renderVibe()`. Simplest: split
`render()` (line 753) so the grid + tonight + count part is callable without
`renderQuick(); renderVibe();`. Keep the `click` handler (`vtog`/`vp`/`vt`/
`vreset`) calling the full `render()` — those change panel structure.

**Verify:** `const b=$('[data-vslide="cozy"]'); b.dispatchEvent(new Event('input',{bubbles:true})); document.contains(b)` → must be `true`.

### 2. Two card badges overlap at bottom-left
`.vbadge` (line 224, `left:7px;bottom:7px`, "▶ teach") and `.mscore`
(line 152, `left:8px;bottom:8px`, "82% fit") share a corner. Whenever any vibe
axis is set, every game with a video shows both pills on top of each other.
Measured: bounding boxes intersect.

**Fix (preferred):** in the card template inside `render()`, compute the match
score first and render `.vbadge` only when the score is `null`. The sheet still
shows the video. Alternative: move `.mscore` to `bottom:32px`.

### 3. Header overflows horizontally on phones
At 375px the document is 421px wide (46px of sideways scroll). `.search`
(line 86) is `flex:1` but keeps the default `min-width:auto`, so the input's
intrinsic width (~462px of placeholder) beats the four 38px icon buttons.

**Fix:** add `min-width:0` to `.search`.
**Verify:** at mobile preset, `document.documentElement.scrollWidth === 375`.

### 4. Weight label vs weight filter disagree
`wLabel` (line 506): `<2 Light, <2.75 Light-med, <3.5 Medium, <4.25 Med-heavy, else Heavy`.
Filter (line 547–549): `light <2.5, medium 2.5–3.5, heavy ≥3.5`.
16 games at 2.50–2.74 (Above and Below 2.51, Boblin's Rebellion 2.5, Clash of
Magic Schools 2.67, Dead Men Tell No Tales 2.56, …) are labelled "Light-med"
on the card but excluded by the *Light* filter.

**Fix:** make the filter bands match `wLabel`: light `<2.75`, medium
`2.75–3.5`, heavy `≥3.5`. (Or expose all five bands as filter options — the
`W_OPTS` array at ~line 526 drives the buttons.) Pick one; the first is the
smaller change.

### 5. "Best at" never renders — reads a field that doesn't exist
`openGame` (line 791 and 798) reads `g.best`. **Zero** of the 143 `GAMES`
records have a `best` field. The player-count poll lives in
`VIBES[id].bestP` (137 games have it) and is already used by `renderTonight`.

**Fix:** replace both `g.best` uses with `(vibeOf(g)||{}).bestP`. Then
`renderTonight`'s `.bestbar` and the sheet agree on the same source.

### 6. Hardcoded "143 games"
`index.html:720` in `vibeSection`: `across your 143 games`. Use
`${GAMES.length}` (the header count already does).

### 7. "Least played" sort is meaningless with this data
`SORTS` → `plays` comparator (line 563). Only **4** games have `plays > 0`;
the other 139 tie at 0 and fall through to the rating tiebreak. The user sees
"Least played" and gets "Top rated with four games at the bottom".

**Fix:** remove the `plays` entry from `SORTS` and the comparator. (If the
owner wants it back, they need to log plays on BGG first — see Part 4 #3.)

### 8. Dice ignores the vibe filters
`index.html:883`: `GAMES.filter(matches)`. With "4 players, ≤1 hr" set in the
vibe panel, the dice can still pick a 3-hour game.

**Fix:** `GAMES.filter(matches).filter(vibeEligible)`. Optionally, if any
vibe axis is set, pick from the top 5 by `matchScore` instead of uniformly.

---

## Part 2 — Small unfinished-looking things

> **DONE** — commit `1a98abe`, except the two items marked below.

- **`UPDATED` is never displayed** (line 350). Show it — e.g. as a `title` on
  the `#count` span, or a muted line under the grid. It answers "how fresh?".
- **Thumbnails are soft on 2× phones** — **NOT DONE, the suggested fix does
  not work.** These URLs are signed (`…=/fit-in/246x300/…`) and the signature
  covers the transform: `500x500` and `400x400` both return **400**, as do
  the unsigned `__original` / `__imagepage` / `__medium` / `__large` preset
  paths. Verified with curl. Sharper art needs a fresh BGG pull that stores
  the API's larger `image` field alongside `thumbnail` — a data change for
  the refresh step, not a presentation one. `vibes/bgg-cache.json` holds no
  image URLs at all today.
- **Keyboard/a11y for the sheet:** no `Escape` handler; focus stays on the
  grid behind the sheet. Add `keydown` Escape → `history.back()` when open,
  and `$("#close").focus()` at the end of `openGame`. Add `aria-pressed` to
  `.chip`/`.opt` toggles (they're buttons with an `.on` class — mirror it).
- **Unescaped strings into `innerHTML`:** `name`, `desc`, `note`, `vtitle`
  (8 `vtitle`s contain a bare `&`). Works today because the data is
  self-authored. Add a 3-line `esc()` helper and use it in `openGame` and the
  card template so the next BGG refresh can't break the page on a `<`.
- **Theme toggle can't return to "follow OS"** once tapped — **STILL NOT
  DONE.** A three-state cycle behind one two-icon button is a design decision
  (which icon means auto?), not a bug fix. Part 3 did not touch it either.
- **Stray history entry:** `openGame` pushes state (line 831); reloading with
  the sheet open leaves an entry that Back consumes invisibly. On load,
  `history.replaceState(null,"")`.
- **`norm()` / `sortName` (line 502–504)** have the combining-mark range as
  raw invisible characters (U+0300–U+036F written literally). Replace with
  `[\u0300-\u036f]` — same regex, survives editors.
- **`.gitattributes`:** git warns "LF will be replaced by CRLF" every commit.
  Add `* text=auto eol=lf`.

---

## Part 3 — Look & feel (needs a design pass, not just fixes)

> **DONE** — commit `f5cdf89`. All six items. Icons are generated by
> `tools/make_icons.py` (needs Pillow) from the header's die glyph; rerun it
> after any palette change. The service worker is verified live on Pages:
> registered, activated, shell cached. Two notes: #5 also made the winner's
> title and the runners-up open their sheets, and the pass exposed a badge
> collision on 375px cards that the same commit fixes by laying the
> thumbnail's bottom out as a flex row instead of absolute corners.

Dark theme is good. Light theme is flat: white cards on `#f4f6f8` with a
hairline border. Suggestions, in order of payoff:

1. **PWA shell.** `apple-mobile-web-app-capable` is set (line 7) but there is
   no `manifest.json`, no icon, no favicon — tab shows a globe, Android
   "add to home screen" gets a generic tile. Add `manifest.json` + one 512px
   PNG icon (a die or meeple on the `--acc` teal works) + `<link rel=icon>`.
   A minimal service worker caching `index.html` makes the shell load offline
   (BGG images won't, and that's fine).
2. **Meta description + Open Graph** (`og:title`, `og:description`,
   `og:image` → the icon) so a texted link unfurls.
3. **Light-theme card lift:** a soft shadow, e.g.
   `box-shadow:0 1px 2px rgba(15,23,32,.06),0 4px 12px rgba(15,23,32,.05)`
   under `:root[data-theme="light"]` / the light media block.
4. **Image placeholder:** cards are a blank `--bg2` box until the CDN answers.
   The game's first letter centred in `--dimmer`, or a shimmer, reads as
   intentional.
5. **Tonight panel shows only #1.** A top-3 row (name + fit %) under the
   winner makes the match feel less arbitrary. `renderTonight` receives the
   whole sorted `list`; `list.slice(1,3)` is right there.
6. **One display face** for `h1`/`h2` (Inter or Instrument Sans via
   `fonts.googleapis.com`) with the system stack as fallback.

---

## Part 4 — Features (each is its own commit; discuss scope with the owner)

> **DONE** — items 1-5, one commit each: `b13ad83` (URL state), `13a054c`
> (search), `82b500f` (plays), `b038209` (presets), and the compare radar.
> Item 6 is still the owner's to do. Two things worth knowing: presets are
> built on the hash from item 1, so recalling one and opening a shared link
> are the same code path; and plays are localStorage, so they do not follow
> you between devices -- the UI says so.

1. **Filter state in the URL hash.** Reload loses everything. Serialise `S`
   (only non-default keys) into `location.hash` on every render; parse on
   load. Makes "here's what fits tonight" a shareable link.
2. **Search across `mech` and `cat`**, not just `name` (`matches`, line 544).
3. **"We played this"** button on the sheet — log a play locally
   (localStorage, keyed by id, with a date). This is the data the app can't
   get from BGG and the one thing a game night produces. It would make
   "Least played" real again and build the hand-scoring pool that
   `vibes/README.md` says validation still needs.
4. **Named presets** ("Tuesday crowd", "with the kids") — snapshot of the
   vibe panel state saved to localStorage.
5. **Compare two games** on one radar. `radar(g,size)` returns an SVG string;
   overlaying a second polygon is straightforward now that the ring exists.
6. **Finish vibe validation.** (`vibes/bgg-cache.json` also carries a `best`
   field per game, identical to `VIBES[id].bestP` — worth knowing if the
   player-count poll is ever needed outside the VIBES block.)
    `vibes/vibes-manual.json` is `{}`, so
   `LOW_CONF` (line ~597) is empty and the low-confidence caveat never shows.
   This is the owner's job (hand-scoring), not code — but flag it.

---

## Part 5 — Hygiene

> **DONE.** `README.md` and `CLAUDE.md` added. Both were fact-checked against
> the repo: file paths, line numbers, commit shas, storage keys and every
> documented hash parameter, and the example link was run in a browser (the
> first draft's example combined `two=1` with `p=4` and returned nothing).

- No root `README.md`. `vibes/README.md` is excellent; the project itself
  needs a short one: what it is, the Pages URL, how to refresh the collection
  (the `/refresh-bgg-collection` skill), and the vibes build commands.
- Consider a `CLAUDE.md` with: "don't rebuild VIBES for presentation
  changes", "verify in browser, both themes + mobile", "match the terse
  style".

---

## Verification checklist for the Part 1 commit

Run in the in-app browser after the edits, at desktop and mobile preset,
both themes:

```js
// activate vibe UI
S.vibe.cozy=70; S.vibe.crunchy=40; render(); $("#vtoggle").click();
// #1 slider survives input
const b=$('[data-vslide="cozy"]'); b.dispatchEvent(new Event('input',{bubbles:true})); console.log('slider ok', document.contains(b));
// #2 no card has both badges
console.log('badge ok', ![...document.querySelectorAll('.card')].some(c=>c.querySelector('.vbadge')&&c.querySelector('.mscore')));
// #3 (mobile preset) no sideways scroll
console.log('width ok', document.documentElement.scrollWidth===document.documentElement.clientWidth);
// #5 best-at renders for a game with bestP
openGame(GAMES.find(g=>vibeOf(g)&&vibeOf(g).bestP).id); console.log('best ok', !!document.querySelector('.tag.best'));
```

Then screenshot the tonight panel and one open sheet in each theme.
