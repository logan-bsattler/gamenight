#!/usr/bin/env python3
"""Inter-rater agreement between vibes-auto.json and vibes-llm-pass.json.

THIS IS NOT SECTION 5 VALIDATION. Both sides come from the same rater working
from the same BGG knowledge, so agreement here says the tag model reproduces
that rater's priors -- nothing about how these games feel at your table. A low
number does not license "trust the auto scores on unplayed games".

What it is genuinely good for: the disagreements. Where even the same rater
parts company with the tag model, the tag model is probably doing something
crude, and those rows are the ones worth your attention first when you fill in
the real worksheet.

Games flagged low_confidence in the llm pass are excluded by default.
"""
import json, os, statistics, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
AXES = ["cozy", "silly", "chatty", "swingy", "cutthroat", "crunchy", "tense", "storied"]

ap = argparse.ArgumentParser()
ap.add_argument("--include-low-confidence", action="store_true")
a = ap.parse_args()

auto = json.load(open(os.path.join(HERE, "vibes-auto.json"), encoding="utf-8"))
llm = json.load(open(os.path.join(HERE, "vibes-llm-pass.json"), encoding="utf-8"))
names = {k: v["name"] for k, v in
         json.load(open(os.path.join(HERE, "bgg-cache.json"), encoding="utf-8")).items()}

meta = llm.pop("_meta", {})
skip = set() if a.include_low_confidence else set(meta.get("low_confidence", []))
rows = {g: v for g, v in llm.items() if g in auto and g not in skip}

print("inter-rater agreement, NOT validation -- see docstring")
print(f"games compared: {len(rows)}"
      + (f"  ({len(skip)} low-confidence excluded)" if skip else "") + "\n")
print(f"{'axis':9}{'MAE':>7}{'bias':>7}{'sd':>7}")
for ax in AXES:
    e = [auto[g][ax] - rows[g][ax] for g in rows if ax in rows[g]]
    print(f"{ax:9}{statistics.mean(abs(x) for x in e):7.1f}"
          f"{statistics.mean(e):+7.1f}{statistics.pstdev(e):7.1f}")

print("\nbiggest disagreements -- look at these first")
flat = sorted(((abs(auto[g][ax] - rows[g][ax]), ax, g) for g in rows for ax in AXES),
              reverse=True)[:12]
for d, ax, g in flat:
    print(f"  {names.get(g, g)[:32]:34}{ax:9}tags {auto[g][ax]:3}  rater {rows[g][ax]:3}"
          f"  ({auto[g][ax] - rows[g][ax]:+d})")
