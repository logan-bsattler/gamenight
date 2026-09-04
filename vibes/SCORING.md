# Scoring reference

For filling in `worksheet.csv`. Every anchor below is a game **not** in your
collection, so nothing here nudges you on the 35 you are actually scoring.

## Before you start

- **Do not open `vibes-auto.json` or `vibes-llm-pass.json`.** The whole point of
  section 5 is that your numbers exist before you have seen the model's. Once
  you have read them you cannot unsee them, and the validation is spent.
- **Score the game as it plays at your table**, with your group, not as it
  reads on BGG.
- **Do not let your rating leak in.** You rated The Resistance a 5 and Secret
  Hitler a 10; they should score nearly identically on all eight axes. These
  measure what a game *is*, not whether you like it.
- **Blanks are fine.** A skipped cell just means that axis is not scored for
  that game. Partial rows merge per axis.

## How to fill it in

Go **column by column**, not row by row — score cozy for all 35 games, then
chatty for all 35. Judging one thing 35 times in a row is far more consistent
than judging eight different things about one game and then context-switching.

**Use the whole range.** If an axis ends up all 40s and 60s it carries no
information and the match score cannot use it. Something should be near 10 and
something near 90 on every axis. It is fine — expected, even — for a game to be
high on several axes at once.

## The eight axes

### Cozy — calm, warm, low-stakes
Would you play this on a rainy Sunday with tea? Losing does not sting.

| | |
|---|---|
| ~90 | Patchwork, Wingspan |
| ~50 | Carcassonne |
| ~10 | Twilight Struggle |

**Not the same as silly.** Patchwork is cozy and not silly. Jenga is silly
and not cozy. Cozy is the temperature; silly is the register.

### Chatty — how much the game is people
Talking, reading faces, deals, arguing. A game can be highly interactive and
barely chatty — Chess is pure conflict in silence.

| | |
|---|---|
| ~90 | Werewolf, Codenames |
| ~50 | Ticket to Ride |
| ~10 | Patchwork |

**Not the same as player count.** Score the conversation, not the seats.

### Silly — light, unserious
Are you laughing? Is a bad move funny rather than costly?

| | |
|---|---|
| ~90 | Twister, Jenga |
| ~50 | Ticket to Ride |
| ~10 | Brass: Birmingham |

### Cutthroat — direct, zero-sum pressure
Does your gain come out of someone's hide? Do you attack, block, or take?

| | |
|---|---|
| ~90 | Chess, Root |
| ~50 | Azul (you deny tiles, but mostly build) |
| ~10 | Pandemic (co-op — nobody is against you) |

**Not the same as "has a winner".** Everything has a winner. Score the
interference. A race where you never touch each other is low.

### Tense — pressure, stakes, adrenaline
Does your pulse rise? Time trouble, a doom track, a bluff that could collapse.

| | |
|---|---|
| ~90 | Escape: The Curse of the Temple |
| ~50 | Terraforming Mars in the last round |
| ~10 | Patchwork |

**Not the same as cutthroat.** Pandemic is a co-op — cutthroat near 10 — and can be
white-knuckle. Chess is maximally competitive and mostly serene.

### Crunchy — mental effort *while playing*
How hard is your brain working on a turn?

| | |
|---|---|
| ~90 | Chess, Agricola |
| ~50 | Ticket to Ride |
| ~10 | Snakes and Ladders |

**Not the same as rules complexity.** This one matters most. Chess has trivial
rules and is maximally crunchy; Gloomhaven has a phone-book rulebook and much of
a turn is bookkeeping. The model derives crunchy from BGG weight, which measures
*rules complexity* — so light-but-deep games are exactly where it is expected to
be wrong, and exactly where your scores are worth the most. Score the thinking,
not the teach.

### Swingy — how much dice decide it, not decisions

Could a good player lose to a bad one on a bad night? Score the randomness that
actually reaches the outcome, not the presence of dice — Ticket to Ride draws
cards and is barely swingy.

| | |
|---|---|
| ~10 | Chess |
| ~50 | Carcassonne |
| ~90 | Yahtzee, Snakes and Ladders |

**Not the same as silly.** A swingy game can be deadly serious. Backgammon is
almost pure variance and nobody is laughing.

### Storied — story and theme immersion

Do you talk about what happened afterwards as a story, or as a score? Does the
theme do work, or is it a coat of paint on a maths problem?

| | |
|---|---|
| ~10 | Azul, Chess |
| ~50 | Terraforming Mars |
| ~90 | Gloomhaven, Pandemic Legacy |

**Not the same as having a theme.** Nearly everything has a theme. Score
whether it generates events you would retell.

## When you are done

```bash
python vibes/score_worksheet.py --ingest
python vibes/validate_vibes.py
```

Read the report per axis, not overall:

- **MAE under 15** — that axis is trustworthy on the other 108 games.
- **High MAE, bias one direction** — the axis is systematically off. Fix the
  base constant only.
- **High MAE, bias near zero** — the BGG tags do not carry that axis. Mark it
  low-confidence in the UI (`LOW_CONF` in `index.html`) rather than tuning
  weights until it fits. Cozy and tense are the likely failures.

Do not tune weights to drive MAE toward zero. Thirty-five games is a small set
and the goal is generalising to the other 108, not matching these.
