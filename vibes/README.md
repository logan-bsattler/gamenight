# Vibe scorer

Six axes — cozy, social, playful, compete, intense, thinky — scored 0–100 for
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

Manual wins per axis. Correcting `compete` alone leaves the other five on their
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
and `api.geekdo.com` does not carry it either. Social loses a ±5 nudge and the
"easy to jump in" filter is not built. Everything else in section 1 is present.

**Eleven spec signals do not match real BGG tags.** `vibe_scorer.py` maps the
near-misses (`Tech Trees` → `Tech Trees / Tech Tracks`, `Dexterity` →
`Action / Dexterity`, `Nature` → `Environmental`, `Social Deduction` →
`Hidden Roles` / `Roles with Asymmetric Information` / `Traitor Game`). Seven
have no BGG equivalent anywhere in the collection and never fire: Engine
Building, Gardening, Word Game, Trivia, Stacking and Balancing, King of the
Hill, Acting. `--report` lists them every run so they stay visible.

**"Direct conflict-y attack mechanics"** in Compete is not a BGG tag. It is
defined in `ALIASES["DirectConflict"]` as BGG's explicitly conflict-oriented
tags. That is the one place the model encodes a judgement call rather than the
spec — adjust the list rather than the weights.

## Base terms on social and compete (deviation from the spec)

As specified, social and compete were the only axes with **no base term** —
pure additive bonus lists over tags most games do not carry. 60 games (42%)
scored exactly 0 on social and 54 (38%) on compete, across only 11 distinct
values each. Percentiles cannot separate ties, so section 3's spread-the-radar
trick failed on exactly those two axes and the match score treated 60 games as
identical on social.

Both now get a base, keeping every other signal untouched:

```python
social:  50 - wn * 30      # lighter games talk more
compete: 25 + wn * 20      # heavier games give more ways to act against people
```

`wn` is normalised weight, `(averageweight - 1) / 4`, the same input the other
four bases use. The choice of *weight* is the load-bearing part: a base only
breaks ties if it comes from a continuous variable. Player count is the more
intuitive signal for social, but it takes about five distinct values across the
collection, so it relocates the pile-up instead of removing it.

| axis | tied at 0 before | after | distinct before | after |
|---|---|---|---|---|
| social | 60 (42%) | 0 | 11 | 55 |
| compete | 54 (38%) | 0 | 11 | 45 |

The one tie left is 16 games sharing `compete = 10`. Those are exactly the 16
co-ops, pinned by the spec's own hard rule that a co-op scores ≤ 10 whatever
else it carries. That is the rule working, not a defect.

These constants were chosen to make the axes spread, and were never fitted to
hand scores — there are none yet. Section 5 still applies: once
`vibes-manual.json` is populated, an axis that comes out biased in one
direction should be corrected **by moving its base constant**, which is exactly
what these two now have.

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
