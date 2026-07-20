# Clean-room research notes for clone.html

These notes record **observable rules and numeric behavior** studied from two references.
No source code, art, sound, or level data is copied into `clone.html`; all code there is
independently written from these behavioral descriptions.

## Reference A: SimonHung/LodeRunner_TotalRecall (unlicensed repo — study only)

Studied 2026-07-20 from a local clone (HEAD `cceca5d`, v2.30e, AI_VERSION 4).
The repo itself credits the AI algorithm to the book "玩 Lode Runner 學 C 語言" (BNN).
Its `lodeRunner.v.classic.js` levels are extracted from the Apple II 1983 disk image —
**those maps are copyrighted and are NOT transcribed** into clone.html.

### Board / model
- Grid 28 × 16 tiles; logical tile 40 × 44 px (5:5.5 proportion).
- Screen adds a thin "ground" strip (20 px) and a text/status row (44 px) below the field.
- Two-layer map: `base` (terrain incl. gold, hidden ladder) and `act` (live occupancy:
  terrain + RUNNER/GUARD markers). Actors are one tile with signed sub-tile offsets.
- Standard ASCII level charset (used across many LR remakes; a convention, not expressive
  content): ` `=empty, `#`=diggable brick, `@`=solid, `H`=ladder, `-`=bar/rope,
  `X`=false brick, `S`=hidden exit ladder, `$`=gold, `0`=guard, `&`=runner.

### Timing / speeds (AI v3/4 profile)
- Tick rates offered: 14/18/23/29/35 fps (speed setting); "normal" = 23 fps.
- Per tick: runner moves 8 px horizontally (tile = 40 → 5 ticks/tile) and 9 px
  vertically (tile = 44 → ~5 ticks/tile).
- Guard scheduling: per-tick move counts come from a 6-entry cyclic policy table indexed
  by guard count; e.g. 1 guard → [0,1,0,1,0,1] (half runner speed), 2 → [1,1,1,1,1,1],
  3 → [1,2,1,1,2,1] (each guard ~4/9 runner speed)… guards individually move at runner
  step size but skip turns; round-robin across guards.
- Hole: open ≈166 ticks, then 3 fill frames (8+8+4 ticks). Digging aborts (hole refills
  instantly) if a guard reaches the hole tile before a dig-progress threshold.
- Guard trapped shake: still 51 ticks (AI v4) + 5×3 shake frames, then climbs out.
- Guard reborn: 2 frames (6+2 ticks) at a random empty column starting from row 1.
- Level completes when all gold collected AND runner reaches row 0 (top) with offset 0.

### Movement rules (both actors)
- State support check: standing if on LADDER, or on BAR with yOffset==0, or tile below
  (act layer) is BLOCK/SOLID/LADDER/GUARD; otherwise falling. yOffset<0 (above center)
  always means falling continues.
- Offsets commit to the next tile when |offset| crosses half a tile; position then wraps
  (offset ± tile size), i.e. movement is continuous but tile identity is discrete.
- Perpendicular auto-centering: moving vertically decays xOffset toward 0 by one step
  per tick; moving horizontally decays yOffset likewise. Centering is gameplay.
- Ladder up: only if current or supporting cell is ladder; blocked above by BLOCK/SOLID/
  and (runner only) TRAP. Down from bar: releases into fall unless ladder/guard below.
- Falling past a BAR cell catches the bar exactly at center (yOffset 0).
- False brick (TRAP): blocks horizontal entry & upward exit like a brick, but gives no
  support — actor falls through when standing on it; revealed (dimmed) when fallen into.
- Gold pickup: only near tile center (|offset| < quarter tile, non-negative side), or
  slightly above a ladder top; guards pick up at most one gold.
- Runner death: guard within 3/4 tile in both axes, or guard occupies entered tile;
  also when buried by a refilling hole.

### Digging
- Dig left/right (not straight down): target is the tile beside+below; requires that
  tile to be diggable BLOCK and the tile directly beside to be empty (and not gold).
  Runner snaps to tile center when digging.
- A guard standing in/near an in-progress hole cancels the dig.
- Guard falling into hole: score bonus; carried gold is dropped in the cell above the
  hole (or lost if that cell is occupied). Guard buried by refill dies → respawns.
- Runner buried by refill dies.

### Guard AI (classic floor-scan; deliberately not BFS)
1. If must fall → fall (no decision).
2. Same-floor rule: if guard row == runner row (and runner not falling), walk toward
   runner if an uninterrupted "walkable-ignoring-walls" scan along the row reaches
   the runner column (cells passable if ladder/bar in cell, or support below:
   solid/brick/ladder/bar/gold/guard).
3. Otherwise scan the whole reachable floor span (left/right until a wall or until one
   step past a drop-off edge). At each column: if can descend (no floor below), rate a
   simulated fall/descent; if ladder, rate climbing up. Rating: reaches runner's row →
   |Δx from guard start|; ends above runner's row → (rowDiff + 100); below → (rowDiff
   + 200). Lowest rating wins; direction (left/right/up/down) of the best column is
   the chosen move. Ties resolve first-found (deterministic, learnable).
4. Trapped guard: shakes, then climbs out (up, then steps off the hole column).
5. Guards carrying gold drop it after a random 12–37 movement-boundary count, only on
   empty supported cells.
- Guards block each other (a guard tile is unwalkable for another guard).

### Scoring / lives (classic values)
- Gold 250, guard trapped 75, guard killed 75, level complete 1500; 5 lives,
  extra-life cap 100. (Win bonus per remaining man 42500 — endgame only.)

### Start-of-level behavior
- Game waits in a frozen state until the first accepted key action, then runs
  (matches the "inspection phase" in our experiments; historically the original also
  starts frozen until input).

## Reference B: YouTube PGUBbduTE6Y — "Apple Macintosh Shortplay Lode Runner 001-016"

1080p60 re-download studied 2026-07-20. This is the **1984 Macintosh port** —
used for monochrome look-and-feel, proportions, density and pacing only.
Frame samples in `frames-hq/` are analysis artifacts; nothing is embedded in the game.
The Mac OS menu bar / window chrome is deliberately NOT reproduced in clone.html.

Observations (qualitative, from sampled frames + prior contact sheets):
- White playfield, dense black brick patterning with light mortar lines, thin ladders
  and bars; tiny high-contrast actors; circular money-bag gold icons.
- Large status strip inside the display: `SCORE000000 MEN005 LEVEL001` style, boxed.
- Runner visibly faster than guards; digging and refill are quick; transitions minimal.
