// Audit harness for runner.html (node). Extracts the inline script, runs it
// with DOM stubs, then checks structure + static reachability of all levels.
"use strict";
const fs = require("fs");
const vm = require("vm");

const html = fs.readFileSync(__dirname + "/runner.html", "utf8");
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (!m) { console.error("FAIL: no inline script found"); process.exit(1); }
const src = m[1];

// ---- DOM/browser stubs ----
const noop = () => {};
const ctxStub = new Proxy({}, { get: (t, p) => {
  if (p === "canvas") return {};
  return noop;
}, set: () => true });
const canvasStub = { getContext: () => ctxStub, width: 0, height: 0 };
const sandbox = {
  console,
  window: {},
  document: {
    getElementById: () => canvasStub,
    body: { style: {} },
  },
  localStorage: { getItem: () => null, setItem: noop },
  performance: { now: () => 0 },
  requestAnimationFrame: noop,
  addEventListener: noop,
};
sandbox.window = sandbox; // window === global scope for the script
vm.createContext(sandbox);
try {
  vm.runInContext(src, sandbox, { filename: "runner.html<script>" });
} catch (e) {
  console.error("FAIL: script threw during load:", e.stack.split("\n").slice(0, 4).join("\n"));
  process.exit(1);
}
const { Profile, LevelModel, campaignLevels, parseTextLevel } =
  sandbox.CloneGame || sandbox.window.CloneGame;
const levels = campaignLevels().map(lv => ({ ...lv, src: "embedded" }));
console.log(`Loaded ${levels.length} embedded levels`);

// ---- external single-level files: levels/level-NNN.js, custom-NNN.js ----
const path = require("path");
const levelsDir = path.join(__dirname, "levels");
if (fs.existsSync(levelsDir)) {
  const files = fs.readdirSync(levelsDir)
    .filter(f => /^(level|custom)-\d{3}\.js$/.test(f))
    .sort((a, b) => (+a.match(/(\d+)/)[1]) - (+b.match(/(\d+)/)[1]) || a.localeCompare(b));
  let expected = levels.length + 1; // campaign numbering continues after embedded
  for (const f of files) {
    const js = fs.readFileSync(path.join(levelsDir, f), "utf8");
    const tm = js.match(/registerTextLevel\(`([\s\S]*?)`\)/);
    if (!tm) { console.error(`${f}: FAIL no registerTextLevel template`); process.exit(1); }
    const lv = parseTextLevel(tm[1]);
    if (!lv) { console.error(`${f}: FAIL unparseable level text`); process.exit(1); }
    const fileNum = +f.match(/(\d+)/)[1];
    const nameNum = +(lv.name.match(/^(\d+)\./) || [])[1];
    const naming = [];
    if (fileNum !== expected)
      naming.push(`filename number ${fileNum} but campaign position is ${expected}`);
    if (nameNum !== fileNum)
      naming.push(`name says ${nameNum} but filename says ${fileNum}`);
    // pad like registerLevelPack does
    const map = lv.map.slice(0, Profile.rows);
    while (map.length < Profile.rows) map.push("");
    lv.map = map.map(r => r.length > Profile.cols ? r.slice(0, Profile.cols) : r.padEnd(Profile.cols));
    levels.push({ ...lv, src: f, naming });
    expected++;
  }
  console.log(`Loaded ${files.length} external levels from levels/`);
} else {
  console.log("No levels/ directory — auditing embedded levels only");
}

const T = { EMPTY:0, BRICK:1, SOLID:2, LADDER:3, BAR:4, TRAP:5, HLADDER:6, GOLD:7 };
const ROWS = Profile.rows, COLS = Profile.cols;

// simplified movement graph (matches prior attempts' static audits):
// walk/climb/fall/one-deep-dig edges; no guards, no hole timing
function reachable(model, exitRevealed) {
  const act = model.act.map((row, y) => row.map((t, x) => {
    if (model.base[y][x] === T.HLADDER) return exitRevealed ? T.LADDER : T.EMPTY;
    return t;
  }));
  const baseAt = (x, y) => (x < 0 || x >= COLS || y < 0 || y >= ROWS) ? T.SOLID : model.base[y][x];
  const actAt = (x, y) => (x < 0 || x >= COLS || y < 0 || y >= ROWS) ? T.SOLID : act[y][x];
  const solid = t => t === T.BRICK || t === T.SOLID;
  const blockedWalk = (x, y) => {
    const t = actAt(x, y);
    return solid(t) || t === T.TRAP;
  };
  const support = (x, y) => {
    const cur = actAt(x, y);
    if (cur === T.LADDER || cur === T.BAR) return true;
    if (y >= ROWS - 1) return true;
    const b = actAt(x, y + 1);
    return solid(b) || b === T.LADDER;
  };
  const start = model.runnerStart;
  const seen = new Set([start.x + "," + start.y]);
  const q = [[start.x, start.y]];
  const push = (x, y) => {
    if (x < 0 || x >= COLS || y < 0 || y >= ROWS) return;
    const k = x + "," + y;
    if (!seen.has(k)) { seen.add(k); q.push([x, y]); }
  };
  while (q.length) {
    const [x, y] = q.shift();
    if (!support(x, y)) {           // falling: only straight down
      if (!solid(actAt(x, y + 1))) push(x, y + 1);
      continue;
    }
    if (!blockedWalk(x - 1, y)) push(x - 1, y);
    if (!blockedWalk(x + 1, y)) push(x + 1, y);
    if (actAt(x, y) === T.LADDER && !blockedWalk(x, y - 1)) push(x, y - 1);
    if (!solid(actAt(x, y + 1))) push(x, y + 1);   // step/fall down (traps passable from above)
    // one-deep dig: stand here, dig sideways-below, drop into the pit
    for (const d of [-1, 1]) {
      if (actAt(x + d, y) === T.EMPTY && baseAt(x + d, y) !== T.GOLD &&
          actAt(x + d, y + 1) === T.BRICK && baseAt(x + d, y + 1) === T.BRICK)
        push(x + d, y + 1);
    }
  }
  return seen;
}

let failures = 0;
levels.forEach((lv, i) => {
  const problems = [...(lv.naming || [])];
  if (lv.map.length !== ROWS) problems.push(`rows=${lv.map.length}`);
  lv.map.forEach((r, y) => { if (r.length !== COLS) problems.push(`row ${y} len=${r.length}`); });
  const model = new LevelModel(lv);
  const runners = lv.map.join("").split("&").length - 1;
  if (runners !== 1) problems.push(`runner count=${runners}`);
  if (model.goldCount < 1) problems.push("no gold");
  const guardCount = model.guardStarts.length;
  if (guardCount < 1) problems.push("no guards");
  if (guardCount > Profile.maxGuards) problems.push(`too many guards (${guardCount})`);

  const phaseA = reachable(model, false);
  const golds = [];
  for (let y = 0; y < ROWS; y++)
    for (let x = 0; x < COLS; x++)
      if (model.base[y][x] === T.GOLD) golds.push([x, y]);
  const badGold = golds.filter(([x, y]) => !phaseA.has(x + "," + y));
  if (badGold.length) problems.push(`unreachable gold: ${badGold.map(g => g.join(",")).join(" ")}`);

  const phaseB = reachable(model, true);
  let topOk = false;
  for (let x = 0; x < COLS; x++) if (phaseB.has(x + ",0")) topOk = true;
  if (!topOk) problems.push("top row (exit) unreachable");

  const hasS = lv.map.join("").includes("S");
  if (!hasS) problems.push("no hidden exit ladder");

  const tag = lv.src && lv.src !== "embedded" ? ` [${lv.src}]` : "";
  if (problems.length) {
    failures++;
    console.log(`LEVEL ${i + 1} "${lv.name}"${tag} FAIL: ${problems.join("; ")}`);
  } else {
    console.log(`LEVEL ${i + 1} "${lv.name}"${tag} ok (gold=${golds.length} guards=${guardCount})`);
  }
});
console.log(failures ? `\n${failures} level(s) FAILED` : "\nAll levels passed");
process.exit(failures ? 1 : 0);
