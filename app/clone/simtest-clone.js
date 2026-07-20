// Dynamic smoke test: drive the real Game logic headlessly for many ticks.
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
vm.runInContext(src, sandbox, { filename: "clone.html" });
const { game, Profile } = sandbox.CloneGame;
const A = { STOP:0, LEFT:1, RIGHT:2, UP:3, DOWN:4 };

let errors = 0;
const step = (n, action) => {
  if (action !== undefined) game.keyAction = action;
  for (let i = 0; i < n; i++) {
    try { game.tick(); }
    catch (e) { console.error("tick threw:", e.message); errors++; return; }
  }
};

for (let lv = 0; lv < game.levels.length; lv++) {
  game.loadLevel(lv);
  game.lives = 99;
  const acts = [A.RIGHT, A.LEFT, A.UP, A.DOWN, A.RIGHT, A.UP, A.LEFT, A.DOWN];
  step(1, A.RIGHT);                 // leave ready state
  let digs = 0;
  for (let round = 0; round < 60 && !errors; round++) {
    step(20, acts[round % acts.length]);
    // opportunistic digging to exercise DigSystem
    if (game.state === "running" && !game.digging) {
      for (const d of [-1, 1]) if (game.canDig(d)) { game.startDig(d); digs++; break; }
      if (game.digging) step(30, A.STOP);
    }
    if (game.state === "dead") step(Profile.tickHz + 2, A.STOP); // let it respawn
    if (game.state === "over" || game.state === "win") break;
  }
  const gs = game.guards.map(g => `${g.x},${g.y}`).join(" ");
  console.log(`level ${lv + 1}: state=${game.state} score=${game.score} holesLive=${game.holes.length} digs=${digs} guards=[${gs}]`);
}

// guard pursuit sanity on level 1: guard should approach the runner over time
game.loadLevel(0); game.lives = 99;
const g0 = game.guards[0];
const d0 = Math.abs(g0.x - game.runner.x) + Math.abs(g0.y - game.runner.y);
step(1, A.RIGHT); step(150, A.STOP);
const d1 = Math.abs(g0.x - game.runner.x) + Math.abs(g0.y - game.runner.y);
console.log(`pursuit: initial distance ${d0}, after 150 ticks ${d1}`);
if (d1 >= d0) { console.error("FAIL: guard did not approach runner"); errors++; }

console.log(errors ? `\n${errors} error(s)` : "\nDynamic smoke test passed");
process.exit(errors ? 1 : 0);
