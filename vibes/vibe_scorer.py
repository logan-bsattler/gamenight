#!/usr/bin/env python3
"""Score every owned game on six vibe axes from BGG data.

Reads  vibes/bgg-cache.json   (raw BGG fields, refreshed via the bgg-mcp server)
Writes vibes/vibes-auto.json  (raw 0-100 scores, regenerable, safe to delete)

Never touches vibes-manual.json. Merging happens in build_vibes.py.

Signal matching
---------------
The spec names signals in shorthand; BGG's actual tag vocabulary differs in
places. Named signals are matched against the union of a game's mechanics and
categories, since the spec mixes the two freely (Dexterity is a category,
Flicking is a mechanic, Negotiation is both). ALIASES below maps each shorthand
onto the real BGG tags. Anything with no real tag never fires and is reported
by --report so the dead signals stay visible rather than silently scoring zero.
"""
import json, os, sys, argparse, statistics
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "bgg-cache.json")
AUTO = os.path.join(HERE, "vibes-auto.json")

AXES = ["cozy", "social", "playful", "compete", "intense", "thinky"]

# Spec shorthand -> real BGG tags. A shorthand mapping to () never fires.
ALIASES = {
    "Tech Trees": ("Tech Trees / Tech Tracks",),
    "Dexterity": ("Action / Dexterity",),
    "Nature": ("Environmental",),
    # Spec says "Social Deduction or Hidden Roles". Plain "Deduction" is
    # deliberately excluded -- Alchemists is deductive but not social.
    "Social Deduction": ("Hidden Roles", "Roles with Asymmetric Information", "Traitor Game"),
    # The umbrella tag plus BGG's specific auction variants.
    "Auction/Bidding": ("Auction / Bidding", "Auction: Dutch", "Auction: English",
                        "Auction: Once Around", "Auction: Sealed Bid",
                        "Auction: Turn Order Until Pass", "Turn Order: Auction",
                        "Constrained Bidding"),
    # Spec's "Direct conflict-y attack mechanics" is not a BGG tag. Defined here
    # as BGG's explicitly conflict-oriented tags. Adjust this list to taste --
    # it is the one place the model encodes a judgement call rather than the spec.
    "DirectConflict": ("Campaign / Battle Card Driven", "Card Play Conflict Resolution",
                       "Tug of War", "Wargame", "Modern Warfare"),
}

# Shorthands with no BGG equivalent anywhere in the collection.
KNOWN_DEAD = ["Engine Building", "Gardening", "Word Game", "Trivia",
              "Stacking and Balancing", "King of the Hill", "Acting"]


def tags(g):
    return set(g.get("mech", [])) | set(g.get("cat", []))


def has(g, name, seen=None):
    """True if the game carries the spec signal `name`."""
    want = ALIASES.get(name, (name,))
    if seen is not None:
        seen[name] += 1 if tags(g) & set(want) else 0
    return bool(tags(g) & set(want))


def rank(g, family):
    return family in (g.get("ranks") or {})


def capped(g, names, per, cap, seen=None):
    return min(cap, per * sum(1 for n in names if has(g, n, seen)))


def weight_of(g, fallback):
    """averageweight, with 0 treated as null per spec, falling back to the
    median weight of games sharing this game's primary category."""
    w = g.get("weight")
    if w:
        return w
    cats = g.get("cat") or []
    primary = cats[0] if cats else None
    return fallback.get(primary) or fallback["__all__"]


def score(g, fallback, seen=None):
    w = weight_of(g, fallback)
    wn = (w - 1) / 4.0  # normalised complexity, ~0..1
    maxT = g.get("maxT") or 0
    maxP = g.get("maxP") or 0
    minAge = g.get("minAge") or 99
    s = {}

    # ---- Thinky ----
    v = wn * 70
    v += 15 if rank(g, "strategygames") else 0
    v += 10 if rank(g, "abstracts") else 0
    v += capped(g, ["Worker Placement", "Engine Building", "Action Points", "Tech Trees",
                    "Network and Route Building", "Programmed Movement", "Grid Coverage",
                    "Auction/Bidding"], 5, 15, seen)
    v -= 25 if rank(g, "partygames") else 0
    v -= 30 if rank(g, "childrensgames") else 0
    v -= 10 if has(g, "Roll / Spin and Move", seen) else 0
    s["thinky"] = v

    # ---- Cozy ----
    v = 60 - wn * 30
    v += 15 if has(g, "Cooperative Game", seen) else 0
    v += 10 if has(g, "Solo / Solitaire Game", seen) else 0
    v += capped(g, ["Tile Placement", "Set Collection", "Pattern Building",
                    "Open Drafting", "Closed Drafting"], 8, 24, seen)
    v += 8 * sum(1 for n in ["Animals", "Farming", "Nature", "Puzzle", "Gardening"]
                 if has(g, n, seen))
    v -= 25 if has(g, "Player Elimination", seen) else 0
    v -= 20 if has(g, "Take That", seen) else 0
    v -= 15 if has(g, "Real-Time", seen) else 0
    v -= 20 if rank(g, "wargames") else 0
    v -= 10 * sum(1 for n in ["Horror", "Fighting", "Wargame"] if has(g, n, seen))
    s["cozy"] = v

    # ---- Social ----
    # Base (not in the spec, added afterwards). Social and compete were the only
    # axes without one, so they were pure additive bonus lists: 42% and 38% of the
    # collection scored exactly 0 and percentiles could not separate the ties.
    # A base has to come from a CONTINUOUS variable to break them -- player count
    # takes about five distinct values across the collection and just moves the
    # pile-up, so both bases key off averageweight, like the other four axes.
    # Lighter games talk more; the table is louder over Sushi Go than Brass.
    v = 50 - wn * 30
    sd, hr = has(g, "Social Deduction", seen), has(g, "Hidden Roles", seen)  # no short-circuit, keeps --report honest
    v += 30 if (sd or hr) else 0
    v += 25 if has(g, "Negotiation", seen) else 0
    v += 20 if has(g, "Trading", seen) else 0
    v += capped(g, ["Voting", "Acting", "Storytelling", "Team-Based Game",
                    "Communication Limits"], 20, 40, seen)
    v += 20 if rank(g, "partygames") else 0
    v += 10 if rank(g, "familygames") else 0
    v += 10 if maxP >= 6 else 0
    v -= 20 if maxP == 2 else 0
    v -= 15 if rank(g, "abstracts") else 0
    # NOTE: spec's "+5 language dependence: no necessary text" is unimplemented --
    # the bgg-mcp server does not expose the language_dependence poll.
    s["social"] = v

    # ---- Playful ----
    v = 70 - wn * 55
    v += 20 * sum(1 for n in ["Party Game", "Humor", "Children's Game"] if has(g, n, seen))
    v += capped(g, ["Dexterity", "Flicking", "Stacking and Balancing",
                    "Push Your Luck", "Acting"], 15, 30, seen)
    v += 10 * sum(1 for n in ["Word Game", "Trivia"] if has(g, n, seen))
    v += 10 if maxT and maxT <= 30 else 0
    v += 5 if minAge <= 8 else 0
    v -= 20 if rank(g, "wargames") else 0
    v -= 15 if maxT >= 120 else 0
    s["playful"] = v

    # ---- Compete ----
    # Hard rule: a co-op is not competitive, whatever else it carries.
    if has(g, "Cooperative Game", seen):
        s["compete"] = 10
    else:
        # Base, same reasoning as social. Heavier games give players more ways to
        # act against each other, so competitive pressure rises with weight.
        v = 25 + wn * 20
        v += 30 if has(g, "Player Elimination", seen) else 0
        v += 25 if has(g, "Take That", seen) else 0
        v += capped(g, ["Area Majority / Influence", "Auction/Bidding",
                        "Betting and Bluffing", "King of the Hill",
                        "Territory Building", "DirectConflict"], 15, 45, seen)
        v += 20 if rank(g, "wargames") else 0
        v += 10 if rank(g, "strategygames") else 0
        v -= 15 if has(g, "Solo / Solitaire Game", seen) else 0
        s["compete"] = v

    # ---- Intense ----
    v = wn * 35
    v += 25 if has(g, "Real-Time", seen) else 0
    v += 20 if has(g, "Traitor Game", seen) else 0
    v += 20 if has(g, "Player Elimination", seen) else 0
    v += 15 if rank(g, "thematic") else 0
    v += 15 if rank(g, "wargames") else 0
    v += 10 * sum(1 for n in ["Horror", "Fighting", "Adventure"] if has(g, n, seen))
    v += 15 if maxT >= 120 else 0
    v += 10 if maxT >= 180 else 0
    v -= 20 if rank(g, "childrensgames") else 0
    v -= 15 * sum(1 for n in ["Party Game", "Children's Game"] if has(g, n, seen))
    s["intense"] = v

    return {k: int(round(max(0, min(100, val)))) for k, val in s.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="print signal coverage and axis spread")
    a = ap.parse_args()

    games = json.load(open(CACHE, encoding="utf-8"))

    # Median weight per primary category, for games whose averageweight is 0/null.
    bycat = {}
    allw = [g["weight"] for g in games.values() if g.get("weight")]
    for g in games.values():
        if g.get("weight") and g.get("cat"):
            bycat.setdefault(g["cat"][0], []).append(g["weight"])
    fallback = {c: statistics.median(v) for c, v in bycat.items()}
    fallback["__all__"] = statistics.median(allw) if allw else 2.0

    seen = Counter()
    out = {gid: score(g, fallback, seen) for gid, g in games.items()}

    with open(AUTO, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"scored {len(out)} games -> {os.path.relpath(AUTO, HERE)}")

    if a.report:
        print("\n--- signals that never fire ---")
        dead = [n for n in list(seen) if seen[n] == 0] + KNOWN_DEAD
        for n in sorted(set(dead)):
            print(f"  {n}")
        print("\n--- axis spread (raw) ---")
        print(f"{'axis':9}{'min':>5}{'p25':>6}{'med':>6}{'p75':>6}{'max':>6}{'mean':>7}")
        for ax in AXES:
            v = sorted(s[ax] for s in out.values())
            q = lambda p: v[int(p * (len(v) - 1))]
            print(f"{ax:9}{v[0]:5}{q(.25):6}{q(.5):6}{q(.75):6}{v[-1]:6}"
                  f"{statistics.mean(v):7.1f}")


if __name__ == "__main__":
    main()
