# External levels

Each `.js` file in this directory is **one level**. The game (`../clone.html`)
probes for numbered filenames at load time, so adding or removing a file and
reloading the page updates the campaign — no manifest, no build step. Works on
GitHub Pages, any static server, and directly from disk (`file://`).

## File format

A level file is plain ASCII art wrapped in one function call:

```js
registerTextLevel(`
11. THE VAULT
----------------------------
<up to 16 map rows go here>
`);
```

- Line 1 inside the backticks: the level name (shown on the ready screen).
  Start it with the campaign number and a dot.
- Line 2: a dashed ruler (4+ dashes). It conveniently marks 28 columns.
- Then the board, top row first: up to 16 rows, up to 28 columns.
  Short or missing rows are padded with empty space automatically.
- Don't use backticks or `${` inside (nothing in the charset needs them).

## Charset

| char | meaning                               |
|------|---------------------------------------|
| ` `  | empty space                           |
| `#`  | diggable brick                        |
| `@`  | solid steel (never diggable)          |
| `H`  | ladder                                |
| `-`  | bar / rope                            |
| `X`  | false brick (looks solid, falls through) |
| `S`  | hidden exit ladder (appears when all gold is taken) |
| `$`  | gold                                  |
| `0`  | guard (max 5)                         |
| `&`  | runner start (exactly one)            |

## Filenames

- `level-NNN.js` — campaign continuation (original-inspired levels)
- `custom-NNN.js` — custom levels
- `NNN` is the zero-padded campaign level number. The 10 embedded levels are
  1–10, so external files start at 011. The probe window is 011–060; extend
  `probeExternalLevels()` in clone.html if you need more.
- Keep numbers contiguous: the audit warns when a filename's number doesn't
  match its actual campaign position.

## Validating

From the project root:

```
node audit-clone.js
```

audits every embedded and external level: dimensions, one runner, 1–5 guards,
gold present, hidden exit present, all gold statically reachable, and the exit
reachable after the last gold. Run it before playing a new level.

All levels here are original designs. Do not submit transcriptions of
copyrighted level maps (including the original 150-level campaign).
