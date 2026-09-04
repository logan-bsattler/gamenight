#!/usr/bin/env python3
"""Blind hand-scoring worksheet for spec section 5.

  python score_worksheet.py            # write worksheet.csv (35 rated games)
  python score_worksheet.py --all      # every owned game
  python score_worksheet.py --ingest   # worksheet.csv -> vibes-manual.json

This script never opens vibes-auto.json. That is the entire point: section 5
only means something if the hand scores are set down before the auto scores are
seen. Fill the eight columns with 0-100 (blank = skip that axis; partial rows are
fine, manual overrides merge per axis), then --ingest and run validate_vibes.py.

The context columns are deliberately thin -- name, players, time, weight, a few
mechanics -- enough to recognise the game, not enough to reconstruct the
scoring model in your head.
"""
import json, os, csv, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, "bgg-cache.json")
MANUAL = os.path.join(HERE, "vibes-manual.json")
SHEET = os.path.join(HERE, "worksheet.csv")
AXES = ["cozy", "silly", "chatty", "swingy", "cutthroat", "crunchy", "tense", "storied"]


def owned_games():
    page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    i = page.index("const GAMES = [")
    j = page.index("\n];", i)
    return json.loads(page[i + len("const GAMES = "):j + 2])


def write_sheet(only_rated):
    cache = json.load(open(CACHE, encoding="utf-8"))
    games = owned_games()
    if only_rated:
        games = [g for g in games if g.get("myRating")]
    games.sort(key=lambda g: g["name"].lower())

    with open(SHEET, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "players", "time", "weight", "mechanics",
                    "yourRating"] + AXES + ["note"])
        for g in games:
            c = cache.get(str(g["id"]), {})
            w.writerow([g["id"], g["name"],
                        f'{g["minP"]}-{g["maxP"]}', g.get("time", ""),
                        g.get("weight", ""),
                        "; ".join((c.get("mech") or [])[:4]),
                        g.get("myRating", "")] + [""] * 6 + [""])
    print(f"wrote {os.path.relpath(SHEET, ROOT)} with {len(games)} games")
    print("fill the eight axis columns 0-100, then: python score_worksheet.py --ingest")


def ingest():
    if not os.path.exists(SHEET):
        raise SystemExit(f"no {SHEET} -- run without --ingest first")
    manual = json.load(open(MANUAL, encoding="utf-8")) if os.path.exists(MANUAL) else {}
    filled = axes_set = 0
    for row in csv.DictReader(open(SHEET, encoding="utf-8")):
        gid = (row.get("id") or "").strip()
        if not gid:
            continue
        rec = {}
        for ax in AXES:
            v = (row.get(ax) or "").strip()
            if v:
                rec[ax] = max(0, min(100, int(round(float(v)))))
        if (row.get("note") or "").strip():
            rec["note"] = row["note"].strip()
        if rec:
            manual.setdefault(gid, {}).update(rec)
            filled += 1
            axes_set += sum(1 for ax in AXES if ax in rec)
    with open(MANUAL, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manual, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"ingested {filled} games, {axes_set} axis scores -> "
          f"{os.path.relpath(MANUAL, ROOT)}")
    print("now: python validate_vibes.py")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="every owned game, not just rated")
    ap.add_argument("--ingest", action="store_true", help="read worksheet.csv back in")
    a = ap.parse_args()
    ingest() if a.ingest else write_sheet(not a.all)
