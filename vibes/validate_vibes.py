#!/usr/bin/env python3
"""Spec section 5 -- does the auto scorer agree with hand scores?

Compares vibes-manual.json against vibes-auto.json and reports mean absolute
error per axis, plus the signed bias, because the two mean different things:

  MAE < 15, low bias        -> trust auto scores on unplayed games
  MAE high, bias one way    -> adjust that axis's BASE CONSTANT only
  MAE high, bias near zero  -> the BGG tags do not carry that axis.
                               Mark it low-confidence in the UI. Do not tune.

Order matters: hand-score in vibes-manual.json BEFORE reading vibes-auto.json.
Scoring against numbers you have already seen measures your memory, not the
model. And per the spec, do not tune weights until MAE is near zero -- that
overfits to the hand-scored subset instead of generalising to the rest.
"""
import json, os, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
AXES = ["cozy", "silly", "chatty", "swingy", "cutthroat", "crunchy", "tense", "storied"]
TARGET = 15

auto = json.load(open(os.path.join(HERE, "vibes-auto.json"), encoding="utf-8"))
manual = json.load(open(os.path.join(HERE, "vibes-manual.json"), encoding="utf-8"))
names = {k: v["name"] for k, v in
         json.load(open(os.path.join(HERE, "bgg-cache.json"), encoding="utf-8")).items()}

pairs = {ax: [(gid, manual[gid][ax], auto[gid][ax])
              for gid in manual if gid in auto and ax in manual[gid]]
         for ax in AXES}

n_games = len({g for ax in AXES for g, _, _ in pairs[ax]})
if not n_games:
    sys.exit("vibes-manual.json has no hand scores yet -- nothing to validate.\n"
             "Score the games you have actually played, then re-run.")

print(f"hand-scored games: {n_games}\n")
print(f"{'axis':9}{'n':>4}{'MAE':>7}{'bias':>7}{'sd':>7}  verdict")
for ax in AXES:
    p = pairs[ax]
    if not p:
        print(f"{ax:9}{0:>4}{'-':>7}{'-':>7}{'-':>7}  no hand scores")
        continue
    errs = [a - m for _, m, a in p]           # signed: auto minus manual
    mae = statistics.mean(abs(e) for e in errs)
    bias = statistics.mean(errs)
    sd = statistics.pstdev(errs) if len(errs) > 1 else 0.0
    if mae < TARGET:
        verdict = "pass -- trust on unplayed"
    elif abs(bias) > 0.6 * mae:
        verdict = f"biased {'high' if bias > 0 else 'low'} -- adjust base only"
    else:
        verdict = "scatter -- mark low-confidence"
    print(f"{ax:9}{len(p):>4}{mae:7.1f}{bias:+7.1f}{sd:7.1f}  {verdict}")

print("\nworst disagreements")
flat = sorted(((abs(a - m), ax, g, m, a) for ax in AXES for g, m, a in pairs[ax]),
              reverse=True)[:10]
for d, ax, g, m, a in flat:
    print(f"  {names.get(g, g)[:38]:40}{ax:9}hand {m:3}  auto {a:3}  ({a - m:+d})")
