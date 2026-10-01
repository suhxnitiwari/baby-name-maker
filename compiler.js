// ─────────────────────────────────────────────────────────────
// MOM + DAD COMPILER
// family inputs → splice + scan real names → validate → test with surname → rank → top picks
// Every name shows where its letters came from. Uses globals from index.html.
// ─────────────────────────────────────────────────────────────
let locks = { start: "", end: "" };
const capW = s => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
const COMMON_ENDINGS = { girl: "a ia ya na ra la ira ina ana ika iya elle", boy: "an en on ar el ir av ansh esh ian o", either: "i y en an ar el is o" };

function familyInputs() {
  const a = $("#mom").value.trim(), b = $("#dad").value.trim();
  const extra = $("#familyIn").value.split(/[,;]+|\s+/).map(t => t.trim()).filter(t => /^[\p{L}'-]{2,}$/u.test(t)).map(capW);
  return { a: capW(a), b: capW(b), extra, honor: +$("#honor").value, mode: $("#synthMode").value };
}

// 1. Splice two names at syllable-ish cut points, remembering which letters came from where.
function cutsOf(w) {
  const c = [];
  for (let i = 2; i < w.length - 1; i++) if (/[aeiouy]/i.test(w[i - 1]) || /[aeiouy]/i.test(w[i])) c.push(i);
  return c.length ? c : [Math.ceil(w.length / 2)];
}
function splices(x, y) {
  const out = [];
  for (const i of cutsOf(x)) for (const j of cutsOf(y)) {
    if (x[i - 1].toLowerCase() === y[j].toLowerCase()) continue;
    out.push({ n: capW(x.slice(0, i) + y.slice(j)), segs: [{ from: x, s: 0, e: i }, { from: y, s: j, e: y.length }], method: "splice" });
  }
  return out;
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
  const known = BY_NAME.get(fold(n));
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
function blend() {
  const fam = familyInputs(), { a, b } = fam;
  $("#more").classList.add("hidden");
  renderLocks();
  if (!a || !b) { $("#count").textContent = ""; return render([], "Type Mom's and Dad's names, then tap Generate names 💞"); }
  const f = filters(), last = lastName(), names = [a, b, ...fam.extra];
  const log = [];
  const parentSet = new Set(names.map(fold));

  // synthesize
  let raw = [];
  if (fam.mode !== "real") {
    for (let p = 0; p < names.length; p++) for (let q = 0; q < names.length; q++) if (p !== q) raw.push(...splices(names[p], names[q]));
    raw.push(...lockBuilds(names));
    log.push([`splicing ${names.join(" × ")}`, `${raw.length.toLocaleString()} candidates`]);
    const seen = new Set();
    const dedup = raw.filter(c => { const k = fold(c.n); if (seen.has(k) || parentSet.has(k)) return false; seen.add(k); return true; });
    log.push(["removing duplicates & copies of parents", `−${(raw.length - dedup.length).toLocaleString()}`]);
    raw = dedup.filter(c => sayable(c.n));
    log.push(["removing hard-to-say clusters", `−${(dedup.length - raw.length).toLocaleString()}`]);
  }
  // scan real names
  let real = [];
  if (fam.mode !== "new") {
    const pool = attestedPool();
    for (const n of pool) {
      if (parentSet.has(fold(n))) continue;
      const hit = carryBoth(n, a, b);
      if (hit) real.push({ n, hit, method: "real name" });
    }
    log.push([`scanning ${pool.length.toLocaleString()} real names for both parents' sounds`, `${real.length} carry both`]);
  }

  // build candidate objects
  const synthKeys = new Set();
  let cands = [];
  for (const c of raw) {
    const att = attestation(c.n);
    synthKeys.add(fold(c.n));
    cands.push(makeCand(c.n, c.segs, c.method, att, names));
  }
  for (const r of real) {
    if (synthKeys.has(fold(r.n))) continue;
    const segs = r.hit.map(([p, h]) => ({ from: p, s: h.j, e: h.j + h.len, at: h.i }));
    cands.push(makeCand(r.n, segs, "real name carrying both parents' sounds", attestation(r.n), names));
  }
  const attestedN = cands.filter(c => c.badge === "Real name" || c.badge === "Rare real name").length;
  log.push(["checking official records & name list", `${attestedN} are real names`]);

  // filters
  const before = cands.length;
  cands = cands.filter(x => lenOk(x.n, f.len) && (!f.vibe || vibeMatch(x, f.vibe)) &&
    (!locks.start || fold(x.n).startsWith(fold(locks.start))) && (!locks.end || fold(x.n).endsWith(fold(locks.end))) &&
    (!(f.theme || f.religion || f.culture || f.lang) || x.type !== "invented" && matches(x, f, false)));
  if (before !== cands.length) log.push(["applying your filters & locks", `−${(before - cands.length).toLocaleString()}`]);
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
    const att = x.badge === "Real name" ? 1 : x.badge === "Rare real name" ? .92 : x.badge === "Built from roots" ? .85 : .72;
    x.parts = { balance, coverage, ease: ease(x.n), flow, att, len: lengthFit(x.n), gfit: genderFit(x.n) };
    x.score = 100 * (.2 * balance + .18 * coverage + .18 * x.parts.ease + .12 * flow + .14 * att + .08 * x.parts.len + .1 * x.parts.gfit) + (ex ? 2 * fam.honor : 0);
  }
  cands.sort((p, q) => q.score - p.score);
  log.push(["ranking", `${cands.length.toLocaleString()} survived`]);
  if (!cands.length) { $("#count").textContent = ""; return render([{ pipeline: log }], "No names survived. Try another mode, fewer filters or a different lock."); }

  // top picks (each a different objective)
  const picks = [], used = new Set(), top = cands.slice(0, Math.max(10, Math.ceil(cands.length * .4)));
  // each category takes its best name that no earlier category already claimed
  const pick = (label, list) => { const x = list.find(c => !used.has(c.n)); if (x) { used.add(x.n); picks.push(Object.assign(Object.create(x), x, { pick: label })); } };
  pick("Best overall", cands);
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

  const rest = cands.filter(x => !used.has(x.n)).slice(0, 24);
  log.push(["showing", `${picks.length} top picks + ${rest.length} more`]);
  $("#count").innerHTML = `<b>${cands.length.toLocaleString()}</b> candidates survived the compiler`;
  render([
    { formula: [a, b] }, picks[0],
    { pipeline: log },
    { share: true },
    { heading: "Top picks" }, ...picks.slice(1),
    { heading: `All candidates · top ${rest.length}` }, ...rest,
  ], "Couldn't compile those names. Try different spellings!");
  revealAll();
}

function makeCand(n, segs, method, att, names) {
  // contribution = share of the new name's letters that came from each family name
  const L = fold(n).length || 1;
  const contrib = names.map(p => segs.filter(s => s.from === p).reduce((t, s) => t + (s.e - s.s), 0) / L);
  const base = att && att.obj ? att.obj : { n, g: gender, o: "", l: "", r: [], m: "", src: "", type: att ? "attested" : "invented" };
  return Object.assign(Object.create(base), base, {
    n, prov: { segs, method, names }, contrib, badge: att ? att.badge : "New blend", rank: att ? att.rank : 99999,
  });
}

// 6. Provenance view on each card
function provHTML(x) {
  const { segs, method, names } = x.prov;
  const rows = names.map((p, i) => {
    const mine = segs.filter(s => s.from === p);
    if (!mine.length) return "";
    let html = "", k = 0;
    for (const s of [...mine].sort((u, v) => u.s - v.s)) { html += esc(p.slice(k, s.s)) + `<mark>${esc(p.slice(s.s, s.e))}</mark>`; k = s.e; }
    html += esc(p.slice(k));
    const who = i === 0 ? "Mom" : i === 1 ? "Dad" : "Family";
    return `<div class="prow"><span class="pl">${who}</span><span class="pw">${html}</span><b>${Math.round(x.contrib[i] * 100)}%</b></div>`;
  }).join("");
  const lockSeg = segs.find(s => s.lock), addSeg = segs.find(s => s.add);
  const pieces = segs.map(s => s.lock ? `🔒${s.lock}` : s.add ? `+${s.add}` : s.from.slice(s.s, s.e)).join(" + ");
  const first = segs[0], lastSeg = segs[segs.length - 1];
  const startPiece = first.lock || first.add || (first.from && first.from.slice(first.s, first.e));
  const endPiece = lastSeg.lock || lastSeg.add || (lastSeg.from && lastSeg.from.slice(lastSeg.s, lastSeg.e));
  const canLock = x.badge === "New blend" || method === "splice" || method.startsWith("locked");
  return `<div class="prov">
    ${rows}
    ${lockSeg || addSeg ? `<div class="prow"><span class="pl">${lockSeg ? "Locked" : "Added"}</span><span class="pw"><mark>${esc((lockSeg || addSeg).lock || (lockSeg || addSeg).add)}</mark></span><b></b></div>` : ""}
    <div class="pmethod">${method === "splice" ? `built by splicing: ${esc(pieces)} → ${esc(x.n)}` : method.startsWith("locked") ? `built around your lock: ${esc(pieces)} → ${esc(x.n)}` : `${esc(method)}`}</div>
    ${canLock ? `<div class="locks">
      <button data-lock-start="${esc(startPiece)}">🔒 keep “${esc(startPiece)}…”</button>
      <button data-lock-end="${esc(endPiece)}">🔒 keep “…${esc(endPiece)}”</button></div>` : ""}
  </div>`;
}

function pipelineHTML(log) {
  const dots = (a, b) => ".".repeat(Math.max(3, 52 - a.length - b.length));
  return `<div class="pipeline">
    <div class="pipe-head">name compiler · ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
    ${log.map(([a, b], i) => `<div class="pipe-line" style="animation-delay:${i * 140}ms"><span>${esc(a)}</span><i>${dots(a, b)}</i><b>${esc(b)}</b></div>`).join("")}
    <div class="pipe-note">scores are heuristics: balance, how easy it is to say, surname flow, real-name evidence, length</div>
  </div>`;
}

function renderLocks() {
  const row = $("#lockRow");
  const chips = [];
  if (locks.start) chips.push(`<button data-unlock="start">🔒 starts with “${esc(locks.start)}” ✕</button>`);
  if (locks.end) chips.push(`<button data-unlock="end">🔒 ends with “${esc(locks.end)}” ✕</button>`);
  row.innerHTML = chips.join("");
  row.classList.toggle("hidden", !chips.length);
}

$("#results").addEventListener("click", e => {
  const ls = e.target.closest("[data-lock-start]"), le = e.target.closest("[data-lock-end]");
  if (ls) { locks.start = ls.dataset.lockStart; blend(); window.scrollTo({ top: $("#panel").offsetTop, behavior: "smooth" }); }
  if (le) { locks.end = le.dataset.lockEnd; blend(); window.scrollTo({ top: $("#panel").offsetTop, behavior: "smooth" }); }
});
$("#lockRow").addEventListener("click", e => { const u = e.target.closest("[data-unlock]"); if (u) { locks[u.dataset.unlock] = ""; blend(); } });
["#familyIn"].forEach(s => $(s).addEventListener("keydown", e => { if (e.key === "Enter") blend(); }));
["#honor", "#synthMode"].forEach(s => $(s).addEventListener("change", () => tab === "blend" && blend()));
