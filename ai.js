// ─────────────────────────────────────────────────────────────
// THE ASSISTANT, ON THE PAGE: two places where a parent can use their own words.
//   Dream  (in Find)  "We love Layla and Maya, something short, Arabic roots, means light": the assistant reads the words into
//                     filters, Lullabyte's own search finds the names, and the assistant says in one line why each one fits.
//   Meet   (in Duet)  each partner lists names they love; Lullabyte finds real names close to both lists, and says why.
// The assistant never adds a name or a meaning. It reads the request (worker/lullabyte-ai.js /interpret) and explains the
// results from the facts sent with them (/explain); a line that breaks a rule comes back empty and is written here from the
// same facts. When the assistant can't be reached, reader.js reads the words on the device and every line is written here.
// Uses globals from app.js, taste.js, generator.js and compiler.js.
// ─────────────────────────────────────────────────────────────
const AI_URL = /^(localhost|127\.0\.0\.1)$/.test(location.hostname) ? "http://localhost:8787" : "https://lullabyte-ai.suhxnitiwari.workers.dev";
async function askAI(path, body, ms = 9000) {
  const stop = new AbortController(), t = setTimeout(() => stop.abort(), ms);
  try {
    const r = await fetch(AI_URL + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: stop.signal });
    if (!r.ok) throw new Error(r.status);
    return await r.json();
  } finally { clearTimeout(t); }
}

// ── what two names share, said plainly (the facts the reasons are written from) ──
const SAY_NUM = ["", "one", "two", "three", "four", "five", "six"];
const THEME_WORD = { "Light & sun": "light", "Moon & stars": "the moon and stars", Nature: "nature", "Divine & faith": "faith", Wise: "wisdom", "Royal & noble": "nobility",
  "Peace & calm": "peace", "Life & hope": "hope", "Victory & glory": "victory", Strong: "strength", "Brave & fierce": "courage", "Kind & gentle": "kindness",
  "Love & joy": "love and joy", Beautiful: "beauty", "Feminine & graceful": "grace" };
const sylWord = n => `${SAY_NUM[n] || n} syllable${n === 1 ? "" : "s"}`;
// one name's sound, worked out once
function shapeOf(n) {
  const w = fold(n), sk = soundKey(n);
  // one = spellings close enough to be the same choice (Anwar, Anuar, Anvar), so a list shows each name once
  return { n, w, sk, one: sk.replace(/[wvu]/g, "u").replace(/h/g, ""), bg: bigrams(n), syl: sylCount(n), end2: w.slice(-2), end1: w.slice(-1), start: sk[0] || w[0] };
}
// cultures a name belongs to, from its own record: where it comes from first
function rootsOf(x) {
  const o = originOf(x), set = new Set();
  if (o) for (const p of o.split(/ · (?:from )?/)) set.add(p.replace(/^from /, ""));
  for (const c of [x.o, x.l, ...(x.oo || [])]) if (c) set.add(c);
  return set;
}
// how close a name sounds to one the parents love (0 to 1), and what they share
function soundNear(a, b) {
  const d = dice(a.bg, b.bg), end = a.end2 === b.end2 && a.w.length > 2 ? 1 : a.end1 === b.end1 ? .5 : 0;
  const syl = a.syl === b.syl ? 1 : Math.abs(a.syl - b.syl) === 1 ? .4 : 0, start = a.start === b.start ? 1 : 0;
  return .4 * d + .25 * end + .2 * syl + .15 * start;
}
function sharesOf(x, a, b, extra = {}) {
  const out = [];
  if (a.end2 === b.end2 && a.w.length > 2) out.push(`the \u2011${a.end2} ending`);
  if (a.start === b.start) out.push(`the same ${b.n[0].toUpperCase()} sound at the start`);
  if (a.end2 !== b.end2 && a.end1 === b.end1 && /[aeiouy]/.test(a.end1)) out.push(`the open \u2011${a.end1} ending`);
  if (a.syl === b.syl) out.push(sylWord(a.syl));
  if (extra.roots) { const r = [...extra.roots].find(c => extra.theirRoots && extra.theirRoots.has(c)); if (r) out.push(`${r} roots`); }
  if (extra.themes) { const t = extra.themes.find(t => extra.theirThemes && extra.theirThemes.includes(t)); if (t) out.push(`a meaning about ${THEME_WORD[t] || t.toLowerCase()}`); }
  return out.slice(0, 3);
}
const andList = a => a.length < 2 ? a.join("") : a.slice(0, -1).join(", ") + " and " + a[a.length - 1];
const firstCap = s => s.charAt(0).toUpperCase() + s.slice(1);
const meaningShort = m => { const s = m.split(/;|\. /)[0].trim(); return s.length > 60 ? s.slice(0, 58).replace(/\s\S*$/, "") + "…" : s; };
// a name's line written straight from its facts, used whenever the assistant's line is missing or broke a rule
function plainLine(p) {
  let s = p.near && p.near.length === 2 && p.near.every(n => n.shares.length)
    ? `Shares ${p.near[0].shares[0]} with ${p.near[0].name} and ${p.near[1].shares[0]} with ${p.near[1].name}.`
    : `${firstCap(andList(p.matched.slice(0, 3)) || "A real name that fits what you asked")}.`;
  if (p.meaning) s += ` It means “${meaningShort(p.meaning)}”.`;
  return s;
}
// the line shown: the assistant's if it kept to the facts, else the plain one; a name with no meaning on file says so
function lineFor(p, said) {
  const ok = typeof said === "string" && said.trim() && !(!p.meaning && /\bmean/i.test(said));
  return (ok ? said.trim() : plainLine(p)) + (p.meaning ? "" : " No meaning on file.");
}
// reasons for a few rows at once; each row is updated wherever it is on the page
async function explainRows(items, mode, wish) {
  if (!items.length) return;
  const picks = items.map(x => x._facts);
  let said = [];
  try { said = (await askAI("/explain", { mode, wish, picks })).reasons || []; } catch { said = []; }
  items.forEach((x, i) => {
    x.why = lineFor(x._facts, said[i]);
    $$(".row").forEach(row => { if (REG[+row.dataset.r] === x) { const el = row.querySelector(".row-why"); if (el) { el.textContent = x.why; el.removeAttribute("data-wait"); } } });
    if (x._onWhy) x._onWhy(x.why);
  });
}
// a row of our own: the name's record, with its reason attached (the record itself is never changed)
const withWhy = (x, facts) => ({ ...x, why: "", _facts: facts });

// common enough that families actually use it (official records), 0 to 1
const heldBy = x => { const c = x.cnt ?? (dbEntry(x.n) || {}).cnt ?? 0; return Math.min(1, Math.log10(c + 1) / 4); };
// easy to spell in modern English: plain letters, none of the scholarly marks (aa, q without u, bh), and the spelling most
// families chose for that sound (Layla, not Laylah)
function easySpell(n) {
  if (!/^[A-Za-z]+$/.test(n)) return false;
  const w = n.toLowerCase();
  if (/aa|ii|uu|q(?!u)|bh|dh|jh|[^aeiouy]{4}|(.)\1\1/.test(w)) return false;
  const mine = (dbEntry(n) || {}).cnt || 0, best = Math.max(mine, ...soundAlikes(n).map(s => (dbEntry(s) || {}).cnt || 0));
  return !best || mine >= best * .3;
}
// the names in the data a written name stands for: our record, or nothing (a name the data doesn't have is left out, and said)
const knownName = n => (BY_NAME.get(fold(n)) || [])[0] || dbEntry(n) || null;

// ─────────────────────────────────────────────────────────────
// DREAM: describe it, and Find does the rest
// ─────────────────────────────────────────────────────────────
const Dream = (() => {
  const form = $("#dream"), box = $("#dreamText"), heard = $("#dreamHeard"), note = $("#dreamNote");
  let W = null, wish = "", by = "", unknown = [], run = 0, queue = [], seen = new Set();
  const RELAX = [["easy", 1, () => "easy spelling"], ["feel", 1, () => "the feel"], ["len", 1, () => "the length"], ["syl", 2, () => "the syllables"],
    ["meanings", 3, w => `meaning ${andList(w.meanings).replace(/ and /, " or ")}`], ["origins", 3, w => `${andList(w.origins).replace(/ and /, " or ")} roots`]];

  // every culture a spoken origin can stand for: the data's own cultures and languages that contain the word, plus a few
  // ways people say them ("Hindi roots" are Indian and Sanskrit names; "Celtic" is Irish, Scottish and Welsh)
  const ALIAS = { hindi: ["Indian", "Sanskrit", "Hindi", "Hindu"], indian: ["Indian", "Sanskrit", "Hindi", "Hindu", "Tamil", "Telugu", "Bengali", "Punjabi", "Marathi", "Gujarati", "Kannada", "Malayalam"],
    sanskrit: ["Sanskrit", "Indian", "Hindu"], hindu: ["Hindu", "Sanskrit", "Indian"], arabic: ["Arabic", "Arab", "Arabian"], muslim: ["Islamic", "Arabic"], jewish: ["Hebrew", "Jewish"],
    biblical: ["Hebrew", "Biblical", "Christian"], gaelic: ["Irish", "Scottish"], celtic: ["Irish", "Scottish", "Welsh", "Celtic", "Breton", "Cornish"],
    scandinavian: ["Norse", "Swedish", "Norwegian", "Danish", "Icelandic", "Nordic"], maori: ["Māori"], sikh: ["Sikh", "Punjabi"] };
  let CULTS = null;
  const cultures = () => CULTS || (CULTS = [...new Set($$("#fRoots option").map(o => o.value).concat($$("#fLang option").map(o => o.value)).filter(Boolean))]);
  addEventListener("namesdb", () => CULTS = null);
  const originSet = o => { const k = o.toLowerCase(), set = new Set([o, ...(ALIAS[k] || [])]); for (const c of cultures()) if (c.toLowerCase().includes(k)) set.add(c); return set; };

  // what was heard, as a sentence of clauses that each take an ×
  const CLAUSE = {
    gender: w => ({ girl: "a girl’s name", boy: "a boy’s name", either: "a name for any gender" })[w.gender],
    syl: w => w.syl[0] === w.syl[1] ? sylWord(w.syl[0]) : `${w.syl[0]}–${w.syl[1]} syllables`,
    len: w => ({ "3-4": "3–4 letters", "5-6": "5–6 letters", "7-8": "7–8 letters", "9-99": "9 letters or more" })[w.len],
    feel: w => `${FEEL_LABEL[w.feel] || w.feel}`,
    origins: w => `${w.origins.join(" or ")} roots`, meanings: w => `meaning ${w.meanings.join(" or ")}`,
    like: w => `close to ${andList(w.like)}`, notLike: w => `nothing like ${andList(w.notLike)}`,
    easy: () => "easy to spell", notPopular: () => "not a top name", starts: w => `starting with ${w.starts.toUpperCase()}`, ends: w => `ending in \u2011${w.ends}`,
  };
  const has = k => W && (Array.isArray(W[k]) ? W[k].length : W[k] !== undefined && W[k] !== false);
  function showHeard() {
    const keys = Object.keys(CLAUSE).filter(has);
    heard.hidden = false;
    heard.innerHTML = keys.length
      ? `<span class="heard-k">Heard</span> ${keys.map(k => `<span class="heard-c">${esc(CLAUSE[k](W))}<button type="button" class="clause-x" data-drop="${k}" aria-label="Take out ${esc(CLAUSE[k](W))}">×</button></span>`).join("")}`
      : `<span class="heard-k">Heard</span> <span class="heard-none">nothing to search by yet. Try a sound, a length, roots or a meaning.</span>`;
    note.hidden = !unknown.length && by !== "reader";
    note.textContent = [unknown.length ? `${andList(unknown)} ${unknown.length > 1 ? "aren’t" : "isn’t"} in Lullabyte’s records, so ${unknown.length > 1 ? "they’re" : "it’s"} left out.` : "",
      by === "reader" ? "Read on this device: the assistant didn’t answer, so the reasons are written from the records." : ""].filter(Boolean).join(" ");
  }
  // the form below shows what it can (feel, letters, length, ruled-out sounds, popularity), so any of it can be changed by hand
  function setForm() {
    const set = (id, v) => { const el = $(id); el.value = v; fit(el); };
    set("#fStart", W.starts || ""); set("#fEnd", W.ends || ""); set("#fLen", W.len || ""); set("#fNoLike", (W.notLike || []).join(", ")); set("#fNotTop", W.notPopular ? "100" : "");
    Find.setVibe(W.feel || "");
    if (W.gender && W.gender !== gender) setGender(W.gender);
  }
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const text = box.value.trim();
    if (!text) return box.focus();
    MB.ensure(); MB.tick(.6);
    form.classList.add("reading"); $("#dreamGo").disabled = true; $("#dreamGo").textContent = "Reading…";
    try { const r = await askAI("/interpret", { text }); W = Reader.clean(r.filters); by = r.by === "reader" ? "reader" : "assistant"; }
    catch { W = Reader.read(text); by = "reader"; }
    form.classList.remove("reading"); $("#dreamGo").disabled = false; $("#dreamGo").textContent = "Find names";
    wish = text;
    unknown = W.like.filter(n => !knownName(n)); W.like = W.like.filter(knownName);
    showHeard(); setForm(); Find.run();
    $("#findOut").scrollIntoView({ behavior: "smooth", block: "start" });
  });
  box.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
  heard.addEventListener("click", e => {
    const b = e.target.closest("[data-drop]"); if (!b) return;
    const k = b.dataset.drop;
    W[k] = ["origins", "meanings", "like", "notLike"].includes(k) ? [] : undefined;
    // with every wish taken out, Find goes back to its own form
    if (!Object.keys(CLAUSE).some(has)) { W = null; heard.hidden = true; note.hidden = true; return Find.run(); }
    showHeard(); setForm(); Find.run();
  });
  // clear empties the words too
  $("#findReset").addEventListener("click", () => { W = null; wish = ""; box.value = ""; heard.hidden = true; note.hidden = true; }, { capture: true });

  // ── the search: Find's own filters, plus the ones only words can say; real names only ──
  function want(f) {
    const w = { ...f };
    if (!w.syl && W.syl) w.syl = W.syl.join("-");
    return w;
  }
  async function search(f) {
    const me = ++run, w = want(f), out = $("#findRows"), head = $("#findHead");
    $("#findOut").hidden = false;
    head.innerHTML = `<p class="count">Listening through the records…</p>`;
    const likes = W.like.map(shapeOf), likeKeys = new Set(likes.map(l => l.sk));
    const origins = W.origins.map(originSet), means = W.meanings.map(m => [new RegExp(`\\b${m.replace(/[^\p{L} ]/gu, "")}`, "iu"), THEMES.find(([, re]) => re.test(m))?.[1]]);
    // a name either passes Find's filters with the loosenable ones taken out, or it isn't a candidate; the loosenable ones are
    // checked one by one, so if nothing passes them all, the fewest and least important can be let go
    const base = { ...w, syl: "", len: "", vibe: "" };
    const check = {
      easy: x => !W.easy || easySpell(x.n), feel: x => !w.vibe || vibeMatch(x, w.vibe), len: x => lenOk(x.n, w.len),
      syl: x => { if (!w.syl) return true; const [lo, hi] = w.syl.split("-").map(Number), c = sylCount(x.n); return c >= lo && c <= hi; },
      // the meaning on file itself says it (light, or a word of the same family: radiance, lamp, dawn), never the story around it
      meanings: x => !means.length || !!x.m && means.some(([re, th]) => re.test(x.m) || th && th.test(x.m.toLowerCase())),
      origins: x => { if (!origins.length) return true; const r = rootsOf(x); return origins.some(set => [...set].some(c => r.has(c))); },
    };
    const active = RELAX.filter(([k]) => k === "feel" ? !!w.vibe : k === "len" ? !!w.len : k === "syl" ? !!w.syl : has(k));
    const found = [];
    const look = x => {
      if (likeKeys.has(soundKey(x.n)) || !matches(x, base)) return;
      let m = 0;
      active.forEach(([k], i) => { if (!check[k](x)) m |= 1 << i; });
      found.push([m, x]);
    };
    await slowly(REAL, x => { if (x.type === "real") look(x); });
    if (me !== run) return;
    if (DB_READY) await slowly(DB, x => { if (x.cnt >= 5 && !x.n.includes(" ")) look(x); });
    if (me !== run) return;
    // the cheapest set of loosened wishes that leaves at least one name
    let R = 0;
    if (!found.some(([m]) => !m)) {
      let best = null;
      for (let r = 1; r < 1 << active.length; r++) {
        let cost = 0; active.forEach(([, c], i) => { if (r & 1 << i) cost += c; });
        if (best && cost >= best.cost) continue;
        if (found.some(([m]) => (m & ~r) === 0)) best = { r, cost };
      }
      R = best ? best.r : (1 << active.length) - 1;
    }
    const keep = found.filter(([m]) => (m & ~R) === 0).map(([, x]) => x);
    const loosened = active.filter((_, i) => R & 1 << i).map(([, , say]) => say(W));
    // rank: close to the names they love, then a meaning on file, names families actually use, and the plainest spelling
    const scored = [];
    await slowly(keep, x => {
      const s = shapeOf(x.n), near = likes.length ? Math.max(...likes.map(l => soundNear(s, l))) : 0;
      const sink = tasteSink(x.n);
      if (sink >= .85) return;
      scored.push([(likes.length ? .55 * near : 0) + (x.m ? .15 : 0) + .2 * heldBy(x) + (easySpell(x.n) ? .05 : 0) + .05 * Math.random() - sink, x, s]);
    });
    if (me !== run) return;
    scored.sort((a, b) => b[0] - a[0]);
    queue = scored; seen = new Set();
    head.innerHTML = loosened.length
      ? `<p class="relax">Nothing in the records fits all of that at once, so these let go of <b>${esc(andList(loosened))}</b> and kept the rest.</p>`
      : `<p class="count"><b>${keep.length.toLocaleString()}</b> real names fit · closest to what you described first${taste.hate.length ? ` · ${taste.hate.length} you turned down are steering it` : ""}</p>`;
    if (!scored.length) { out.innerHTML = ""; head.innerHTML = `<p class="relax">Nothing in the records fits that. Take a wish out above and try again.</p>`; $("#findMore").classList.add("hidden"); return; }
    const first = take(8);
    fillRows(out, first, () => { const n = take(1); explainRows(n, "find", wish); return n[0]; });
    explainRows(first, "find", wish);
    $("#findMore").classList.toggle("hidden", !queue.length);
  }
  // the next names off the ranked list: one per sound (Layla, not Layla and Leila), each with its facts
  function take(n) {
    const out = [];
    while (out.length < n && queue.length) {
      const [, x, s] = queue.shift();
      if (seen.has(s.one) || tasteHated(x.n)) continue;
      seen.add(s.one); out.push(withWhy(x, factsFor(x, s)));
    }
    return out;
  }
  function factsFor(x, s) {
    const matched = [];
    if (W.syl) matched.push(sylWord(s.syl));
    if (W.origins.length) { const sets = W.origins.map(originSet), hit = [...rootsOf(x)].find(c => sets.some(set => set.has(c))); if (hit) matched.push(`${hit} roots`); }
    if (W.easy && easySpell(x.n)) matched.push("easy to spell");
    if (W.feel && vibeMatch(x, W.feel)) matched.push(`a ${FEEL_LABEL[W.feel] || W.feel} feel`);
    if (W.starts && s.w.startsWith(W.starts)) matched.push(`starts with ${W.starts.toUpperCase()}`);
    if (W.ends && s.w.endsWith(W.ends)) matched.push(`ends in \u2011${W.ends}`);
    const near = W.like.map(shapeOf).map(l => [soundNear(s, l), l]).sort((a, b) => b[0] - a[0])[0];
    if (near && near[0] > .25) { const sh = sharesOf(x, s, near[1]); if (sh.length) matched.push(`close to ${near[1].n} in ${andList(sh.slice(0, 2))}`); }
    return { name: x.n, origin: whereOf(x) || null, meaning: x.m || null, matched };
  }
  $("#findMore").addEventListener("click", e => {
    if (!W) return;
    e.stopImmediatePropagation();
    const more = take(8);
    $("#findRows").insertAdjacentHTML("beforeend", more.map(x => rowHTML(x)).join(""));
    explainRows(more, "find", wish);
    $("#findMore").classList.toggle("hidden", !queue.length);
  }, { capture: true });
  return { on: () => !!W, search };
})();

// ─────────────────────────────────────────────────────────────
// MEET IN THE MIDDLE: each partner lists names they love; the names closest to both lists come first
// ─────────────────────────────────────────────────────────────
const Meet = (() => {
  const A = $("#meetA"), B = $("#meetB");
  let run = 0, pool = null, poolG = "";
  const listOf = el => [...new Set(el.value.split(/[,;\n]+|\s+(?:and|&)\s+|\s+/).map(t => capName(t.trim())).filter(t => /^[\p{L}'’-]{2,}$/u.test(t)))].slice(0, 12);
  // real names only, the ones families actually give: our named records and official names that 50 or more people have
  async function poolFor() {
    if (pool && poolG === gender + DB_READY) return pool;
    const out = [], seen = new Set();
    const add = x => { const k = fold(x.n); if (seen.has(k) || !genderOk(x)) return; seen.add(k); out.push([x, shapeOf(x.n)]); };
    await slowly(REAL, x => { if (x.type === "real" && !/\s/.test(x.n)) add(x); });
    if (DB_READY) await slowly(DB, x => { if (x.cnt >= 50 && !/[\s-]/.test(x.n)) add(x); });
    pool = out; poolG = gender + DB_READY;
    return out;
  }
  // a partner's list as a taste: each name's sound, roots and meanings
  const tasteOf = names => names.map(n => { const x = knownName(n) || { n, o: "", oo: [], l: "", r: [], m: "", src: "", type: "attested" }; return { x, s: shapeOf(n), roots: rootsOf(x), themes: themesOf(x) }; });
  function sideScore(c, side) {
    let best = -1, sum = 0, at = side[0];
    for (const p of side) {
      const v = soundNear(c.s, p.s) + (c.roots && [...c.roots].some(r => p.roots.has(r)) ? .12 : 0) + (c.themes && c.themes.some(t => p.themes.includes(t)) ? .08 : 0);
      sum += v; if (v > best) { best = v; at = p; }
    }
    return { v: .7 * best + .3 * sum / side.length, at };
  }
  // how alike two tunes are: the same notes in the same order score highest
  function tuneNear(a, b) {
    const t = n => MB.melody(n).ev.filter(e => e.kind === "main").map(e => e.i), x = t(a), y = t(b), L = Math.min(x.length, y.length);
    if (!L) return 0;
    let d = 0; for (let i = 0; i < L; i++) d += Math.abs(x[i] - y[i]);
    return Math.max(0, 1 - d / L / 5 - Math.abs(x.length - y.length) * .15);
  }
  async function find() {
    const a = listOf(A), b = listOf(B);
    if (!a.length || !b.length) return (a.length ? B : A).focus();
    const me = ++run;
    MB.ensure(); MB.tick(.6);
    const box = $("#meetOut"); box.hidden = false;
    $("#meetBest").innerHTML = `<p class="count">Listening for names close to both…</p>`; $("#meetRows").innerHTML = "";
    const all = await poolFor();
    if (me !== run) return;
    const TA = tasteOf(a), TB = tasteOf(b), mine = new Set([...TA, ...TB].map(p => p.s.sk));
    // first by sound alone, which is quick; the closest few hundred are then weighed with roots, meanings and their tunes
    const rough = [];
    await slowly(all, ([x, s]) => {
      if (mine.has(s.sk) || tasteHated(x.n)) return;
      let ba = 0, bb = 0;
      for (const p of TA) ba = Math.max(ba, soundNear(s, p.s));
      for (const p of TB) bb = Math.max(bb, soundNear(s, p.s));
      rough.push([Math.min(ba, bb), x, s]);
    });
    if (me !== run) return;
    rough.sort((p, q) => q[0] - p[0]);
    const fine = rough.slice(0, 400).map(([, x, s]) => {
      const c = { x, s, roots: rootsOf(x), themes: themesOf(x) }, sa = sideScore(c, TA), sb = sideScore(c, TB);
      return { c, sa, sb, score: .85 * Math.min(sa.v, sb.v) + .15 * (sa.v + sb.v) / 2 + (x.m ? .03 : 0) + .04 * heldBy(x) - .5 * tasteSink(x.n) };
    }).sort((p, q) => q.score - p.score).slice(0, 80);
    for (const f of fine) f.score += .08 * Math.min(tuneNear(f.c.x.n, f.sa.at.x.n), tuneNear(f.c.x.n, f.sb.at.x.n));
    fine.sort((p, q) => q.score - p.score);
    const seen = new Set(), ranked = fine.filter(f => !seen.has(f.c.s.one) && seen.add(f.c.s.one));
    if (!ranked.length) { $("#meetBest").innerHTML = `<p class="relax">Nothing in the records sits between those two lists. Add a name or two to each.</p>`; return; }
    const items = ranked.map(f => {
      const share = (p) => sharesOf(f.c.x, f.c.s, p.s, { roots: f.c.roots, theirRoots: p.roots, themes: f.c.themes, theirThemes: p.themes });
      const facts = { name: f.c.x.n, origin: whereOf(f.c.x) || null, meaning: f.c.x.m || null, matched: [],
        near: [{ who: "one of you", name: f.sa.at.s.n, shares: share(f.sa.at) }, { who: "the other", name: f.sb.at.s.n, shares: share(f.sb.at) }] };
      return Object.assign(withWhy(f.c.x, facts), { nearA: f.sa.at.s.n, nearB: f.sb.at.s.n });
    });
    $("#meetLog").innerHTML = [[`one of you loves ${andList(a)}`, `${a.length} name${a.length > 1 ? "s" : ""}`], [`the other loves ${andList(b)}`, `${b.length} name${b.length > 1 ? "s" : ""}`],
      [`listening to real ${gender === "either" ? "" : gender + "s’ "}names for both`, all.length.toLocaleString()], ["closest in sound to both lists", "400"],
      ["weighed with roots, meanings and their tunes", `${ranked.length} kept`]].map(([s, n]) => `<div><span>${esc(s)}</span><i></i><b>${esc(n)}</b></div>`).join("");
    const best = items[0], rest = items.slice(1);
    $("#meetBest").innerHTML = `<p class="kick">Closest to both</p><h3 class="duet-name">${esc(best.n)}</h3>
      <p class="row-where">close to <span class="lg-a">${esc(best.nearA)}</span> and <span class="lg-b">${esc(best.nearB)}</span> · ${esc(whereOf(best) || "a real name")}</p>
      <p class="meet-why" data-wait></p>`;
    best._onWhy = t => { const el = $("#meetBest .meet-why"); if (el) { el.textContent = t; el.removeAttribute("data-wait"); } };
    fillRows($("#meetRows"), [best, ...rest.splice(0, 5)], () => { const n = rest.shift(); if (n) explainRows([n], "meet"); return n; });
    $("#meetRows .row").classList.add("big");
    explainRows(items.slice(0, 6), "meet");
    box.classList.remove("descend"); void box.offsetWidth; box.classList.add("descend");
    const top = box.getBoundingClientRect().top; if (top > innerHeight * .7) scrollBy({ top: top - innerHeight * .3, behavior: "smooth" });
  }
  $("#meetGo").onclick = find;
  [A, B].forEach(el => el.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); find(); } }));
  addEventListener("namesdb", () => { pool = null; });
  return { find };
})();
