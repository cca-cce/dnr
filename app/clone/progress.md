# Lode Runner Recreation — Progress and Technical Handoff

## Overarching aim

The long-term goal is to recreate all important aspects of the **Apple II version of Lode Runner** as faithfully as reasonably possible in **one standalone HTML file**, while avoiding copyright and other intellectual-property infringement.

“Faithfully” should mean matching the original experience at the level of observable behavior and design principles:

- Tile dimensions and screen composition.
- Movement speed, centering, gravity, ladder transitions, bars/ropes, digging, hole timing, and collision behavior.
- Guard pursuit, relative speed, trapping, climbing out, respawning, and interaction with gold.
- Gold collection, hidden exit ladders, scoring, lives, level completion, death, and restart flow.
- Keyboard responsiveness and the deliberate, puzzle-like rhythm of play.
- Apple II-era color restrictions, pixel proportions, sprite readability, tile patterns, typography, sound character, and minimal interface.
- Level-design principles such as route planning, irreversible drops, guard manipulation, false bricks, dig timing, escape ladders, and progressively denser puzzles.

The recreation must remain a **clean-room implementation**:

- Do not copy source code from another remake or disassembly.
- Do not embed original sprites, sound files, fonts, screenshots, video frames, or other extracted assets.
- Do not transcribe copyrighted level maps wholesale from the original game, repositories, screenshots, or videos.
- Use independently written JavaScript, canvas-drawn graphics, synthesized audio, and original or procedurally generated levels.
- External projects and recordings may be studied to understand publicly observable rules, timing, architecture, and visual principles, but their expressive content must not be imported.
- Preserve source attribution in research notes and comments where helpful, without implying endorsement or copying.

The current three HTML files are experiments toward that objective. None should yet be treated as the definitive recreation.

## Current files

| File | Role | Approximate size | Campaign |
|---|---|---:|---:|
| `index.html` | First iterative/naive implementation, subsequently heavily repaired | 45 KB | 100 levels |
| `runner.html` | Clean-room, code-architecture-driven Apple II-style implementation | 24 KB | 150 levels |
| `apple-ii.html` | Video-observation-driven monochrome Macintosh-style experiment | 17 KB | 150 levels |
| `clone.html` | Consolidated clean-room single file: repo-measured mechanics, themed renderer (Apple II / mono / neon), authored extensible levels | 56 KB | 10 levels |

All four are self-contained and have no external runtime dependencies. `progress.md` is the continuation document; `research-notes.md` holds the clean-room behavioral notes behind `clone.html`.

> **Note on this repository copy (`/tmp/comm/clone`):** only the consolidated
> clean-room file is present here, **renamed from `clone.html` to
> `runner.html`** — it is *not* the 24 KB attempt-2 `runner.html` described
> above (that file, plus `index.html` and `apple-ii.html`, lives in
> `/tmp/comm/dnr`). This repo is self-contained: `runner.html`, `levels/`,
> and the Node test harnesses `audit-clone.js`, `simtest-clone.js`, and
> `test-guard-gold.js` all run from this directory.

---

## Attempt 1: iterative naive implementation (`index.html`)

### Initial approach

The first version was designed from general knowledge of Lode Runner rather than a close study of a reference implementation. It used:

- A responsive dark/neon interface.
- Canvas-based tile rendering.
- Initially 28 × 18 tiles, later expanded to 28 × 19.
- Four classic-inspired text templates mixed with deterministic procedural generation.
- One hundred levels.
- Arrow movement and Space digging.
- Gold, ladders, ropes, diggable brick, solid steel, guards, holes, lives, score, hidden exits, pause, restart, and level skipping.

The code is primarily functional/procedural. Major systems are implemented as top-level functions and shared state rather than strongly separated classes.

### Level generation

The generator uses stable seeded randomness, so a given level number always creates the same layout.

Core generation ideas:

- Platform tiers are placed at regular vertical intervals.
- Segmented brick runs are created across each tier.
- Ladders connect adjacent tiers.
- Ropes bridge selected horizontal spans.
- Gold is placed only on cells considered reachable by a graph search.
- Guards spawn at reachable positions sufficiently far from the runner.
- A reachable high cell is selected for the hidden exit ladder.
- Every fifth level uses a classic-inspired template; other levels are generated.
- Gold count, guard count, ladder density, rope count, and steel reinforcement increase with level number.

Later improvements added:

- `improveRopes()` to move/remove ropes sitting directly above floors.
- `prepareDifficulty()` to add bottom access shafts and reinforced steel runs.
- Reachability filtering that prevents gold from overwriting ladders or ropes.
- Nondiggable reinforced sections from the first level onward.
- Full-campaign audits checking all 100 levels.

### Movement and collision evolution

The most valuable learning from this attempt came from repeated alignment bugs.

#### Early coordinate mistake

Actor `x` and `y` represented the top-left of a logical tile, but vertical cell lookup used:

```js
Math.floor(actor.y + 0.5)
```

This changed the reported row halfway through a cell. As a result, support detection saw the floor below approximately half a tile too early and stopped gravity while the sprite was visibly suspended above a platform.

The correction was to use a top-anchored vertical row lookup:

```js
Math.floor(actor.y + 0.05)
```

Landing now resolves against the tile intersected by the proposed body edge:

- Downward collision places the actor exactly one row above the contacted tile.
- Upward collision places the actor exactly one row below the contacted ceiling.

#### Sprite/collision mismatch

The original collision body ended around 11 pixels above the sprite’s feet. This caused visual overlap or floating during falling and landing. Collision extents were changed to match the drawn body more closely, with soles at the tile boundary.

#### Ladder-top transitions

Climbing could leave the runner at a fractional vertical coordinate near a platform corner. Horizontal movement then collided with the neighboring brick even though the sprite appeared to have cleared the ladder.

The implemented fix treats ladder exit as a discrete transition:

- Detect when the actor has crossed the top of the final ladder cell.
- Snap `x` to the ladder column.
- Snap `y` to the exact standing row.
- Preserve horizontal input so the actor can immediately step onto the platform.

This same behavior was later applied to guards.

#### Rope behavior

The first pose made actors appear to walk upright on ropes. The renderer was changed to a hanging pose with hands on the rope centerline and the body below it. Down releases the rope.

#### Dig snapping

Digging at a boundary between horizontal tiles could select the wrong diagonal brick. The current implementation:

- Considers nearby integer tile alignments.
- Sorts them by distance.
- Verifies the entire horizontal snap path is unobstructed.
- Requires a valid diggable diagonal brick.
- Snaps runner position before creating the hole.
- Supports the same operation from a rope when the snapped position remains on a rope cell.

### Guard logic

The first guard implementation greedily minimized Manhattan distance. It frequently became stuck at platform ends or selected a locally attractive route with no useful ladder.

It was replaced with breadth-first tile navigation:

- Horizontal transitions require support, ladder, or rope.
- Vertical transitions require ladders.
- Unsupported actors fall.
- Guards may release ropes when the runner is below.
- Neighbor ordering prefers the runner-facing direction when shortest paths tie.
- Guards share ladder-top snapping with the player.
- A short stuck timer recenters a guard if collision rounding prevents progress.

### Inspection phase

Each level now starts in a non-running inspection state:

- Runner blinks.
- Guards are frozen.
- Timer does not advance.
- Digging is disabled.
- First successful arrow movement arms the level.
- Guards start simultaneously and the runner receives brief spawn protection.

### Validation performed

Custom Node-based harnesses extracted the inline JavaScript, supplied minimal DOM/canvas stubs, and audited generated levels.

Verified at various stages:

- 100/100 levels generated.
- Zero unreachable gold cells.
- Every level retained bottom access shafts.
- Bottom planes were continuous and retained diggable brick.
- Every level contained ropes and reinforced steel.
- No rope tile remained immediately above solid floor after rope cleanup.
- Direct pursuit, distant-ladder pursuit, and rope-drop guard scenarios selected expected actions.
- Digging from platform borders, blocked snapping, and rope digging behaved correctly.
- Frozen inspection and post-movement activation behaved correctly.
- Chromium syntax/loading and screenshots were used for smoke testing.

### Strengths

- Most mature movement logic of the three files.
- Many edge cases were found using user screenshots and corrected empirically.
- Strong procedural reachability validation.
- Useful reference for ladder exits, platform alignment, dig snapping, inspection mode, and BFS guards.

### Weaknesses

- Visual design is an unrelated modern neon theme.
- Functional code grew through patches and is harder to reason about globally.
- The 19-row layout no longer resembles the original Apple II dimensions.
- Physics values were chosen by feel, not measured against original footage/emulation.
- Procedural tiers often look artificial and do not yet reproduce the authored puzzle language of classic Lode Runner.
- Reachability validation proves ordinary traversal but not full puzzle solvability under guard pressure, digging constraints, false bricks, or irreversible drops.

---

## Attempt 2: repository/code-informed implementation (`runner.html`)

### Reference studied

Repository:

<https://github.com/SimonHung/LodeRunner_TotalRecall>

The repository is a CreateJS-based HTML5 remake with separate files for:

- Runner movement.
- Guard movement and pursuit.
- Main state management.
- Tile definitions.
- Themes and recoloring.
- Input.
- Level sets.
- Storage and high scores.
- Audio and asset preloading.

Important observed architectural concepts included:

- A 28 × 16 tile map.
- Separate base terrain and active actor state.
- Tile types for empty, diggable brick, solid brick, ladder, bar, false brick, hidden ladder, gold, guard, and runner.
- Integer tile positions plus sub-tile offsets.
- Movement actions such as left, right, up, down, fall, dig, trapped, climb out, and reborn.
- Automatic centering on the perpendicular axis.
- Guard movement throttled relative to runner movement.
- Same-floor direct pursuit followed by broader floor/ladder scanning.
- Guards carrying and later dropping gold.
- Hole shaking, climbing out, death, and rebirth.

The cloned repository contained no obvious license file. For that reason, `runner.html` was written as a clean-room implementation. It does not include code, images, sounds, or level arrays from the repository.

### Architecture

`runner.html` is more top-down and structured than `index.html`:

- `Campaign` owns procedural terrain generation and static reachability.
- `Actor` contains shared runner/guard state.
- `Game` owns runtime state, movement, AI, holes, scoring, rendering, sound, controls, and transitions.
- Constants define the tile model and movement configuration.

The file returns to the reference’s 28 × 16 map.

### Mechanics

Implemented mechanics include:

- Arrow-key movement.
- `Z` and `X` for fixed-direction digging.
- Space for facing-direction digging.
- Platform-border dig snapping.
- Rope/bar hanging and downward release.
- Diggable and reinforced bricks.
- False bricks on later levels.
- Gold and hidden exit ladders.
- Guards with BFS pursuit.
- Guards picking up, carrying, and dropping gold.
- Guards trapped in holes, climbing out, dying on refill, and respawning.
- Five lives.
- Score rewards modeled on classic values.
- Previous/next level keys and buttons.
- No player-name input or high-score registration gate.
- Frozen inspection phase before the first move.

### Level design

`Campaign.build()` creates 150 deterministic original levels.

Generation uses:

- Platform rows at classic-looking 3-row intervals.
- Guaranteed ladder connections between all tiers.
- Bars with open air below.
- Steel runs increasing by level.
- False bricks introduced after early levels.
- Reachability-filtered gold placement.
- High reachable exit positions.
- Guard spawns far from the runner.
- Rising gold and guard counts.

### Visual design

The file uses a self-drawn Apple II-inspired palette:

- Black background.
- Blue patterned brick.
- White ladders and ropes.
- Violet runner.
- Cyan guards.
- Yellow gold.
- Green hidden exit ladder.
- Square-wave synthesized sounds.
- CRT scanline treatment.

No external images, sound files, libraries, fonts, or network calls are required.

### Validation

The full 150-level campaign was audited:

- 150/150 levels generated.
- Zero unreachable gold cells.
- 150/150 exit cells were statically reachable.
- 150/150 levels contained at least one guard.
- Inline JavaScript parsed successfully.
- Chromium rendered a visual smoke-test screenshot.

### Strengths

- Cleanest architecture of the three attempts.
- Most suitable foundation for a final single-file Apple II recreation.
- Includes guard/gold behavior absent from the initial design.
- Returns to the historically relevant 28 × 16 map.
- Avoids player-name and high-score-entry requirements.

### Weaknesses

- Visual appearance is “Apple II-inspired,” not measured or reconstructed faithfully.
- Generated maps remain tier-based and lack the deliberate traps and dependencies of authored classic levels.
- Guard gold behavior is simplified.
- False-brick placement is not yet validated as a puzzle mechanic.
- Sound frequencies and timings are invented.
- Animation is vector-like rather than carefully pixel-authored.
- There is no automated temporal simulation proving levels remain solvable with moving guards and hole refill.

---

## Attempt 3: video-informed implementation (`apple-ii.html`)

### Video studied

<https://www.youtube.com/watch?v=PGUBbduTE6Y>

The video title and metadata identify it as:

> Apple Macintosh Shortplay — Lode Runner — Levels 001–016

This is important: the recording is the **1984 Macintosh version**, not Apple II footage. It is useful for classic gameplay timing and monochrome interface study, but it must not be mistaken for the definitive Apple II visual reference.

Three sections were sampled:

- Opening and early levels.
- Mid-video levels.
- Later levels around the 30-minute mark.

Contact sheets were generated locally for analysis only. No frame is embedded in the game.

### Observed presentation

The Macintosh version uses:

- A white playfield.
- A Macintosh menu bar with File, Editor, Game, Options, and Scores.
- A centered “Lode Runner” window title.
- Thin monochrome ladders and horizontal bars.
- Dense black brick patterns with white mortar.
- Tiny black runner and guard sprites.
- Small circular money-bag/gold icons.
- A large outlined status strip inside the game display.
- Labels resembling `SCORE000000 MEN005 LEVEL001`.
- Minimal transition screens and almost no decorative UI.

### Observed gameplay characteristics

- Movement is discrete and strongly centered on the tile grid.
- The runner is visibly faster than guards.
- Guards take direct same-floor routes when possible.
- Digging and brick refill occur quickly.
- Actors visibly fall through holes and guards climb out.
- Hidden exit ladders appear immediately after all treasure is collected.
- Levels transition quickly.
- Level maps are densely authored and use large solid regions, shafts, chambers, bars, guard funnels, and false-brick routes.

### Implementation

`apple-ii.html` is a separate monochrome experiment with:

- A 28 × 16 playfield plus a 40-pixel in-canvas status row.
- Macintosh-style menu and title chrome.
- Black-and-white patterned bricks.
- Thin ladders and bars.
- Monochrome stick/pixel actors.
- Treasure-sack icons.
- `SCORE / MEN / LEVEL` display.
- Faster runner movement and slower guard movement.
- Faster 3.2-second holes and 2.1-second guard trap duration.
- Hidden exit ladders and short level transitions.
- Frozen inspection phase.
- 150 deterministic original levels.

It deliberately does not reproduce the observed level maps or captured graphics.

### Validation

- JavaScript syntax passed.
- No external assets were detected.
- 150/150 levels generated.
- Zero unreachable gold cells.
- 150/150 exits were statically reachable.
- 150/150 levels contained guards.
- Chromium rendered the Macintosh-style board successfully.

### Strengths

- Closest of the three attempts to the sampled video’s actual composition.
- Strong reference for monochrome tile patterns and minimal classic UI.
- Captures the large embedded status strip and compact sprites.
- Smaller and easier to inspect than `index.html`.

### Weaknesses

- It emulates Macintosh presentation, not Apple II presentation.
- Code is highly compressed and less maintainable than `runner.html`.
- The observed video was used qualitatively; frame-by-frame timing has not been measured.
- Generated layouts do not yet reproduce the density or authored puzzle structure visible in the video.
- The actor art is still schematic.

---

## Attempt 4: consolidated single-file clone (`clone.html`)

### Sources consolidated

Written 2026-07-20 as the first attempt to combine all three research tracks
(see `research-notes.md` for the full behavioral notes):

- **Mechanics/timing** reimplemented from behavior observed in the local clone
  of `SimonHung/LodeRunner_TotalRecall` (repo now in `LodeRunner_TotalRecall/`):
  28×16 board, 40×44 logical tile, 23 ticks/s, 8 px/tick horizontal and
  9 px/tick vertical movement, half-tile commit with perpendicular
  auto-centering, hole open 166 ticks + 8/8/4 refill, dig 11 ticks with
  guard-cancel window, guard shake 51+15 ticks, reborn 8 ticks, guard
  schedule via the classic 6-entry move-policy table, classic floor-scan
  guard AI (|dx| / +100 above / +200 below ratings), gold carry 12–37 steps,
  classic scoring (250/75/75/1500) and 5 lives (+1 per level).
  No code, art, sound, or level data was copied; the repo has no license and
  its `v.classic` levels are the copyrighted Apple II originals.
- **Look and feel** calibrated against the 1080p60 re-download of the
  Macintosh shortplay video (`lode-runner-mac-shortplay-PGUBbduTE6Y-hq.mp4`,
  frames in `frames-hq/`): the "MONOCHROME" theme reproduces the white field,
  dense black brick, thin outlined ladders, `$` money bags, silhouette actors,
  checkered strip and boxed `SCORE/MEN/LEVEL` line — deliberately **without**
  the Mac menu bar/window chrome.
- **Architecture** follows this document's recommended structure: Profile,
  LevelModel (base/act layers), ActorState, MovementSystem, DigSystem,
  GuardSystem, Campaign, themed Renderer, AudioSystem (synth square-wave),
  GameStateMachine (ready→running→dead/done/over/win/paused).

### Design decisions

- **Themes are first-class**: `Themes` array (APPLE II, MONOCHROME, NEON),
  cycled with `T`, persisted in localStorage, overridable via `?theme=N`.
  Apple II look is one theme among several, per the plan to keep the
  reference platform explicit.
- **Levels are data**: 10 original hand-authored levels (28×16 ASCII maps in
  the conventional charset) registered through `registerLevelPack(name,
  levels)`; extra packs can be appended in code or via a JSON array under
  localStorage key `clone_custom_levels`. Short rows are space-padded by the
  loader. `?level=N` jumps for testing.
- Win condition is classic: all gold collected reveals hidden `S` ladders,
  then reach row 0.
- Keys: arrows, `Z`/`X` (+`U`/`O`) dig, Space digs facing, `P` pause, `R`
  abort (costs a life), `,`/`.` level nav, `T` theme, `M` mute.

### Validation performed

- `node --check` on the extracted inline script: pass.
- `audit-clone.js` (node + vm with DOM stubs, running the real LevelModel):
  10/10 levels pass structure checks (16×28, one runner, 1–5 guards, ≥1 gold,
  hidden ladder present) and static reachability (all gold reachable with
  walk/climb/fall/one-deep-dig edges; top row reachable after exit reveal).
  Six levels initially failed and were redesigned until clean.
- `simtest-clone.js`: drives the real Game headlessly ~1200 ticks per level
  with scripted inputs and opportunistic digs — no exceptions, holes and
  guard trapping exercised on every level, and the pursuit AI closes
  distance 16→4 in 150 ticks on level 1.
- Chromium headless screenshots: desktop 1400×1000 (`shot-clone-desktop.png`
  APPLE II, `shot-clone-mono.png` MONOCHROME, `shot-clone-neon.png` NEON) and
  compact 700×500 (`shot-clone-compact.png`, canvas scales correctly).

### External levels (added 2026-07-20, second session)

The project aim was rescoped to **proof of concept** rather than a full
150-level clone. `clone.html` gained a ~90-line external-level loader; the
embedded 10 levels are untouched and the file still works standalone.

- **One level per file** in `levels/`: `level-011.js` … `level-020.js`
  (original-inspired campaign continuation) and `custom-021.js` …
  `custom-030.js` (custom levels). A file is the plain-text ASCII format
  (name line, dashed ruler, ≤16 map rows) wrapped in a single
  `registerTextLevel(\`…\`)` call — see `levels/README.md`.
- **Discovery by filename probing** (`probeExternalLevels()`): script tags for
  `level-NNN.js`/`custom-NNN.js`, N = 011–060; missing files are silent
  no-ops; found files self-register and the campaign refreshes
  (`Game.refreshCampaign`). Works identically on GitHub Pages, any static
  server, and `file://` (which is why packs are `<script src>`-loaded JS
  wrappers, not fetched `.txt` — fetch is blocked on `file://`).
  Add/remove files → reload → campaign follows.
- **Copyright stance**: the 20 new levels are original geometry. The
  original-inspired batch follows the classic campaign's *progression
  structure* (mechanic introduction cadence, guard/gold ramps) but no layout
  is transcribed or derived from the protected 150 maps; "slightly modified
  but recognizable" was explicitly rejected as still-infringing.
- **Validation**: `audit-clone.js` now also parses every `levels/*.js`
  (structure, reachability, filename-number vs campaign-position vs name-number
  consistency). 30/30 levels pass (one ANTFARM redesign was required —
  corridor segments between floor gaps were statically unreachable).
  Chromium `file://` smoke screenshots: `shot-clone-ext15.png` (external
  level 15, Apple II theme), `shot-clone-ext25.png` (custom level 25, mono
  theme); the ~80 unmatched probe names exercised the missing-file path.
- `?level=N` now works past the embedded range (a pending request is honored
  when probing completes).

**Dynamic-solvability incident (same day):** the first version of external
level 11 (THE VAULT) passed the static audit but was unwinnable in play — its
vault-floor dig opened a pit enclosed by steel and bedrock, burying the runner
on refill. Confirmed by driving the real engine headlessly
(scripted dig → drop → wait out refill → `state: dead`), then fixed by raising
the vault one row so the floor dig drops through into the open bottom
corridor (same script now ends alive on row 14). This is the concrete case
for research task 10 (a solver modeling digging/refill), and the sim script
pattern is the seed for it.

**Gold-accounting fix (same day, user-reported):** the exit ladder was
appearing once map gold hit zero even while a guard still carried one.
Reference evidence (`lodeRunner.guard.js:367` — guard pickup calls
`removeGold` **without** `decGold`; only the runner's pickup and
carried-gold destruction call `decGold`, which is the sole reveal site)
confirms the classic rule: goldCount tracks gold the runner has yet to
collect; guard pickup/carry/drop never change it; gold destroyed with a
dying/trapped guard is written off so it can't block the exit forever.
clone.html now mirrors this, including the post-drop `hasGold = -1`
re-pickup cooldown. Verified with an engine-driven test
(guard carries → exit stays hidden → drop → runner collects → reveal).

### Guard pit physics (2026-07-20, third session — deliberate house rules)

User-reported bug: guards sometimes failed to release carried gold when
falling into a dug pit. Root cause: gold release lived only in
`guardTrapped()`, gated on the guard landing at exactly `yo === 0`; the
settle clamp only applied when `hardBelow` held, so in a pit dug through a
one-brick floor with open space below, `yo` stepped past 0, `moveGuards`
misrouted the guard into the shake timer without ever calling
`guardTrapped()`, and the guard hung suspended mid-hole (~6 s, no trap
score, no `holeX`) before falling out the bottom still carrying its gold —
or being buried by the refill.

The fix implements **deliberately chosen house rules** (predictable,
physically motivated) that **deviate from the reference**, where *any* hole
pins a guard regardless of what is below (`lodeRunner.guard.js:92-94`
forces `stayCurrPos = 1` on every settling tick) and gold release is always
forced (at `AI_VERSION >= 4` even before the guard fully lands,
`lodeRunner.guard.js:217-225`):

1. **Pit with a hard floor below** → guard traps at `yo = 0`,
   `guardTrapped()` force-releases gold onto the cell above the hole (or
   writes it off against `goldCount` if that cell is blocked). Classic
   behavior, unchanged; common on the bottom plane of levels.
2. **Open-bottomed pit (space/ladder/bar below), hole open** → the guard
   falls straight through in one clean motion, always, keeping any carried
   gold. (`stepActor`: FALL→INHOLE conversion now requires `stay`;
   `moveGuards`: INHOLE with `yo > 0` resumes `A.FALL` instead of the shake
   timer.)
3. **Open-bottomed pit that is refilling** → the closing brick pins the
   guard even over open space (`stepActor` treats a `phase === "fill"` hole
   as `stay` for guards): it traps, releases gold as in rule 1, and is then
   buried by the refill (dies, carried-gold accounting as before).
4. **Carried gold while running** — unchanged, verified: guards drop
   carried gold mid-run after a random 12–37 tile crossings
   (`Profile.goldDropMin/Max`, same values as the reference), with the
   1-crossing re-pickup cooldown.

Validation: new engine-driven test `test-guard-gold.js` (in this repo)
asserts all four rules headlessly against the real `Game`; plus
`audit-clone.js` (30/30 levels) and `simtest-clone.js` both pass.
The test harnesses were updated to load `runner.html` (this repo's name for
the consolidated file) so the repo is self-contained.

### Guard pit physics reverted to classic (2026-07-20, fourth session)

The house rules above were judged a mistake and **reverted to the
reference-faithful behavior** (`lodeRunner.guard.js` in
`/tmp/comm/LodeRunner_TotalRecall`):

1. **Any dug hole pins a falling guard**, regardless of what is below
   (reference lines 92–94 force `stayCurrPos = 1` whenever a falling guard
   with `yOffset < 0` occupies a `base == BLOCK_T` cell). The former rule 2
   (clean fall-through of open-bottomed pits) and rule 3 (fill-phase-only
   pinning) are gone; `stepActor` now forces `stay` for any guard settling
   into a hole, and the `INHOLE`-commit escape plus the `moveGuards`
   mid-settle fall-out branch were removed as dead code.
2. **Carried gold is released while the guard is still falling in**
   (reference AI v4, lines 217–225: drop onto the cell above if empty, else
   written off via `decGold`). Implemented as `releaseGuardGold(g)`, called
   from `moveGuards` on the tick the fall converts to `INHOLE`;
   `guardTrapped()` calls it too as a safety net (v3-timing equivalent).
3. Trap score, shake, climb-out, refill burial, and mid-run gold drop
   (12–37 crossings) are unchanged.

`test-guard-gold.js` was updated accordingly: rule B now asserts the guard
is pinned over open space, never falls through, releases gold before
landing, and climbs out. All checks pass, plus `audit-clone.js` (30/30)
and `simtest-clone.js`.

### Known gaps

- Solvability is proven statically, not under guard pressure or hole timing;
  the richer solver from "Next research tasks" item 10 still applies.
- Runner/guard sprites are parametric rects, not measured pixel art.
- Sound is plausible synth, not measured against Apple II character.
- The mono status strip uses a bold monospace font, not the dotted outline
  font visible in the footage.
- Still Macintosh-informed for visuals; the Apple II theme palette remains
  approximate until real Apple II footage is measured (task list item 1).

---

## Cross-cutting technical insights

### 1. Use one unambiguous actor coordinate convention

The most damaging bugs arose from mixing tile-center, tile-top, and sprite-foot coordinates.

Recommended final convention:

- `actor.x` and `actor.y` represent the top-left of the actor’s logical tile.
- Horizontal cell identity may use the actor’s body center.
- Vertical support identity must remain top-anchored until a collision boundary is crossed.
- Sprite feet and collision bottom must terminate at the same tile boundary.
- Ladder and bar transitions should explicitly snap to rows/columns.

Document this in the final file near the actor class.

### 2. Movement should be stateful, not merely velocity-based

A faithful final implementation should explicitly track states such as:

- Waiting/blinking.
- Standing.
- Running left/right.
- Climbing up/down.
- Hanging left/right.
- Falling.
- Digging left/right.
- Trapped.
- Climbing out.
- Reborn.
- Dead.

This will make animation, collision, sound, and AI easier to synchronize than inferring everything from velocity every frame.

### 3. Centering is part of the gameplay

Classic movement does not behave like free analog platforming. When changing axis:

- Vertical movement should center horizontal offset.
- Horizontal movement should center vertical offset.
- Ladder tops and bottoms need explicit transitions.
- Digging should center/snap before opening a brick.

The first attempt’s corrections should be preserved.

### 4. Static reachability is necessary but insufficient

Current audits only prove that cells are connected under simplified movement.

A level can still be practically impossible because:

- Gold requires a dig sequence not modeled by BFS.
- A false brick causes an irreversible drop.
- A hidden ladder appears in an unusable place.
- A guard permanently carries inaccessible gold.
- A required hole refills too early.
- A nondiggable brick prevents a necessary trap.
- The runner cannot survive guard pressure on a narrow route.

The final generator needs a richer state-space solver or carefully authored original levels.

### 5. Good Lode Runner levels are not just connected platform tiers

Classic puzzle quality depends on interacting mechanisms:

- Routes that are safe in only one direction.
- Deliberate falling entrances.
- Dig sequences with timing dependencies.
- Guard baiting and containment.
- Gold that must be collected before a route is destroyed.
- Bars that provide a genuine alternate route or escape.
- False bricks used as information and commitment tests.
- Steel shaping where holes can and cannot be made.
- Hidden exit ladders that alter the final traversal.

Procedural generation should operate on puzzle motifs and validated transformations, not only random platform segments.

### 6. Guard intelligence should preserve classic limitations

Perfect BFS is robust but may be less faithful or too strong. The final behavior should be calibrated against Apple II gameplay:

- Direct pursuit on the same floor.
- Search along the current floor for useful ladders or drops.
- Slower movement schedule than the runner.
- Deterministic tie-breaking that players can learn and exploit.
- Intentional inability to foresee digging or complex future states.
- Correct interaction with other guards, gold, holes, bars, and false bricks.

The repository-informed floor-scanning logic may be a better behavioral model than unrestricted BFS, but it must be independently reimplemented.

### 7. Inspection mode is useful but may not be historically faithful

The blinking, frozen pre-move phase was requested and works well for generated levels. Before finalizing, determine whether the Apple II original used an equivalent delay or blinking spawn behavior. If not, keep it as an optional accessibility/gameplay setting rather than an unconditional historical claim.

### 8. Reference platform must be kept explicit

Do not mix Macintosh, Apple II, Commodore 64, NES, and modern-remake details without labeling them.

- `apple-ii.html` currently reflects a Macintosh video.
- `runner.html` reflects an Apple II-inspired palette plus architecture learned from a modern remake.
- The next research step must use reliable Apple II footage or emulation as the primary behavioral and visual reference.

---

## Recommended direction for the definitive file

Use `runner.html` as the architectural base, but create a new, clearly named definitive file after additional Apple II research.

Recommended system structure inside the single HTML file:

1. `AppleIIProfile`
   - Exact palette.
   - Canvas resolution and pixel aspect.
   - Tile and sprite dimensions.
   - Timing constants.
   - Sound parameters.

2. `LevelModel`
   - Immutable base terrain.
   - Mutable active terrain.
   - Hidden ladder state.
   - Gold ownership/location.

3. `ActorState`
   - Tile coordinate.
   - Sub-tile offset.
   - Explicit action/state.
   - Facing and animation frame.

4. `MovementSystem`
   - Per-state transition rules.
   - Axis centering.
   - Collision and gravity.
   - Ladder/bar entry and exit.

5. `DigSystem`
   - Snap validation.
   - Hole animation phases.
   - Refill timing.
   - Actor interactions.

6. `GuardSystem`
   - Classic pursuit policy.
   - Guard scheduling/speed ratios.
   - Gold carrying and dropping.
   - Trap, climb-out, death, and rebirth.

7. `Campaign`
   - Original authored levels plus validated procedural variations.
   - Level metadata and difficulty.
   - Solver/auditor hooks.

8. `AppleIIRenderer`
   - Integer pixel scaling only.
   - Original clean-room sprites and patterns.
   - No browser smoothing.
   - Faithful status text composition.

9. `AudioSystem`
   - Synthesized short effects based on measured character, not copied recordings.

10. `GameStateMachine`
    - Load, ready, running, paused, dead, complete, game over, win.

---

## Next research tasks

1. Locate high-quality footage specifically identified as the Apple II release.
2. Record or sample representative events:
   - Horizontal traversal across one tile.
   - Ladder traversal across one tile.
   - Free-fall across one tile.
   - Dig animation duration.
   - Hole open duration and refill phases.
   - Guard trap and climb-out duration.
   - Runner/guard speed ratio.
   - Spawn blink and level-start timing.
3. Determine exact Apple II playfield tile count, status area, palette behavior, and pixel aspect.
4. Compare keyboard repeat behavior and simultaneous-key handling.
5. Study how guards select paths and resolve collisions with one another.
6. Study gold pickup/drop rules for guards.
7. Catalog puzzle motifs from observation without transcribing complete copyrighted level maps.
8. Build a small set of original hand-authored test levels, each isolating one mechanic.
9. Add automated movement traces for ladders, bars, falls, platform edges, holes, and guard pursuit.
10. Add a solver capable of modeling digging and irreversible falls before expanding procedural generation.

## Continuation checklist

Before making future changes:

- Read `agents.md`.
- Preserve all existing files unless replacement is explicitly requested.
- Keep changes to this repo inside `/tmp/comm/clone` (the older experiments
  and reference material live in `/tmp/comm/dnr`).
- After touching guard/gold/hole behavior, run `node test-guard-gold.js`.
- Use `apply_patch` for source edits.
- Do not install packages without explicit approval.
- If Python is needed, activate `~/lib/python/uv-osm` first.
- Validate inline JavaScript with Node.
- Run campaign-wide reachability audits.
- Run a real browser smoke test.
- Capture screenshots at both desktop and compact viewport sizes.
- Document which platform/version each behavior came from.
- Keep the clean-room, non-infringing objective central to every design decision.
