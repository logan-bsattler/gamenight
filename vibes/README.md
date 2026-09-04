# Vibe scorer

Eight axes — cozy, chatty, silly, cutthroat, tense, crunchy, swingy, storied — scored 0–100 for
every owned game from BGG data, hand-correctable, and used for a "what fits
tonight" match score. Implements `vibe-scorer-spec.md`.

## Pipeline

```bash
python vibes/vibe_scorer.py --report   # bgg-cache.json -> vibes-auto.json
python vibes/build_vibes.py            # + vibes-manual.json -> VIBES block in index.html
python vibes/validate_vibes.py         # spec section 5, needs hand scores first
```

`build_vibes.py` is idempotent — it rewrites the block between the
`VIBES:START` / `VIBES:END` markers, so re-running never stacks up copies.

| File | Written by | Safe to delete |
|---|---|---|
| `bgg-cache.json` | the refresh step (see below) | no — it is the scorer's only input |
| `vibes-auto.json` | `vibe_scorer.py` | yes, regenerable |
| `vibes-manual.json` | **you, by hand** | **no** — nothing else can recreate it |

Manual wins per axis. Correcting `cutthroat` alone leaves the other seven on their
auto values, and each axis carries `src: "manual" | "auto"` so the UI can mark
hand-verified games (the radar tints those spoke labels).

## Refreshing the BGG cache

The spec says the scorer pulls from the local `bgg-mcp` server. It does not do
that directly: an MCP server is driven by the agent, not callable from a plain
Python script. So the pull is a separate step — the agent calls `get_games`
(`stats=1`, batched 20 at a time) across the owned ids and writes the trimmed
result to `bgg-cache.json`. Everything downstream is ordinary offline Python.
Re-run it when the collection changes; the fields cached are exactly the ones
the scoring model reads.

## Known gaps against the spec

**`language_dependence` is not implemented.** The bgg-mcp server does not
expose the poll, BGG's XML API now returns `Unauthorized` without credentials,
and `api.geekdo.com` does not carry it either. Chatty loses a ±5 nudge and the
"easy to jump in" filter is not built. Everything else in section 1 is present.

**Eleven spec signals do not match real BGG tags.** `vibe_scorer.py` maps the
near-misses (`Tech Trees` → `Tech Trees / Tech Tracks`, `Dexterity` →
`Action / Dexterity`, `Nature` → `Environmental`, `Social Deduction` →
`Hidden Roles` / `Roles with Asymmetric Information` / `Traitor Game`). Seven
have no BGG equivalent anywhere in the collection and never fire: Engine
Building, Gardening, Word Game, Trivia, Stacking and Balancing, King of the
Hill, Acting. `--report` lists them every run so they stay visible.

**"Direct conflict-y attack mechanics"** in Cutthroat is not a BGG tag. It is
defined in `ALIASES["DirectConflict"]` as BGG's explicitly conflict-oriented
tags. That is the one place the model encodes a judgement call rather than the
spec — adjust the list rather than the weights.

## Base terms on chatty and cutthroat (deviation from the spec)

As specified, chatty and cutthroat were the only axes with **no base term** —
pure additive bonus lists over tags most games do not carry. 60 games (42%)
scored exactly 0 on chatty and 54 (38%) on cutthroat, across only 11 distinct
values each. Percentiles cannot separate ties, so section 3's spread-the-radar
trick failed on exactly those two axes and the match score treated 60 games as
identical on chatty.

Both now get a base, keeping every other signal untouched:

```python
chatty:    50 - wn * 30      # lighter games talk more
cutthroat: 25 + wn * 20      # heavier games give more ways to act against people
```

`wn` is normalised weight, `(averageweight - 1) / 4`, the same input the other
four bases use. The choice of *weight* is the load-bearing part: a base only
breaks ties if it comes from a continuous variable. Player count is the more
intuitive signal for chatty, but it takes about five distinct values across the
collection, so it relocates the pile-up instead of removing it.

| axis | tied at 0 before | after | distinct before | after |
|---|---|---|---|---|
| chatty | 60 (42%) | 0 | 11 | 55 |
| cutthroat | 54 (38%) | 0 | 11 | 45 |

The one tie left is 16 games sharing `cutthroat = 10`. Those are exactly the 16
co-ops, pinned by the spec's own hard rule that a co-op scores ≤ 10 whatever
else it carries. That is the rule working, not a defect.

These constants were chosen to make the axes spread, and were never fitted to
hand scores — there are none yet. Section 5 still applies: once
`vibes-manual.json` is populated, an axis that comes out biased in one
direction should be corrected **by moving its base constant**, which is exactly
what these two now have.

## Crunchy base, renormalised

The spec's `(weight - 1) / 4 * 70` assumes BGG weight uses its full 1-5 range.
No real collection does: here the heaviest game is 4.16 and exactly one clears
4.0, so the top 40% of the scale was dead and a median game (weight 2.06) based
out at 19 — reading as "barely crunchy" on a 0-100 axis. The base now
renormalises over the range that actually occurs:

```python
crunchy: min(1, (w - 1) / 3) * 80
```

Base constant only; no signal weights moved. Median crunchy 21 → 31, distinct
values 56 → 65.

**The residual is a limitation, not a miscalibration.** After the fix, medium
and heavy games line up almost exactly against a hand pass (Viticulture 76 vs
75, Small World 51 vs 50, Above and Below 60 vs 55). Everything still scoring
low is light: Santorini 1.72, Splendor 1.77, Kingdomino 1.24, Sushi Go! 1.16.

That is BGG weight doing what it actually measures — **rules complexity, not
depth of thought**. Santorini teaches in two minutes and is a deep duel; chess
would score light too. Raising the base further would close that gap by
inflating the medium and heavy games that are now correct, and would make Sushi
Go! read as crunchy. If light-but-deep games need to score higher, that wants a
new signal (the abstracts rank is the obvious candidate, currently only +10),
not a bigger base.

## Renamed axes, and two new ones

The axis labels were renamed (cozy kept; social→chatty, playful→silly,
compete→cutthroat, intense→tense, thinky→crunchy) and two axes added:

- **swingy** — how much dice decide it rather than decisions. Orthogonal to
  everything else; a game can be crunchy and swingy at once.
- **storied** — story and theme immersion.

Adding `storied` came with the one **signal** change made to an existing axis
so far: `Storytelling` was removed from chatty's capped group. It was the worst
signal in the model, putting Above and Below — a quiet 2–4p euro with a
storybook — at chatty 100, level with Secret Hitler. Above and Below now reads
chatty 84, storied 100, and the top of chatty is Bohnanza, Secret Hitler and
The Resistance, which is right.

## Validation is not done

Section 5 is the part that decides whether any of this is trustworthy, and it
needs hand scores that only you can produce. `vibes-manual.json` is empty, so
`validate_vibes.py` currently reports nothing to validate.

The order matters: **hand-score before reading `vibes-auto.json`.** Scoring
against numbers you have already seen measures your memory, not the model.

One wrinkle the spec did not anticipate: it assumes ~60 played games to score
against. The collection records **4 games with plays > 0** and 35 with a
personal rating, so "the games he's actually played" cannot be derived from the
data — you will have to pick the set yourself. Thirty-five rated games is a
reasonable starting pool.
