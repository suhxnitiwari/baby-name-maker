// The worker's rules, checked without Cloudflare: node test.mjs
import assert from "node:assert/strict";
import worker, { checkLine } from "./lullabyte-ai.js";

const answer = content => ({ AI: { run: async () => ({ choices: [{ message: { content } }] }) } });
const call = (path, body, env, origin = "http://localhost:8792", ip = "1.1.1.1") => worker.fetch(new Request(`https://w.test${path}`, {
  method: "POST", headers: { Origin: origin, "Content-Type": "application/json", "CF-Connecting-IP": ip }, body: typeof body === "string" ? body : JSON.stringify(body) }), env);
let n = 0; const ok = (name, f) => f().then(() => { n++; console.log("ok   " + name); }, e => { console.log("FAIL " + name + "\n     " + e.message); process.exitCode = 1; });

await ok("reads a request into clean filters", async () => {
  const r = await (await call("/interpret", { text: "we love Layla and Maya, short, Arabic or Hindi roots, means light or moon" },
    answer('{"syl":[1,2],"origins":["Arabic","Hindi"],"meanings":["light","moon"],"like":["Layla","Maya","Zara"],"len":"huge","sql":"drop"}'))).json();
  assert.deepEqual(r.filters.syl, [1, 2]);
  assert.deepEqual(r.filters.like, ["Layla", "Maya"], "Zara was never written by the parent, so it can't come back");
  assert.equal(r.filters.len, undefined); assert.equal(r.filters.sql, undefined);
});
await ok("drops a gender the parent never mentioned", async () => {
  const r = await (await call("/interpret", { text: "something short, Irish" }, answer('{"gender":"either","syl":[1,2]}'))).json();
  assert.equal(r.filters.gender, undefined);
  const g = await (await call("/interpret", { text: "a short name for our daughter" }, answer('{"gender":"girl"}'))).json();
  assert.equal(g.filters.gender, "girl");
});
await ok("falls back to the plain reader when the model answers out of shape", async () => {
  const r = await (await call("/interpret", { text: "a girl, two syllables, Irish" }, answer("Sure! Here are some names: Aoife, Niamh"))).json();
  assert.equal(r.by, "reader"); assert.deepEqual(r.filters.syl, [2, 2]); assert.deepEqual(r.filters.origins, ["Irish"]);
});
await ok("keeps a line built from the facts", async () => {
  assert.ok(checkLine("Two soft syllables like Layla, and it means light.", { name: "Noor", meaning: "light", matched: ["two syllables"], near: [{ name: "Layla" }] }));
  assert.ok(checkLine("Arabic roots and short to spell.", { name: "Noor", origin: "Arabic", meaning: null }));
});
await ok("drops a name that isn't in the facts", async () => {
  assert.equal(checkLine("Like Isabella, it flows.", { name: "Noor", meaning: "light" }), null);
});
await ok("drops a meaning when none is on file", async () => {
  assert.equal(checkLine("It means star of the sea.", { name: "Mira", meaning: null }), null);
});
await ok("drops a meaning that isn't the one on file", async () => {
  assert.equal(checkLine('It means "gift of the moon".', { name: "Mira", meaning: "wonderful" }), null);
  assert.equal(checkLine("It means peaceful night.", { name: "Mira", meaning: "wonderful" }), null);
  assert.ok(checkLine("It means wonderful.", { name: "Mira", meaning: "wonderful, astonishing" }));
});
await ok("drops a loved name used as a loose comparison", async () => {
  const p = { name: "Tara", meaning: "star", matched: ["close to Maya in two syllables", "Indian roots"] };
  assert.equal(checkLine("Like Maya, Tara has Indian roots.", p), null);
  assert.ok(checkLine("Close to Maya in two syllables, it means star.", p));
});
await ok("drops filler, exclamations and emojis", async () => {
  for (const s of ["A perfect blend of both.", "So pretty!", "Soft and short ✨"]) assert.equal(checkLine(s, { name: "Noor", meaning: null }), null, s);
});
await ok("explain returns null for every line that broke a rule", async () => {
  const r = await (await call("/explain", { mode: "find", wish: "short", picks: [{ name: "Noor", meaning: "light", matched: ["short"] }, { name: "Mira", meaning: null }] },
    answer('{"reasons":["Short, and it means light.","Mira means ocean, like Marina."]}'))).json();
  assert.equal(r.reasons[0], "Short, and it means light."); assert.equal(r.reasons[1], null);
});
await ok("caps the request size", async () => {
  assert.equal((await call("/interpret", JSON.stringify({ text: "x".repeat(9000) }), answer("{}"))).status, 413);
  let seen = 0;
  const env = { AI: { run: async (m, o) => { seen = o.messages[1].content.length; return { choices: [{ message: { content: "{}" } }] }; } } };
  await call("/interpret", { text: "y".repeat(2000) }, env);
  assert.ok(seen <= 400 + 20, "only 400 characters reach the model");
});
await ok("only Lullabyte's own pages can call it", async () => {
  assert.equal((await call("/interpret", { text: "short" }, answer("{}"), "https://evil.example")).status, 403);
  assert.equal((await call("/interpret", { text: "short" }, answer("{}"), "https://suhxnitiwari.github.io")).status, 200);
});
await ok("rests after 40 calls in ten minutes", async () => {
  let last;
  for (let i = 0; i < 41; i++) last = await call("/interpret", { text: "short" }, answer("{}"), undefined, "9.9.9.9");
  assert.equal(last.status, 429);
});
console.log(`\n${n} checks passed`);
