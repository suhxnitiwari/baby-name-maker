// ─────────────────────────────────────────────────────────────
// MOM + DAD COMPILER
// Not halves glued together. Each parent's name is split into syllables (SU·HA·NI, KA·PIL);
//  · new names are built from syllables of both, in any order and from any position (NI·KA, HA·NI·KA, KA·HA·NI)
//  · real names are found by SOUND: any real name whose syllables sound like one of Mom's and one of Dad's (A·NI·KA)
//  · every candidate is scored on how well its melody bridges both parents' melodies (the notes it shares with each)
// Every name shows which syllables came from whom. Uses globals from app.js.
// ─────────────────────────────────────────────────────────────
let locks = { start: "", end: "" };
const capW = s => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
const COMMON_ENDINGS = { girl: "a ia ya na ra la ira ina ana ika iya elle", boy: "an en on ar el ir av ansh esh ian o", either: "i y en an ar el is o" };

// 1. Splice two names at syllable-ish cut points, remembering which letters came from where.
function cutsOf(w) {
  const c = [];
  for (let i = 2; i < w.length - 1; i++) if (/[aeiouy]/i.test(w[i - 1]) || /[aeiouy]/i.test(w[i])) c.push(i);
  return c.length ? c : [Math.ceil(w.length / 2)];
}
// 1. Syllables, and what they sound like (spelling aside: Ca = Ka, Pha = Fa)
function syllablesOf(name) {
  const { w, syl } = MB.syllables(name);
  return syl.map((x, i) => ({ t: w.slice(x.s, x.e), core: w.slice(x.s, x.ne), s: x.s, e: x.e, on: x.on, nuc: x.nuc, co: x.co, i, n: syl.length }));
}
const vowelClass = v => /^(ai|ay|ei|ey|ae)/.test(v) ? "A" : /^(oi|oy)/.test(v) ? "O" : /^(oo|ou|u|ew)/.test(v) ? "u" : /^(ee|ea|ie|i|y)/.test(v) ? "i" : /^(au|aw)/.test(v) || v[0] === "o" ? "o" : v[0] === "e" ? "e" : "a";
const onsetKey = on => (on.replace(/^h(?=.)/, "").replace(/ph/g, "f").replace(/^c(?=[eiy])/, "s").replace(/ck|c|q/g, "k").replace(/z/g, "s").replace(/([kgtdbp])h/g, "$1") || "-");
const sylKey = x => onsetKey(x.on) + vowelClass(x.nuc);
// a name's notes (comb teeth), for the melody bridge
const teethOf = n => MB.melody(n).ev.filter(e => e.kind === "main").map(e => e.i);
function bridgeOf(n, a, b) {
  const t = teethOf(n), A = new Set(teethOf(a)), B = new Set(teethOf(b));
  if (!t.length) return { score: 0, a: [], b: [] };
  const fromA = t.filter(x => A.has(x)), fromB = t.filter(x => B.has(x));
  const sa = fromA.length / t.length, sb = fromB.length / t.length;
  // it has to echo both: the weaker side counts most
  return { score: Math.min(sa, sb) * .7 + (sa + sb) / 2 * .3, a: [...new Set(fromA)].map(i => MB.NOTE_NAMES[i]), b: [...new Set(fromB)].map(i => MB.NOTE_NAMES[i]) };
}

// 2. New names from both parents' syllables, any order. A syllable that isn't last can drop its closing consonant (PIL → PI).
function syllableBlends(names) {
  const P = names.map(n => ({ n, syl: syllablesOf(n) })), out = [];
  const units = P.flatMap((p, pi) => p.syl.map(x => ({ ...x, pi, from: p.n })));
  const text = (u, last) => last ? u.t : u.core;
  const build = seq => {
    let n = "", segs = [];
    seq.forEach((u, k) => {
      const piece = text(u, k === seq.length - 1);
      const glued = join([n || "", piece].filter(Boolean));
      const at = glued.length - piece.length;
      segs.push({ from: u.from, s: u.s, e: u.s + piece.length, at: Math.max(0, at) });
      n = glued;
    });
    return { n: capW(n), segs, seq };
  };
  // every name carries at least one syllable of Mom's (0) and one of Dad's (1); a family name can add a third
  const both = seq => seq.some(u => u.pi === 0) && seq.some(u => u.pi === 1);
  for (const u of units) for (const v of units) {
    if (u === v) continue;
    if (both([u, v])) out.push(build([u, v]));
    for (const x of units) {
      if (x === u || x === v) continue;
      const ps = new Set([u.pi, v.pi, x.pi]);
      if (!(ps.has(0) && ps.has(1))) continue;
      out.push(build([u, v, x]));
    }
  }
  return out.map(c => {
    // a straight "front of one + back of the other" join is the least imaginative kind
    const [f, l] = [c.seq[0], c.seq[c.seq.length - 1]];
    const plain = c.seq.length === 2 && f.i === 0 && l.i === l.n - 1;
    const where = c.seq.map(u => `${u.t.toUpperCase()} (${u.from})`).join(" + ");
    return { n: c.n, segs: c.segs, method: `syllables: ${where}`, novelty: plain ? .45 : 1 };
  });
}

// 3. Real names that sound like both parents: syllable by syllable, by sound, in any order
function soundsLikeBoth(name, A, B) {
  const syl = syllablesOf(name);
  if (syl.length < 2) return null;
  const keysA = new Map(A.map(x => [sylKey(x), x])), keysB = new Map(B.map(x => [sylKey(x), x]));
  const hits = []; let gotA = false, gotB = false;
  for (const x of syl) {
    const k = sylKey(x), ha = keysA.get(k), hb = keysB.get(k);
    const h = ha && (!hb || !gotA) ? ["a", ha] : hb ? ["b", hb] : null;
    if (!h) continue;
    if (h[0] === "a") gotA = true; else gotB = true;
    hits.push({ who: h[0], p: h[1], c: x });
  }
  // both parents, and at most one syllable that belongs to neither
  if (!gotA || !gotB || syl.length - hits.length > 1) return null;
  return hits;
}
// Lock-driven builds: keep a locked start (or end) and attach pieces of every family name.
function lockBuilds(names) {
  const out = [], ends = COMMON_ENDINGS[gender].split(" ");
  if (locks.start) {
    for (const y of names) for (const j of cutsOf(y)) out.push({ n: capW(locks.start + y.slice(j)), segs: [{ lock: locks.start }, { from: y, s: j, e: y.length }], method: "locked start" });
    for (const e of ends) out.push({ n: capW(locks.start + e), segs: [{ lock: locks.start }, { add: e }], method: "locked start" });
  }
  if (locks.end) {
    for (const x of names) for (const i of cutsOf(x)) out.push({ n: capW(x.slice(0, i) + locks.end), segs: [{ from: x, s: 0, e: i }, { lock: locks.end }], method: "locked end" });
  }
  return out;
}

// 2. Find where a parent's letters appear inside a real name (longest shared run, ≥ 2 letters).
function sharedRun(name, parent, used) {
  const N = fold(name), P = fold(parent);
  let best = null;
  for (let i = 0; i < N.length; i++) for (let j = 0; j < P.length; j++) {
    let k = 0;
    while (i + k < N.length && j + k < P.length && N[i + k] === P[j + k] && !used[i + k]) k++;
    if (k >= 2 && (!best || k > best.len)) best = { i, j, len: k };
  }
  return best;
}
function carryBoth(name, a, b) {
  const tryOrder = (p, q) => {
    const used = []; const r1 = sharedRun(name, p, used); if (!r1) return null;
    for (let k = 0; k < r1.len; k++) used[r1.i + k] = true;
    const r2 = sharedRun(name, q, used); if (!r2) return null;
    return [[p, r1], [q, r2]];
  };
  const opts = [tryOrder(a, b), tryOrder(b, a)].filter(Boolean);
  if (!opts.length) return null;
  const best = opts.sort((x, y) => (y[0][1].len + y[1][1].len) - (x[0][1].len + x[1][1].len))[0];
  // a real "chunk" from the parents, not just a shared "an": 5+ letters total, one piece of 3+
  const l1 = best[0][1].len, l2 = best[1][1].len, cover = (l1 + l2) / fold(name).length;
  return cover >= .6 && l1 + l2 >= 5 && Math.max(l1, l2) >= 3 ? best : null;
}

// 3. Scores (heuristics, labeled as such in the UI).
function ease(n) {
  const w = fold(n);
  let s = sayable(n) ? 1 : .55;
  s -= ((w.match(/[^aeiouy]{2,}/g) || []).length) * .08;
  s -= (w.match(/[qxz]/g) || []).length * .06;
  if (w.length > 8) s -= (w.length - 8) * .06;
  return Math.max(0, Math.min(1, s));
}
const lengthFit = n => { const l = fold(n).length; return l >= 4 && l <= 7 ? 1 : l === 3 || l === 8 ? .8 : .55; };
function genderFit(n) {
  const w = fold(n);
  return gender === "girl" ? (/[aiey]$/.test(w) ? 1 : .6) : gender === "boy" ? (/[^aeiy]$/.test(w) ? 1 : .6) : .8;
}

// 4. Attestation from our list + official records
function attestation(n) {
  const known = BY_NAME.get(fold(n)), e = dbEntry(n);
  if (!known && e) return { badge: e.cnt >= 500 ? "Real name" : "Rare real name", obj: Object.assign({}, e, { g: e.g || gender }), rank: Math.round(1e7 / (e.cnt + 1)) };
  const ranks = popRanks(n, gender);
  if (known && known.length) {
    const obj = known.find(genderOk) || known[0];
    const badge = obj.type === "root" && !ranks.length ? "Built from roots" : "Real name";
    return { badge, obj, rank: ranks[0] ? ranks[0][1] : 99999 };
  }
  if (ranks.length) return { badge: ranks[0][1] > 1000 ? "Rare real name" : "Real name", obj: null, rank: ranks[0][1] };
  return null;
}
// e.g. "Anand" shows up in some girls' records but is overwhelmingly a boy's name
function mostlyOtherGender(n, sx) {
  const other = sx === "g" ? "b" : "g";
  let mine = 99999, theirs = 99999;
  for (const c of POP.countries) {
    const a = POP.lookup[c.key][`${sx}:${n}`], b = POP.lookup[c.key][`${other}:${n}`];
    if (a) mine = Math.min(mine, a[0]); if (b) theirs = Math.min(theirs, b[0]);
  }
  return theirs * 5 < mine;
}
function attestedPool() {
  const pool = new Map();
  [...REAL, ...ROOT_NAMES].filter(genderOk).forEach(x => pool.set(fold(x.n), x.n));
  // every real name in the official database for this gender (single-word names that 20+ people have)
  if (DB_READY) { for (const e of DB) if (e.g && genderOk(e) && e.cnt >= 20 && !e.n.includes(" ")) pool.set(fold(e.n), e.n); return [...pool.values()]; }
  if (POP) {
    const sx = gender === "either" ? null : gender[0];
    for (const c of POP.countries) for (const key of Object.keys(POP.lookup[c.key])) {
      const [s, n] = key.split(":"); if (sx && s !== sx) continue;
      if (sx && mostlyOtherGender(n, sx)) continue;
      if (!pool.has(fold(n))) pool.set(fold(n), n.split("-").map(capW).join("-"));
    }
  }
  return [...pool.values()];
}

// 5. Compile
// fam: { a, b, extra: [names to honor], honor: .5 | 1, mode: "both" | "real" | "new" }, f: the same filters as Find, last: surname
function blend(fam, f, last = "") {
  const a = capW(fam.a), b = capW(fam.b), extra = (fam.extra || []).map(capW), names = [a, b, ...extra];
  fam = { honor: .5, mode: "both", ...fam, extra };
  const log = [];
  const parentSet = new Set(names.map(fold));

  // synthesize
  let raw = [];
  if (fam.mode !== "real") {
    raw.push(...syllableBlends(names), ...lockBuilds(names));
    log.push([`recombining syllables of ${names.map(n => syllablesOf(n).map(x => x.t.toUpperCase()).join("·")).join(" × ")}`, `${raw.length.toLocaleString()} candidates`]);
    const seen = new Set();
    // no duplicates, and nothing that just is (or contains) a parent's whole name
    const dedup = raw.filter(c => { const k = fold(c.n); if (seen.has(k) || [...parentSet].some(p => k.includes(p) || soundKey(k) === soundKey(p))) return false; seen.add(k); return true; });
    log.push(["removing duplicates & copies of parents", `−${(raw.length - dedup.length).toLocaleString()}`]);
    raw = dedup.filter(c => sayable(c.n));
    log.push(["removing hard-to-say clusters", `−${(dedup.length - raw.length).toLocaleString()}`]);
  }
  // scan real names
  let real = [];
  if (fam.mode !== "new") {
    const pool = attestedPool(), A = syllablesOf(a), B = syllablesOf(b);
    // quick prefilter: the name must contain the sound-core of one of Mom's syllables and one of Dad's
    const cores = arr => [...new Set(arr.map(x => onsetKey(x.on).replace("-", "") + x.nuc[0]).filter(c => c.length >= 2))];
    const cA = cores(A), cB = cores(B);
    const norm = w => w.replace(/ph/g, "f").replace(/c(?=[eiy])/g, "s").replace(/ck|c|q/g, "k").replace(/z/g, "s").replace(/([kgtdbp])h/g, "$1");
    for (const n of pool) {
      const w = fold(n), nw = norm(w);
      if (parentSet.has(w) || !cA.some(c => nw.includes(c)) || !cB.some(c => nw.includes(c)) || wrongGender(n)) continue;
      const hits = soundsLikeBoth(n, A, B);
      if (hits) { real.push({ n, hits, method: "real name" }); continue; }
      const hit = carryBoth(n, a, b);
      if (hit) real.push({ n, hit, method: "real name" });
    }
    log.push([`listening to ${pool.length.toLocaleString()} real names for a syllable of each parent`, `${real.length} sound like both`]);
  }

  // build candidate objects
  const synthKeys = new Set();
  let cands = [];
  for (const c of raw) {
    if (wrongGender(c.n)) continue;
    const att = attestation(c.n);
    synthKeys.add(fold(c.n));
    cands.push(Object.assign(makeCand(c.n, c.segs, c.method, att, names), { novelty: c.novelty ?? 1 }));
  }
  for (const r of real) {
    if (synthKeys.has(fold(r.n))) continue;
    if (r.hits) {
      const segs = r.hits.map(h => ({ from: h.who === "a" ? a : b, s: h.p.s, e: h.p.e, at: h.c.s, len: h.c.e - h.c.s }));
      const said = r.hits.map(h => `${h.c.t.toUpperCase()} like ${h.p.t.toUpperCase()} (${h.who === "a" ? a : b})`).join(", ");
      cands.push(makeCand(r.n, segs, `a real name that sings ${said}`, attestation(r.n), names));
    } else {
      const segs = r.hit.map(([p, h]) => ({ from: p, s: h.j, e: h.j + h.len, at: h.i }));
      cands.push(makeCand(r.n, segs, "a real name carrying both parents' letters", attestation(r.n), names));
    }
  }
  const attestedN = cands.filter(c => c.badge === "Real name" || c.badge === "Rare real name").length;
  log.push(["checking official records & name list", `${attestedN} are real names`]);

  // filters
  const before = cands.length, unfiltered = cands;
  cands = cands.filter(x => lenOk(x.n, f.len) && (!f.vibe || vibeMatch(x, f.vibe)) &&
    (!locks.start || fold(x.n).startsWith(fold(locks.start))) && (!locks.end || fold(x.n).endsWith(fold(locks.end))) &&
    (!(f.theme || f.religion || f.culture || f.lang) || x.type !== "invented" && matches(x, f, false)));
  if (before !== cands.length) log.push(["applying your filters & locks", `−${(before - cands.length).toLocaleString()}`]);
  // every duet gets an answer: if nothing fits every blank, keep the locks and let the other filters go
  if (!cands.length && before) {
    cands = unfiltered.filter(x => (!locks.start || fold(x.n).startsWith(fold(locks.start))) && (!locks.end || fold(x.n).endsWith(fold(locks.end))));
    if (!cands.length) cands = unfiltered;
    log.push(["nothing fit every blank, so the closest are shown", `${cands.length.toLocaleString()} kept`]);
  }
  if (last) {
    const flagged = cands.filter(x => !flowCheck(x.n, last).ok).length;
    log.push([`testing with surname ${last}`, `${flagged} flagged`]);
  }

  // score
  for (const x of cands) {
    const cA = x.contrib[0] || 0, cB = x.contrib[1] || 0;
    const ex = x.contrib.slice(2).reduce((s, v) => s + v, 0);
    const balance = 1 - Math.abs(cA - cB) / Math.max(cA + cB, .01);
    const coverage = Math.min(1, cA + cB + ex * fam.honor);
    const flow = last ? (flowCheck(x.n, last).ok ? 1 : .45) : .8;
    // real-name evidence grows with how many people actually have it (a name held by 20,000 counts more than one held by 20)
    const held = (dbEntry(x.n) || {}).cnt || 0, story = (BY_NAME.get(fold(x.n)) || []).some(y => y.m);
    const att = x.badge === "New blend" ? .62 : x.badge === "Built from roots" ? .8 : Math.min(1, .45 + .4 * Math.min(1, Math.log10(held + 1) / 4.3) + (story ? .15 : 0));
    const br = bridgeOf(x.n, a, b);
    x.bridge = br;
    x.parts = { balance, coverage, bridge: br.score, ease: ease(x.n), flow, att, len: lengthFit(x.n), gfit: genderFit(x.n), novelty: x.novelty ?? 1 };
    x.score = 100 * (.18 * br.score + .13 * balance + .08 * coverage + .12 * x.parts.ease + .07 * flow + .2 * att + .05 * x.parts.len + .09 * x.parts.gfit + .08 * x.parts.novelty) + (ex ? 2 * fam.honor : 0);
  }
  cands.sort((p, q) => q.score - p.score);
  log.push(["ranking by melody bridge, balance, real-name evidence, ease", `${cands.length.toLocaleString()} survived`]);
  if (!cands.length) return { picks: [], rest: [], log, total: 0 };

  // top picks (each a different objective)
  const picks = [], used = new Set(), top = cands.slice(0, Math.max(10, Math.ceil(cands.length * .4)));
  // each category takes its best name that no earlier category already claimed
  const pick = (label, list) => { const x = list.find(c => !used.has(c.n)); if (x) { used.add(x.n); picks.push(Object.assign(Object.create(x), x, { pick: label })); } };
  pick("Best overall", cands);
  pick("Most musical", [...top].sort((p, q) => q.parts.bridge - p.parts.bridge || q.score - p.score));
  pick("Most equal blend", [...top].filter(x => x.badge === "New blend").sort((p, q) => q.parts.balance - p.parts.balance || q.score - p.score));
  const isReal = x => x.badge === "Real name" || x.badge === "Rare real name";
  // real-name picks favor names typical for the chosen gender (official records include some cross-gender use)
  pick("Best real name", cands.filter(isReal).sort((p, q) => q.score * q.parts.gfit - p.score * p.parts.gfit));
  pick("Rarest real name", [...top].filter(x => isReal(x) && x.parts.gfit === 1).sort((p, q) => q.rank - p.rank));
  pick("Easiest to say", [...top].sort((p, q) => q.parts.ease - p.parts.ease || q.score - p.score));
  if (last) pick(`Best with ${last}`, [...top].sort((p, q) => flowCheck(q.n, last).good.length - flowCheck(p.n, last).good.length || q.score - p.score));
  if (fam.extra.length) pick(`Best honoring ${fam.extra.join(" & ")}`, cands.filter(x => x.contrib.slice(2).some(v => v > 0)));
  pick("Wildcard", shuffle(top.filter(x => x.badge === "New blend")));
  picks[0].featured = true;

  const rest = cands.filter(x => !used.has(x.n)).slice(0, 40);
  log.push(["showing", `${picks.length} top picks + ${rest.length} more`]);
  return { picks, rest, log, total: cands.length };
}

function makeCand(n, segs, method, att, names) {
  // contribution = share of the new name's letters that came from each family name
  const L = fold(n).length || 1;
  const contrib = names.map(p => Math.min(1, segs.filter(s => s.from === p).reduce((t, s) => t + (s.len ?? s.e - s.s), 0) / L));
  const base = att && att.obj ? att.obj : { n, g: gender, o: "", l: "", r: [], m: "", src: "", type: att ? "attested" : "invented" };
  return Object.assign(Object.create(base), base, {
    n, prov: { segs, method, names }, contrib, badge: att ? att.badge : "New blend", rank: att ? att.rank : 99999,
  });
}

// 6. Provenance: which letters came from whom
function provHTML(x) {
  const { segs, method, names } = x.prov;
  const rows = names.map((p, i) => {
    const mine = segs.filter(s => s.from === p);
    if (!mine.length) return "";
    let html = "", k = 0;
    for (const s of [...mine].sort((u, v) => u.s - v.s)) { html += esc(p.slice(k, s.s)) + `<mark>${esc(p.slice(s.s, s.e))}</mark>`; k = s.e; }
    html += esc(p.slice(k));
    const who = i === 0 ? "Mom" : i === 1 ? "Dad" : "Family";
    return `<div class="prow p${i < 2 ? i : 2}"><span class="pl">${who}</span><span class="pw">${html}</span><b>${Math.round(x.contrib[i] * 100)}%</b></div>`;
  }).join("");
  const lockSeg = segs.find(s => s.lock), addSeg = segs.find(s => s.add);
  const pieces = segs.map(s => s.lock ? s.lock : s.add ? `+${s.add}` : s.from.slice(s.s, s.e)).join(" + ");
  const first = segs[0], lastSeg = segs[segs.length - 1];
  const startPiece = first.lock || first.add || (first.from && first.from.slice(first.s, first.e));
  const endPiece = lastSeg.lock || lastSeg.add || (lastSeg.from && lastSeg.from.slice(lastSeg.s, lastSeg.e));
  const canLock = x.badge === "New blend" || method.startsWith("syllables") || method.startsWith("locked");
  return `<div class="prov">
    ${rows}
    ${lockSeg || addSeg ? `<div class="prow"><span class="pl">${lockSeg ? "Kept" : "Added"}</span><span class="pw"><mark>${esc((lockSeg || addSeg).lock || (lockSeg || addSeg).add)}</mark></span><b></b></div>` : ""}
    <div class="pmethod">${method.startsWith("locked") ? `built around what you kept: ${esc(pieces)} → ${esc(x.n)}` : esc(method)}</div>
    ${x.bridge && (x.bridge.a.length || x.bridge.b.length) ? `<div class="pmethod">its melody borrows ${esc(x.bridge.a.join(", ") || "nothing")} from ${esc(names[0])} and ${esc(x.bridge.b.join(", ") || "nothing")} from ${esc(names[1])}</div>` : ""}
    ${canLock ? `<div class="locks"><button data-lock-start="${esc(startPiece)}">keep “${esc(startPiece)}…”</button><button data-lock-end="${esc(endPiece)}">keep “…${esc(endPiece)}”</button></div>` : ""}
  </div>`;
}
