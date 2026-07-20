// Guard/gold/pit behavior test: drives the real engine headlessly and asserts
// the classic (reference-faithful) pit physics — any dug hole pins a falling
// guard regardless of what is below, and carried gold is released while the
// guard is still falling in (reference AI v4):
//   A. pit with a hard floor below   -> guard traps, gold is force-released
//   B. open-bottomed pit, hole open  -> guard is pinned anyway: gold released
//                                       on the way in, trap score, climbs out
//   C. carried gold                  -> dropped mid-run after 12-37 crossings
//   D. hole refills while trapped    -> guard buried and respawns; gold was
//                                       already released above the hole
"use strict";
const fs = require("fs");
const vm = require("vm");
const html = fs.readFileSync(__dirname + "/runner.html", "utf8");
const src = html.match(/<script>([\s\S]*)<\/script>/)[1];
const noop = () => {};
const ctxStub = new Proxy({}, { get: (t, p) => (p === "canvas" ? {} : noop), set: () => true });
const sandbox = {
  console, window: {},
  document: { getElementById: () => ({ getContext: () => ctxStub }), body: { style: {} } },
  localStorage: { getItem: () => null, setItem: noop },
  performance: { now: () => 0 }, requestAnimationFrame: noop, addEventListener: noop,
};
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(src, sandbox, { filename: "runner.html" });
const get = expr => vm.runInContext(expr, sandbox);
const game = get("game");
const A = get("A"), T = get("T");
const registerLevelPack = get("registerLevelPack");
const campaignLevels = get("campaignLevels");

const pad = r => r.padEnd(28);
const empty = pad("");
const actorRow = pad("   0                &   $ S");   // guard x=3, runner x=20
const mk = (name, r13, r14, r15) => ({
  name,
  map: [empty, empty, empty, empty, empty, empty, empty, empty, empty, empty, empty,
        actorRow, pad("#".repeat(28)), pad(r13), pad(r14), pad(r15)],
});
registerLevelPack("guard-gold-test", [
  mk("T-SOLID", "@".repeat(28), "@".repeat(28), "@".repeat(28)),
  mk("T-PIERCED", "", "", "@".repeat(28)),
]);
game.levels = campaignLevels();
const SOLID = game.levels.findIndex(l => l.name === "T-SOLID");
const PIERCED = SOLID + 1;
const HOLE = { x: 5, y: 12 };

let failures = 0;
const check = (cond, what) => {
  console.log(`  ${cond ? "ok  " : "FAIL"} ${what}`);
  if (!cond) failures++;
};
const goldAboveHole = () => game.model.baseAt(HOLE.x, HOLE.y - 1) === T.GOLD;

// load a level, arm it, open a finished hole at (5,12), give the guard gold
function setup(idx) {
  game.loadLevel(idx);
  game.lives = 99;
  game.keyAction = A.LEFT; game.tick(); game.keyAction = A.STOP;
  game.model.act[HOLE.y][HOLE.x] = T.EMPTY;
  const hole = { x: HOLE.x, y: HOLE.y, phase: "open", t: 0, stage: 0, dir: 1 };
  game.holes.push(hole);
  const g = game.guards[0];
  g.hasGold = 30;
  return { g, hole };
}

console.log("A: pit with hard floor below -> trap + forced gold release");
{
  const { g } = setup(SOLID);
  const score0 = game.score;
  let trapped = false;
  for (let t = 0; t < 120 && !trapped; t++) {
    game.tick();
    trapped = g.action === A.INHOLE && g.yo === 0;
  }
  check(trapped, "guard is trapped in the hole");
  check(g.hasGold === 0, `carried gold released (hasGold=${g.hasGold})`);
  check(goldAboveHole(), "gold is back on the map above the hole");
  check(game.score - score0 === 75, `trap score awarded (+${game.score - score0})`);
}

console.log("B: open-bottomed pit, hole open -> guard pinned anyway, gold released while falling in");
{
  const { g } = setup(PIERCED);
  const score0 = game.score;
  let trapped = false, earlyRelease = false, fellThrough = false, climbed = false;
  for (let t = 0; t < 400 && !climbed; t++) {
    game.tick();
    if (!trapped && goldAboveHole() && g.yo < 0) earlyRelease = true;
    if (g.action === A.INHOLE && g.yo === 0) trapped = true;
    if (g.y > HOLE.y) fellThrough = true;
    if (g.action === A.CLIMB) climbed = true;
  }
  check(trapped, "guard trapped despite open space below the hole");
  check(!fellThrough, "guard never fell through the hole");
  check(earlyRelease, "gold released while the guard was still falling in");
  check(goldAboveHole(), "gold is on the map above the hole");
  check(g.hasGold === 0, `guard no longer carries gold (hasGold=${g.hasGold})`);
  check(game.score - score0 === 75, `trap score awarded (+${game.score - score0})`);
  check(climbed, "guard climbs out afterwards");
}

console.log("C: carried gold is dropped mid-run after 12-37 crossings");
{
  game.loadLevel(SOLID);
  game.lives = 99;
  game.keyAction = A.LEFT; game.tick(); game.keyAction = A.STOP;
  const g = game.guards[0], r = game.runner;
  game.model.base[11][8] = T.GOLD; game.model.goldCount++;
  let pickups = 0, drops = 0, dropOnMap = false, lastGold = 0;
  for (let t = 0; t < 1500 && drops < 1; t++) {
    if (Math.abs(g.x - r.x) < 5) { r.x = g.x < 14 ? 24 : 3; r.xo = 0; } // keep pacing
    game.tick();
    if (g.hasGold > 0 && lastGold <= 0) pickups++;
    if (g.hasGold === -1 && lastGold > 0) {
      drops++;
      dropOnMap = game.model.baseAt(g.x, g.y) === T.GOLD;
    }
    lastGold = g.hasGold;
  }
  check(pickups >= 1, `guard picked up gold (${pickups}x)`);
  check(drops >= 1, `guard dropped gold while running (${drops}x)`);
  check(dropOnMap, "dropped gold landed on the map");
}

console.log("D: hole refills while guard trapped -> gold already released, guard buried + respawns");
{
  const { g, hole } = setup(PIERCED);
  const score0 = game.score;
  let flipped = false, trapped = false, reborn = false;
  let goldAtTrap = -1, releasedAtTrap = false;
  for (let t = 0; t < 250 && !reborn; t++) {
    game.tick();
    if (!flipped && g.x === HOLE.x && g.y === HOLE.y) {
      hole.phase = "fill"; hole.t = 0; hole.stage = 0;   // pit starts closing
      flipped = true;
    }
    if (!trapped && g.action === A.INHOLE && g.yo === 0) {
      trapped = true;
      goldAtTrap = g.hasGold;
      releasedAtTrap = goldAboveHole();
    }
    if (g.action === A.REBORN) reborn = true;
  }
  check(flipped, "hole flipped to refill while guard was inside");
  check(trapped, "closing brick pinned the guard (trapped)");
  check(goldAtTrap === 0, `carried gold released on trap (hasGold=${goldAtTrap})`);
  check(releasedAtTrap, "gold is on the map above the hole");
  check(reborn, "guard was buried by the refill and respawned");
  check(game.score - score0 >= 75, "trap score awarded");
}

console.log(failures ? `\n${failures} check(s) FAILED` : "\nAll guard/gold checks passed");
process.exit(failures ? 1 : 0);
