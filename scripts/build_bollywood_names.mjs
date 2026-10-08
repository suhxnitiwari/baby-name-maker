// Bollywood first names → data/bollywood-names.json, from the Bollywood Receipts guest list (../bollywood-receipts).
// Every person there was hand-checked onto the board (film credits from Wikidata, CC0). For each first name, the best-known
// bearers (by their size on the board) with what they do, from their film credits, and the year their films begin.
// The site only adds this line to a name it already knows ("In Bollywood: Varun Dhawan, actor, films since 2012"); being a
// star's name says nothing about where a name comes from or who it is for, so it never sets an origin or a sex.
// node scripts/build_bollywood_names.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const BR = path.join(ROOT, "..", "bollywood-receipts", "assets");
global.window = {};
eval(fs.readFileSync(path.join(BR, "world-data.js"), "utf8"));
const people = window.WORLD.people;
const W = eval("(" + fs.readFileSync(path.join(BR, "wd.js"), "utf8").match(/const W=(\{.*?\});\s*\n/s)[1] + ")");

// what each person does: their most frequent credit across the films on file
const roles = new Map(), add = (n, r) => { const m = roles.get(n) || roles.set(n, new Map()).get(n); m.set(r, (m.get(r) || 0) + 1); };
for (const [, , , f] of W.films) {
  for (const c of f.cast || []) add(c, "actor");
  for (const [c, r] of f.crew || []) add(c, r);
}
for (const f of Object.values(W.merge)) {
  for (const c of f.cast || []) add(c, "actor");
  for (const [c, r] of f.crew || []) add(c, r);
}
const WORD = { actor: "actor", director: "director", producer: "producer", composer: "composer", writer: "writer", screenwriter: "writer",
  cinematographer: "cinematographer", lyricist: "lyricist", singer: "singer", "playback singer": "singer", editor: "editor", choreographer: "choreographer" };
const roleOf = n => { const m = roles.get(n); if (!m) return ""; const [r] = [...m].sort((a, b) => b[1] - a[1])[0]; return WORD[r] || ""; };

const first = n => n.replace(/^(Dr|Mr|Mrs|Ms)\.? /, "").split(" ").find(w => w.length > 1 && !w.includes(".")) || "";
const byFirst = new Map();
for (const p of people) {
  const f = first(p.n);
  if (!f || !/^\p{Lu}\p{Ll}+$/u.test(f)) continue;           // a real first name, not initials or a single-name stage title in capitals
  if (/^Shah Rukh\b/.test(p.n)) continue;                    // Shah Rukh is one first name in two words, not "Shah"
  (byFirst.get(f) || byFirst.set(f, []).get(f)).push(p);
}
const rows = [];
for (const [f, ps] of byFirst) {
  ps.sort((a, b) => b.s - a.s);
  const [top, ...rest] = ps;
  const what = [roleOf(top.n), top.yr ? `films since ${top.yr}` : ""].filter(Boolean).join(", ");
  const also = rest.slice(0, 2).map(p => p.n);
  const line = `In Bollywood: ${top.n}${what ? `, ${what}` : ""}${also.length ? `; also ${also.join(" and ")}` : ""}. (Bollywood Receipts; film credits from Wikidata)`;
  rows.push([f, "", "", "", "", "", line, "", "real", []]);
}
rows.sort((a, b) => a[0].localeCompare(b[0]));
fs.writeFileSync(path.join(ROOT, "data", "bollywood-names.json"), JSON.stringify(rows));
console.log(`${rows.length} first names → data/bollywood-names.json`);
for (const r of rows.filter(r => ["Varun", "Deepika", "Ranveer", "Alia", "Shah", "Priyanka", "Kareena"].includes(r[0]))) console.log(" ", r[6]);
