// ─────────────────────────────────────────────────────────────
// LULLABYTE: the page. Data loading and the search engine first, then each room of the house:
// the box (hero), spellings, find, your ear, the duet, the charts, the cradle, explore.
// ─────────────────────────────────────────────────────────────
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
if ("scrollRestoration" in history) history.scrollRestoration = "manual"; // always open on the box
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fold = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[\s-]/g, "");
const capName = s => s.replace(/(^|[\s-])(\p{L})/gu, (m, a, b) => a + b.toUpperCase());
const uniq = arr => [...new Set(arr)].filter(Boolean).sort((a, b) => a.localeCompare(b));
const shuffle = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.random() * (i + 1) | 0; [a[i], a[j]] = [a[j], a[i]]; } return a; };
const store = { get: (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } }, set: (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} } };

// ── data ──
const ROOT_NAMES = buildRootNames();
const HAND_PICKED = REAL.length;                                  // the hand-written names with stories, before the big lists join
const TAKEN = new Set([...REAL, ...ROOT_NAMES].map(x => x.n.toLowerCase()));
const ALL_NAMED = [...REAL, ...ROOT_NAMES];
const BY_NAME = new Map(), SOUND_INDEX = new Map();
const indexName = x => { const k = fold(x.n); BY_NAME.has(k) ? BY_NAME.get(k).push(x) : BY_NAME.set(k, [x]); const sk = soundKey(x.n); SOUND_INDEX.has(sk) ? SOUND_INDEX.get(sk).push(x.n) : SOUND_INDEX.set(sk, [x.n]); };
ALL_NAMED.forEach(indexName);
const soundAlikes = n => SOUND_INDEX.get(soundKey(n)) || [];

// every real first name from government registries in 18 countries (data/names-db.tsv)
// name <TAB> gender (f / m / u = both / ? = registry has no sex) <TAB> countries <TAB> people recorded
let DB = [], DB_READY = false;
const DB_KEYS = new Map(), DB_G = { f: "girl", m: "boy", u: "either", "?": null };
const CC_LABEL = { us: "US", ca: "Canada", qc: "Québec", au: "Australia", uk: "Eng & Wales", nir: "N. Ireland", ie: "Ireland", fr: "France", es: "Spain", ch: "Switzerland",
  ar: "Argentina", br: "Brazil", cl: "Chile", pl: "Poland", de: "Germany", at: "Austria", no: "Norway", lu: "Luxembourg", pt: "Portugal", il: "Israel", fi: "Finland", be: "Belgium", sct: "Scotland", nz: "New Zealand" };
function eastAsian(d) {
  const rows = [];
  for (const [n, g, kanji, kana, ways, m] of d.ja || [])
    rows.push([n, g, "Japanese", "Japanese", "", m, (kanji ? `Written ${kanji} (${m})` + (ways > 1 ? `, one of ${ways} ways to write ${n} in kanji` : "") + ". " : "") + `In kana: ${kana}.`, "", "real"]);
  for (const [n, g, hangul, hanja, m, real] of d.ko || [])
    rows.push([n, g, "Korean", "Korean", "", m, `Written ${hangul} (${hanja}): ${m}.` + (real ? "" : " Built the way Korean names are made: two name syllables, each with its hanja."), "", real ? "real" : "root"]);
  for (const [n, g, hanzi, pinyin, m, real] of d.zh || [])
    rows.push([n, g, "Chinese", "Mandarin", "", m, `Written ${hanzi} (${pinyin}): ${m}.` + (real ? "" : " Built from two given-name characters."), "", real ? "real" : "root"]);
  return rows;
}
// names from sacred texts, Hebrew names from Israel, Japanese/Korean/Chinese names, and 120+ cultures
// the cultures list leads; the East Asian lists (some built from syllables) and Israel's records, which include names
// from everywhere, come after it, so they only add cultures (Rani is Bengali, Hindi and Telugu first)
const storied = Promise.all(["data/scripture-names.json?v=1", "data/culture-names.json?v=7", "data/also-cultures.json?v=1", "data/east-asian-names.json?v=1", "data/hebrew-names.json?v=1"]
  .map(u => fetch(u).then(r => r.json()).catch(() => [])))
  .then(([a, d, e, c, b]) => addStoried([...a, ...d, ...e, ...eastAsian(c), ...b])).catch(e => console.error(e));
function addStoried(rows) {
  const have = new Map(REAL.map(x => [fold(x.n), x]));
  for (const [n, g, o, l, r, m, src, texts, kind, also] of rows) {
    const x = texts ? texts.split(",") : [], k = fold(n), cur = have.get(k);
    if (cur) {
      if (o && o !== cur.o) cur.oo = [...new Set([...(cur.oo || []), o])];
      if (also && also.length) cur.oo = [...new Set([...(cur.oo || []), ...also])].filter(c => c !== cur.o);
      if (!cur.o && o) { cur.o = o; cur.l = cur.l || l; }
      cur.x = [...new Set([...(cur.x || []), ...x])]; cur.m ||= m; cur.src = cur.src ? (src && !cur.src.includes(src) && src.startsWith("Given to") ? `${cur.src} ${src}` : cur.src) : src; continue; }
    const e = { n, g: { g: "girl", b: "boy", e: "either" }[g], o, l, r: r ? r.split(",") : [], m, src, type: kind === "root" ? "root" : "real", x, oo: also || [] };
    (kind === "root" ? ROOT_NAMES : REAL).push(e); ALL_NAMED.push(e); have.set(k, e); TAKEN.add(k); indexName(e);
  }
  // hand-written names join their broad basket too (a Zulu name is also African)
  const GROUP = { African: "Zulu,Xhosa,Sotho,Tswana,Swahili,Akan,Somali,Ethiopian,Yoruba,Igbo,Hausa,Congolese,Sudanese,South Sudanese,Nubian",
    "South Asian": "Indian,Punjabi,Urdu,Pashtun,Afghan,Nepali,Tamil,Telugu,Bengali", Pacific: "Hawaiian,Samoan,Tongan,Fijian,Māori", Slavic: "Slavic,Russian,Ukrainian,Polish",
    "Latin American": "Mexican,Nahua,Maya,Purépecha,Zapotec,Colombian,Dominican,Puerto Rican,Cuban,Taíno,Argentine,Mapuche,Guaraní,Quechua",
    "Indigenous American": "Nahua,Maya,Purépecha,Zapotec,Taíno,Mapuche,Guaraní,Quechua", "Central Asian": "Uzbek,Afghan,Mongolian,Kazakh,Tajik" };
  for (const x of REAL) for (const [grp, list] of Object.entries(GROUP))
    if (x.o !== grp && [x.o, ...(x.oo || [])].some(c => list.split(",").includes(c)) && !(x.oo || []).includes(grp)) x.oo = [...(x.oo || []), grp];
  fillSelects();
}
const dbReady = Promise.all([fetch("data/names-db.tsv?v=3").then(r => r.text()), storied]).then(([t]) => {
  const ours = new Set(ALL_NAMED.map(x => fold(x.n)));
  for (const line of t.split("\n")) {
    if (!line) continue;
    const [n, g, cc, cnt] = line.split("\t"), k = fold(n), ccs = cc.split(",");
    const e = { n, g: DB_G[g], cc: ccs, cnt: +cnt, o: ccs.length === 1 && ccs[0] === "il" ? "Israeli" : "", l: "", r: [], m: "", src: "", type: "attested" };
    if (!DB_KEYS.has(k)) DB_KEYS.set(k, e);
    TAKEN.add(k);
    if (!ours.has(k)) DB.push(e);
  }
  for (const g in INVENTED) delete INVENTED[g]; // rebuild invented names without any real ones
  setTimeout(() => { for (const e of DB) { if (e.cnt < 20 || e.n.includes(" ")) continue; const sk = soundKey(e.n); SOUND_INDEX.has(sk) ? SOUND_INDEX.get(sk).push(e.n) : SOUND_INDEX.set(sk, [e.n]); } }, 50);
  DB_READY = true;
  fillSelects();
  dispatchEvent(new Event("namesdb"));
}).catch(() => {});
const dbEntry = n => DB_KEYS.get(fold(n));
const INVENTED = {};
const invented = g => INVENTED[g] || (INVENTED[g] = buildInvented(g, TAKEN));
const KIND_LABEL = { attested: "Real name", real: "Real name", root: "Built from roots", invented: "Invented" };

// official popularity: rank badges, and every year's top names for the time machine
let POP = null, YEARS = null;
const SHORT = { us: "US", ca: "Canada", au: "NSW", ew: "Eng & Wales", fr: "France" };
fetch("data/popularity.json?v=6").then(r => r.json()).then(d => { POP = d; }).catch(() => {});
fetch("data/years.json?v=1").then(r => r.json()).then(d => { YEARS = d; Charts.ready(); }).catch(() => {});
function popRanks(name, g) {
  if (!POP) return [];
  const sexes = g === "either" ? ["g", "b"] : [(g || gender)[0]], out = [];
  for (const c of POP.countries) for (const sx of sexes) {
    const hit = POP.lookup[c.key][`${sx}:${name.toLowerCase()}`];
    if (hit) out.push([SHORT[c.key] || c.label, hit[0], hit[1], c.last]);
  }
  return out.sort((a, b) => a[1] - b[1]);
}

// ── gender, shared by every room ──
let gender = "girl";
function setGender(g) {
  gender = g;
  $$("[data-gender]").forEach(b => b.setAttribute("aria-pressed", b.dataset.gender === g));
  $$(".g-select").forEach(s => { s.value = g; fit(s); });
  fillThemes();
  Find.refresh(); Charts.draw();
}
document.addEventListener("click", e => { const b = e.target.closest("[data-gender]"); if (b) setGender(b.dataset.gender); });
document.addEventListener("change", e => { if (e.target.classList.contains("g-select")) setGender(e.target.value); });

// ── selects filled from the data ──
function fillSelect(el, anyLabel, values) {
  const cur = el.value;
  el.innerHTML = `<option value="">${anyLabel}</option>` + values.map(v => `<option>${esc(v)}</option>`).join("");
  if (values.includes(cur)) el.value = cur;
  fit(el);
}
function fillSelects() {
  const cultures = uniq([...ALL_NAMED.flatMap(x => [x.o, ...(x.oo || [])]), DB_READY ? "Israeli" : ""]);
  $$('[data-fill="culture"]').forEach(el => fillSelect(el, el.dataset.any || "any", cultures));
  $$('[data-fill="religion"]').forEach(el => fillSelect(el, el.dataset.any || "any faith", uniq(ALL_NAMED.flatMap(x => x.r))));
  $$('[data-fill="lang"]').forEach(el => fillSelect(el, el.dataset.any || "any language", uniq(ALL_NAMED.map(x => x.l))));
}
const fillThemes = () => $$('[data-fill="theme"]').forEach(el => fillSelect(el, el.dataset.any || "anything", THEME_ORDER[gender]));
// size each blank in a sentence to its words, so it reads like a sentence
const measure = document.createElement("canvas").getContext("2d");
function fit(el) {
  if (!el || !el.classList || !el.classList.contains("slot")) return;
  const cs = getComputedStyle(el);
  measure.font = `italic 400 ${cs.fontSize} ${cs.fontFamily}`;
  const txt = el.tagName === "SELECT" ? (el.selectedOptions[0] ? el.selectedOptions[0].text.toLowerCase() : "") : (el.value || el.placeholder);
  el.style.width = Math.ceil(measure.measureText(txt).width) + (el.tagName === "SELECT" ? 26 : 12) + "px";
  el.classList.toggle("set", !!el.value);
}
const fitAll = () => $$(".slot").forEach(fit);
document.addEventListener("input", e => fit(e.target));
document.addEventListener("change", e => fit(e.target));

// ── the search engine ──
const genderOk = x => gender === "either" ? x.g === "either" : x.g === gender || x.g === "either";
const wrongGender = n => {
  const k = BY_NAME.get(fold(n)); if (k && k.length) return !k.some(genderOk);
  const e = dbEntry(n); return !!(e && (!e.g || !genderOk(e)));
};
// a feel: one of the name's vibe words, or its sound leans that way. "rare" means no country's top 1,000 has it.
function vibeMatch(x, want) {
  if (want === "rare") return !popRanks(x.n, x.g).length && (x.type !== "attested" || x.cnt < 400);
  const v = vibeOf(x);
  if (v.words.includes(want)) return true;
  return want === "soft" ? v.soft > .66 : want === "bold" ? v.soft < .34 : want === "timeless" ? v.modern < .34 :
    want === "modern" ? v.modern > .66 : want === "playful" ? v.elegant < .3 : want === "elegant" ? v.elegant > .7 :
    want === "celestial" ? v.words.includes("dreamy") : false;
}
function lenOk(name, len) {
  if (!len) return true;
  const [lo, hi] = len.split("-").map(Number), n = fold(name).length;
  return n >= lo && n <= hi;
}
function matches(x, f, letters = true) {
  if (!genderOk(x)) return false;
  if (f.theme && !themesOf(x).includes(f.theme)) return false;
  if (f.religion && !x.r.includes(f.religion)) return false;
  if (f.culture && x.o !== f.culture && !(x.oo || []).includes(f.culture)) return false;
  if (f.lang && x.l !== f.lang) return false;
  if (f.text && !(x.x || []).includes(f.text)) return false;
  if (letters) {
    const n = fold(x.n);
    if (f.first2 && !n.startsWith(f.first2)) return false;
    if (f.ends && !n.endsWith(f.ends)) return false;
  }
  if (!lenOk(x.n, f.len)) return false;
  if (f.vibe && !vibeMatch(x, f.vibe)) return false;
  return true;
}
function buildPools(f) {
  const needsMeaning = f.theme || f.religion || f.culture || f.lang || f.text; // invented names have no meaning or background
  const pools = {
    real: shuffle(REAL.filter(x => matches(x, f))),
    root: shuffle(ROOT_NAMES.filter(x => matches(x, f))),
    // official records: weighted toward names more people actually have; they only know culture when it's Israel
    db: !needsMeaning || (f.culture && !f.theme && !f.religion && !f.lang && !f.text) ? DB.filter(x => matches(x, f)).map(x => [Math.random() ** (1 / (1 + Math.log10(x.cnt))), x]).sort((a, b) => b[0] - a[0]).map(p => p[1]) : [],
    invented: !needsMeaning ? shuffle(invented(gender).filter(x => matches(x, f))) : [],
  };
  pools.ptr = { real: 0, db: 0, root: 0, invented: 0 };
  return pools;
}
// mix real names, root names and invented ones; real ones show up most, and names like ones you turned down sink
function drawFrom(pools, n, seen) {
  const out = [], W = { real: 4, db: 4, root: 2, invented: 3 };
  while (out.length < n) {
    const open = Object.keys(W).filter(k => pools.ptr[k] < pools[k].length);
    if (!open.length) break;
    let r = Math.random() * open.reduce((s, k) => s + W[k], 0), k = open[0];
    for (const key of open) { r -= W[key]; if (r <= 0) { k = key; break; } }
    const x = pools[k][pools.ptr[k]++], sink = tasteSink(x.n);
    if (seen.has(x.n) || sink >= .85 || Math.random() < sink) continue;
    seen.add(x.n); out.push(x);
  }
  return out;
}
const poolsLeft = p => p && ["real", "db", "root", "invented"].some(k => p.ptr[k] < p[k].length);
const poolsTotal = p => p.real.length + p.db.length + p.root.length + p.invented.length;
// when no name fits every blank: loosen the fewest, least important blanks and say which
const RELAX = [["vibe", 1, f => `the ${FEEL_LABEL[f.vibe] || f.vibe} feel`], ["len", 1, () => "the length"], ["lang", 2, f => `the ${f.lang} language`], ["culture", 2, f => `${f.culture} roots`],
  ["text", 3, f => `being named in the ${f.text}`], ["religion", 3, f => `the ${f.religion} faith`], ["theme", 3, f => `meaning ${f.theme.toLowerCase()}`],
  ["ends", 5, f => `ending in “${f.ends}”`], ["start", 6, f => `starting with “${f.first2}”`]];
const CHECK = {
  vibe: (x, f) => vibeMatch(x, f.vibe), len: (x, f) => lenOk(x.n, f.len), lang: (x, f) => x.l === f.lang, culture: (x, f) => x.o === f.culture || (x.oo || []).includes(f.culture),
  text: (x, f) => (x.x || []).includes(f.text), religion: (x, f) => x.r.includes(f.religion), theme: (x, f) => themesOf(x).includes(f.theme),
  ends: (x, f) => fold(x.n).endsWith(f.ends), start: (x, f) => fold(x.n).startsWith(f.first2),
};
function closest(f) {
  const active = RELAX.filter(([k]) => k === "start" ? !!f.first2 : !!f[k]), byMask = new Map();
  for (const x of [...REAL, ...ROOT_NAMES, ...DB, ...invented(gender)]) {
    if (!genderOk(x)) continue;
    let m = 0;
    active.forEach(([k], i) => { if (!CHECK[k](x, f)) m |= 1 << i; });
    byMask.has(m) ? byMask.get(m).push(x) : byMask.set(m, [x]);
  }
  let best = null;
  for (let R = 1; R < 1 << active.length; R++) {
    let cost = 0, n = 0;
    active.forEach(([, c], i) => { if (R & (1 << i)) cost += c; });
    if (best && cost > best.cost) continue;
    for (const [m, xs] of byMask) if ((m & ~R) === 0) n += xs.filter(x => x.type !== "invented").length;
    if (n && (!best || cost < best.cost || n > best.n)) best = { R, cost, n };
  }
  const items = [];
  for (const [m, xs] of byMask) if (!best || (m & ~best.R) === 0) items.push(...xs);
  return { loosened: active.filter((_, i) => !best || best.R & (1 << i)).map(([, , say]) => say(f)), items };
}
// new names that keep the letters, length and feel exactly (meanings are left to the parents)
function compose(f, want = 4) {
  const P = PARTS[gender], split = t => [...new Set(t.trim().split(/\s+/))], pre = f.first2, capW = t => t.charAt(0).toUpperCase() + t.slice(1);
  const fits = n => sayable(n) && !TAKEN.has(fold(n)) && (!pre || fold(n).startsWith(pre)) && (!f.ends || fold(n).endsWith(f.ends)) &&
    lenOk(n, f.len) && (!f.vibe || vibeMatch({ n, g: gender, o: "", l: "", r: [], m: "", src: "", type: "invented" }, f.vibe));
  const starts = split(P.start).filter(t => !pre || t.toLowerCase().startsWith(pre) || pre.startsWith(t.toLowerCase()));
  const starters = starts.length ? starts : [capW(pre)], enders = f.ends ? [f.ends] : split(P.end), mids = split(P.mid);
  const out = new Set(), pick = a => a[Math.random() * a.length | 0];
  for (let i = 0; i < 6000 && out.size < want; i++) {
    let st = pick(starters);
    if (pre && pre.length > st.length) st = capW(pre);
    const n = capW(join([st, ...Array.from({ length: Math.random() * 3 | 0 }, () => pick(mids)), pick(enders)]).toLowerCase());
    if (fits(n) && !tasteHated(n)) out.add(n);
  }
  return [...out].map(n => ({ n, g: gender, o: "", l: "", r: [], m: "", src: "", type: "invented", badge: "Composed for you" }));
}
// full name flow: how the first name runs into the last
const BAD_INITIALS = new Set("ASS BUM FAT PIG PMS STD WTF DIE DUM BAD SAD MAD HAG POO PEE RAT SOB FU BS PP VD OD DUD SOS CRY".split(" "));
const sylCount = n => (fold(n).replace(/y(?=[aeiou])/g, "Y").match(/[aeiouy]+/g) || []).length;
function flowCheck(first, last) {
  const f = fold(first), l = fold(last), notes = [], good = [], sf = sylCount(first), sl = sylCount(last);
  if (f.slice(-1) === l[0] && /[aeiouy]/.test(l[0])) notes.push(`“${f.slice(-1)}” runs into “${l[0]}”`);
  else if (f.slice(-1) === l[0]) notes.push("the sounds blur together");
  if (f.length > 2 && l.length > 2 && f.slice(-2) === l.slice(-2)) notes.push("it rhymes with the last name");
  if (f[0] === l[0]) good.push("alliterative");
  if (sf !== sl) good.push(`${sf} + ${sl} syllable rhythm`); else if (sf >= 3) notes.push(`${sf} + ${sl} syllables feels long`);
  if (f.length + l.length > 18) notes.push("a long full name");
  const ini = (first[0] + last[0]).toUpperCase();
  if (BAD_INITIALS.has(ini)) notes.push(`the initials spell ${ini}`);
  return { ok: !notes.length, notes, good };
}

// ── the cradle: saved names ──
const Cradle = (() => {
  let list = store.get("lullabyte-cradle", []);
  const save = () => { store.set("lullabyte-cradle", list); $$("[data-cradle-count]").forEach(el => el.textContent = list.length ? list.length : ""); render(); };
  const has = n => list.some(x => fold(x) === fold(n));
  function toggle(n) { if (has(n)) list = list.filter(x => fold(x) !== fold(n)); else { list.push(n); tasteSet(n, "love"); } save(); syncHearts(); return has(n); }
  function syncHearts() { $$("[data-heart]").forEach(b => { const on = has(b.dataset.heart); b.classList.toggle("tied", on); b.setAttribute("aria-pressed", on); }); }
  function render() {
    const root = $("#cradleMobile");
    if (!root) return;
    $("#cradleEmpty").classList.toggle("hidden", !!list.length);
    $("#cradlePlay").classList.toggle("hidden", list.length < 2);
    Hang.render(root, list.map((n, k) => ({ key: fold(n), len: 70 + (MB.melody(n).ev.find(e => e.kind === "main")?.i ?? 4) * -6 + 90 + (k % 3) * 26,
      html: `<button class="charm" data-play-name="${esc(n)}"><svg class="bow" viewBox="0 0 40 22" aria-hidden="true"><path d="M20 11c-6-9-17-9-17 0s11 9 17 0c6-9 17-9 17 0s-11 9-17 0zM20 11l-5 10M20 11l5 10"/></svg><span>${esc(n)}</span></button><button class="untie" data-untie="${esc(n)}" aria-label="Take ${esc(n)} out of the cradle">×</button>` })));
  }
  async function playAll() {
    for (const n of list) {
      const tag = $$("#cradleMobile .hc").find(el => el.dataset.key === fold(n));
      tag && tag.classList.add("lit"); tag && Hang.nudge(tag.firstChild, .15);
      await new Promise(r => setTimeout(r, MB.play(MB.melody(n)) * 1000 + 120));
      tag && tag.classList.remove("lit");
    }
  }
  return { toggle, has, save, render, playAll, syncHearts, get list() { return list; } };
})();

// ── a name row: quiet at rest; open it and a toy piano slides out and plays it ──
const REG = [];
const reg = x => (REG.push(x), REG.length - 1);
const hexId = n => ([...n].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7) & 0xffff).toString(16).toUpperCase().padStart(4, "0");
const notesOf = (m) => m.ev.filter(e => e.kind === "main").map(e => MB.NOTE_NAMES[e.i]).join(" · ");
function ownersOf(x) {
  if (!x.prov) return null;
  const L = fold(x.n).length, own = Array(L).fill(""), names = x.prov.names;
  let pos = 0;
  for (const s of x.prov.segs) {
    const len = s.from ? s.e - s.s : (s.lock || s.add || "").length, at = s.at ?? pos;
    const who = s.from ? (names.indexOf(s.from) === 0 ? "a" : names.indexOf(s.from) === 1 ? "b" : "f") : "";
    for (let k = 0; k < len; k++) if (at + k < L) own[at + k] = who;
    pos = at + len;
  }
  return own;
}
function coloredName(n, own) {
  let k = 0;
  return [...n].map(c => /[\s-]/.test(c) ? esc(c) : `<span class="o-${own[k++] || "x"}">${esc(c)}</span>`).join("");
}
// a name's cultures, most specific first (the broad baskets only when there's nothing else)
const BASKETS = new Set(["African", "South Asian", "Pacific", "Slavic", "Latin American", "Indigenous American", "Central Asian", "Nordic"]);
function whereOf(x) {
  const cc = x.cc || (dbEntry(x.n) || {}).cc || [];
  const all = [...new Set([x.o, ...(x.oo || [])].filter(Boolean))], named = all.filter(c => !BASKETS.has(c));
  const cultures = (named.length ? named : all).slice(0, 3);
  if (cultures.length > 1) return cultures.join(" · ");
  return [cultures[0], x.l && x.l !== cultures[0] ? x.l : ""].filter(Boolean).join(" · ") || (x.type === "attested" ? "Official records · " + cc.slice(0, 3).map(c => CC_LABEL[c]).join(", ") : "An original");
}
function rowHTML(x, o = {}) {
  const r = reg(x), m = MB.melody(x.n, "", ownersOf(x)), syl = sylCount(x.n);
  return `<article class="row${o.big ? " big" : ""}" data-r="${r}">
    <button class="row-hit" data-open aria-expanded="false">
      <span class="row-id">${x.pick ? `<em class="pick">${esc(x.pick)}</em>` : ""}No. ${hexId(x.n)} · ${esc(x.badge || KIND_LABEL[x.type])}</span>
      <span class="row-name">${x.prov && o.big ? coloredName(x.n, ownersOf(x)) : esc(x.n)}</span>
      <span class="row-where">${esc(whereOf(x))} · ${syl} syllable${syl === 1 ? "" : "s"}</span>
      <span class="row-notes"><i>♪</i> ${notesOf(m)}</span>
      <span class="row-play">Play <i>→</i></span>
    </button>
    <button class="heart${Cradle.has(x.n) ? " tied" : ""}" data-heart="${esc(x.n)}" aria-label="Keep ${esc(x.n)} in the cradle">${HEART}</button>
    <div class="row-more" hidden></div>
  </article>`;
}
const HEART = `<svg viewBox="0 0 24 22" aria-hidden="true"><path class="h" d="M12 20s-8-5-8-11a4.5 4.5 0 0 1 8-2.8A4.5 4.5 0 0 1 20 9c0 6-8 11-8 11z"/><path class="ribbon" d="M12 3c-3-3-7-1-5 1.5S12 3 12 3zm0 0c3-3 7-1 5 1.5S12 3 12 3zm0 0-2 4m2-4 2 4"/></svg>`;
function moreHTML(x) {
  const own = ownersOf(x), v = vibeOf(x), pop = popRanks(x.n, x.g).slice(0, 2).map(([c, r, , yr]) => `#${r} in ${c}, ${yr}`).join(" · ");
  const isNew = x.badge === "New blend" || x.badge === "Composed for you" || x.type === "invented";
  const spell = spellingsOf(x.n, soundAlikes(x.n)).filter(s => s.common).slice(0, 4);
  const last = Find.surname();
  const fl = last ? flowCheck(x.n, last) : null;
  return `${Piano.html([Piano.voice(x.n, "", own)])}
    <div class="row-detail">
      <div>
        ${x.m ? `<p class="mean">“${esc(x.m)}”</p>` : `<p class="mean none">${isNew ? "A brand-new name. No meaning yet: it's yours to give." : x.x && x.x.length ? `A name from the ${esc(x.x[0])}.` : "A real name, from official birth records."}</p>`}
        ${x.src ? `<p class="src">${esc(x.src)}</p>` : ""}
        ${x.prov ? provHTML(x) : ""}
      </div>
      <dl class="dl">
        <div><dt>Feels</dt><dd>${v.words.map(esc).join(", ") || "its own thing"}</dd></div>
        ${pop ? `<div><dt>Chart</dt><dd>${esc(pop)}</dd></div>` : ""}
        ${spell.length ? `<div><dt>Also spelled</dt><dd>${spell.map(s => `<button class="inline" data-spell="${esc(s.n)}">${esc(s.n)}</button>`).join(", ")}</dd></div>` : ""}
        ${fl ? `<div><dt>With ${esc(last)}</dt><dd class="${fl.ok ? "ok" : "warn"}">${fl.ok ? "flows" + (fl.good.length ? ": " + esc(fl.good.join(", ")) : "") : esc(fl.notes.join(", "))}</dd></div>` : ""}
      </dl>
    </div>
    <div class="row-acts">
      <button data-replay>Play again</button>
      ${last ? `<button data-replay-full>With ${esc(last)}</button>` : ""}
      <button data-spell="${esc(x.n)}">Hear its spellings</button>
      <button data-say>Say it aloud</button>
      <button class="nope" data-nope>Not for me</button>
    </div>`;
}
function openRow(row, play = true) {
  const x = REG[+row.dataset.r], more = row.querySelector(".row-more");
  if (!row.classList.contains("open")) {
    $$(".row.open").forEach(r => r !== row && r.closest(".rows") === row.closest(".rows") && closeRow(r));
    more.innerHTML = moreHTML(x); more.hidden = false;
    requestAnimationFrame(() => row.classList.add("open"));
    row.querySelector("[data-open]").setAttribute("aria-expanded", "true");
  }
  if (play) setTimeout(() => playRow(row), 260);
}
function closeRow(row) { row.classList.remove("open"); row.querySelector("[data-open]").setAttribute("aria-expanded", "false"); setTimeout(() => { if (!row.classList.contains("open")) row.querySelector(".row-more").hidden = true; }, 400); }
function playRow(row, withLast = false) {
  const x = REG[+row.dataset.r], p = row.querySelector(".piano");
  MB.ensure();
  if (withLast) return MB.play(MB.melody(x.n, Find.surname()));
  return Piano.play(p, [Piano.voice(x.n, "", ownersOf(x))]);
}
// say it with the browser's voice; a native voice for Latin-script languages
const VOICE_LANG = { French: "fr-FR", Spanish: "es-ES", Italian: "it-IT", German: "de-DE", Norse: "nb-NO", Turkish: "tr-TR", Indian: "en-IN", Irish: "en-IE", Scottish: "en-GB", Welsh: "en-GB", English: "en-GB" };
function say(x) {
  if (!("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(x.n);
  u.lang = VOICE_LANG[x.o] || "en-US"; u.rate = .85;
  const v = speechSynthesis.getVoices().find(v => v.lang === u.lang); if (v) u.voice = v;
  speechSynthesis.speak(u);
}
// "not for me": the string lets go, a new name takes its place, and the site remembers
const REASONS = ["too popular", "too long", "too short", "wrong roots", "the sound"];
function nope(row) {
  const x = REG[+row.dataset.r], list = row.closest(".rows");
  tasteSet(x.n, "hate");
  row.classList.add("let-go");
  const next = list && list._next ? list._next() : null;
  setTimeout(() => {
    const note = document.createElement("div");
    note.className = "nope-note";
    note.innerHTML = `<span>Not ${esc(x.n)}. Noted, and names like it will sink. Why?</span>${REASONS.map(r => `<button data-reason="${r}" data-n="${esc(x.n)}">${r}</button>`).join("")}<button class="undo" data-undo="${esc(x.n)}">undo</button>`;
    row.replaceWith(note);
    if (next) { note.insertAdjacentHTML("afterend", rowHTML(next)); note.nextElementSibling.classList.add("arrive"); }
    setTimeout(() => { if (note.isConnected && !note.dataset.kept) { note.classList.add("fade"); setTimeout(() => note.remove(), 600); } }, 9000);
  }, 380);
}
document.addEventListener("click", e => {
  const t = e.target;
  const heart = t.closest("[data-heart]");
  if (heart) { const on = Cradle.toggle(heart.dataset.heart); if (on) MB.tick(.6); return; }
  const sp = t.closest("[data-spell]");
  if (sp) return Spell.open(sp.dataset.spell);
  const reason = t.closest("[data-reason]");
  if (reason) { const said = reject(reason.dataset.n, reason.dataset.reason); const n = reason.closest(".nope-note"); n.dataset.kept = 1; n.innerHTML = `<span>Got it: ${esc(said)}.</span>`; setTimeout(() => { n.classList.add("fade"); setTimeout(() => n.remove(), 600); }, 2600); return; }
  const undo = t.closest("[data-undo]");
  if (undo) { tasteSet(undo.dataset.undo, null); const n = undo.closest(".nope-note"); n.dataset.kept = 1; n.innerHTML = `<span>${esc(undo.dataset.undo)} is back in the running.</span>`; return; }
  const row = t.closest(".row");
  if (!row) return;
  const x = REG[+row.dataset.r];
  if (t.closest("[data-open]")) return row.classList.contains("open") && !t.closest(".row-play") ? closeRow(row) : openRow(row);
  if (t.closest("[data-replay]")) return playRow(row);
  if (t.closest("[data-replay-full]")) return playRow(row, true);
  if (t.closest("[data-say]")) return say(x);
  if (t.closest("[data-nope]")) return nope(row);
  const ls = t.closest("[data-lock-start]"), le = t.closest("[data-lock-end]");
  if (ls || le) { if (ls) locks.start = ls.dataset.lockStart; else locks.end = le.dataset.lockEnd; Duet.run(); }
});
// a list of rows that can top itself up
function fillRows(el, items, next) {
  el.innerHTML = items.map(x => rowHTML(x)).join("");
  el._next = next;
}

// ─────────────────────────────────────────────────────────────
// THE BOX: type a name and the mobile builds it
// ─────────────────────────────────────────────────────────────
const Hero = (() => {
  const inp = $("#heroName"), typed = $("#typed"), field = $(".field");
  let auto = null, touched = store.get("lullabyte-typed", false), lastStrip = "";
  if (touched) $("#typeHint").classList.add("gone");
  function show(v, user) {
    typed.textContent = v;
    field.classList.toggle("empty", !v);
    Mobile.set(v);
    const parts = v ? MB.explain(v) : [];
    $("#heroPlay").innerHTML = `<svg viewBox="0 0 24 24"><path d="M7 4l13 8-13 8z"/></svg><span>${v ? "Play " + esc(v) : "Play"}</span>`;
    $("#heroPlay").disabled = !v;
    $("#sylRow").innerHTML = parts.map((p, k) => `<button class="cell" data-k="${k}" data-why="${esc(p.text + " · " + p.why + " → " + p.notes.join("–"))}"><b>${esc(p.text)}</b><code>${p.notes.join("–") || "·"}</code></button>`).join(`<i class="sep">·</i>`);
    $("#why").textContent = parts.length ? "point at a syllable to see why it plays that note" : "";
    $("#heroActs").classList.toggle("hidden", !v || !user);
    $("#heroKeep").classList.toggle("tied", !!v && Cradle.has(v)); $("#heroKeep").dataset.heart = v;
    if (v !== lastStrip) $("#tape").classList.remove("out");
  }
  // the instruction types itself, then hands over
  async function demo() {
    const sleep = ms => new Promise(r => auto.t = setTimeout(r, ms));
    auto = { t: 0 };
    const me = auto;
    for (const n of ["Theo", "Amara"]) {
      for (let k = 1; k <= n.length; k++) { if (auto !== me) return; show(n.slice(0, k)); await sleep(150 + Math.random() * 90); }
      await sleep(1500);
      for (let k = n.length - 1; k >= 0; k--) { if (auto !== me) return; show(n.slice(0, k)); await sleep(70); }
      await sleep(380);
    }
    if (auto === me) { show(""); auto = null; }
  }
  function takeOver() {
    if (auto) { clearTimeout(auto.t); auto = null; if (!inp.value) show(""); }
  }
  inp.addEventListener("focus", takeOver);
  inp.addEventListener("pointerdown", takeOver);
  inp.addEventListener("input", () => {
    takeOver();
    const v = capName(inp.value.replace(/^\s+/, "").replace(/\s{2,}/g, " "));
    show(v.trim(), true);
    if (v.trim() && !touched) { touched = true; store.set("lullabyte-typed", true); $("#typeHint").classList.add("gone"); }
  });
  inp.addEventListener("keydown", e => { if (e.key === "Enter") play(); });
  field.addEventListener("click", () => inp.focus());
  function play() {
    const v = typed.textContent.trim();
    if (!v) { inp.focus(); return; }
    MB.ensure();
    const m = MB.melody(v), labels = MB.explain(v).map(p => p.text);
    const tape = $("#tape");
    if (v !== lastStrip || !tape.classList.contains("out")) {
      $("#tapePaper").innerHTML = MB.paperSVG(m, { labels, cw: 30, rh: 5 }).svg;
      tape.classList.remove("out"); void tape.offsetWidth; tape.classList.add("out");
      lastStrip = v;
    }
    Mobile.play();
    MB.playPaper($("#tapePaper"), m, 1, { silent: true });
    $("#heroActs").classList.remove("hidden");
  }
  Mobile.onNote(e => {
    $$("#sylRow .cell").forEach(c => c.classList.toggle("on", e.kind === "main" && +c.dataset.k === e.syl));
    $$("#tapePaper .syl").forEach(c => c.classList.toggle("on", e.kind === "main" && +c.dataset.syl === e.syl));
  });
  Mobile.onDone(() => $$("#sylRow .cell.on, #tapePaper .syl.on").forEach(c => c.classList.remove("on")));
  $("#sylRow").addEventListener("pointerover", e => { const c = e.target.closest(".cell"); if (c) $("#why").textContent = c.dataset.why; });
  $("#sylRow").addEventListener("click", e => { const c = e.target.closest(".cell"); if (c) { const p = MB.explain(typed.textContent)[+c.dataset.k]; $("#why").textContent = c.dataset.why; const ev = MB.melody(typed.textContent).ev.filter(x => x.kind === "main" && x.syl === +c.dataset.k); ev.forEach((x, g) => MB.pluck(x.i, .9, 0)); } });
  $("#heroPlay").onclick = play;
  $("#heroSpell").onclick = () => Spell.open(typed.textContent.trim());
  $("#heroFind").onclick = () => $("#find").scrollIntoView({ behavior: "smooth" });
  show("");
  return { demo, get name() { return typed.textContent.trim(); } };
})();

// ─────────────────────────────────────────────────────────────
// SAME SONG, DIFFERENT LETTERS: paper strips slide out, one per spelling
// ─────────────────────────────────────────────────────────────
const Spell = (() => {
  const sheet = $("#spellSheet"), list = $("#spellList");
  let run = 0;
  const tune = n => MB.melody(n).ev.filter(e => e.kind === "main").map(e => e.i).join(",");
  function open(name) {
    name = capName((name || "").trim() || "Layla");
    $("#spellIn").value = name; fit($("#spellIn"));
    sheet.hidden = false; requestAnimationFrame(() => sheet.classList.add("on"));
    document.body.classList.add("sheet-open");
    build(name, 4);
  }
  function close() { run++; MB.stopAll(); sheet.classList.remove("on"); document.body.classList.remove("sheet-open"); setTimeout(() => { if (!sheet.classList.contains("on")) sheet.hidden = true; }, 450); }
  function build(name, max) {
    const me = ++run;
    const used = n => (dbEntry(n) || { cnt: 0 }).cnt;
    const vars = spellingsOf(name, soundAlikes(name)).slice(0, 30).map(s => ({ ...s, common: s.common || used(s.n) > 0 }))
      .sort((a, b) => (b.common - a.common) || (used(b.n) - used(a.n)));
    const all = [{ n: name, common: true }, ...vars].slice(0, max), home = tune(name);
    list.innerHTML = all.map((s, i) => {
      const m = MB.melody(s.n), same = tune(s.n) === home, r = popRanks(s.n, gender)[0];
      return `<div class="sp${i ? "" : " orig"}" data-n="${esc(s.n)}" style="--d:${i * 160}ms">
        <span class="sp-name">${esc(s.n)}</span>
        <div class="sp-paper">${MB.paperSVG(m, { cw: 24, rh: 4, labels: MB.explain(s.n).map(p => p.text) }).svg}</div>
        <span class="sp-tag"><b>${i === 0 ? "the original" : same ? "♪ same song" : "a different tune"}</b>${notesOf(m)}${r ? ` · #${r[1]} ${r[0]}` : !s.common ? " · possible spelling" : ""}</span>
      </div>`;
    }).join("");
    const same = all.slice(1).filter(s => tune(s.n) === home).length;
    $("#spellVerdict").textContent = "";
    $("#spellMore").classList.toggle("hidden", vars.length + 1 <= max);
    // hear them one after another, then say what we heard
    let t = 500;
    $$("#spellList .sp").forEach(el => {
      setTimeout(() => { if (run === me) MB.playPaper(el.querySelector(".sp-paper"), MB.melody(el.dataset.n)); }, t);
      t += MB.melody(el.dataset.n).steps * MB.STEP * 1000 + 260;
    });
    setTimeout(() => {
      if (run !== me) return;
      $("#spellVerdict").textContent = all.length < 2 ? `No other spellings of ${name} that we know of.` :
        same === all.length - 1 ? "Different letters. Same lullaby." : same ? `${same + 1} spellings, one song. The others change the tune.` : "Every spelling here changes the tune.";
    }, t);
  }
  list.addEventListener("click", e => { const r = e.target.closest(".sp"); if (r) { run++; MB.playPaper(r.querySelector(".sp-paper"), MB.melody(r.dataset.n)); } });
  $("#spellClose").onclick = close;
  $("#spellMore").onclick = () => build($("#spellIn").value.trim(), 12);
  $("#spellIn").addEventListener("keydown", e => { if (e.key === "Enter") build(capName($("#spellIn").value.trim()), 4); });
  addEventListener("keydown", e => { if (e.key === "Escape" && sheet.classList.contains("on")) close(); });
  return { open, close };
})();

// ─────────────────────────────────────────────────────────────
// FIND THEIR LULLABY: one quick form, then names that play themselves
// ─────────────────────────────────────────────────────────────
const FEEL_LABEL = { soft: "soft", bold: "bold", elegant: "romantic", timeless: "timeless", modern: "modern", playful: "playful", rare: "rare" };
const Find = (() => {
  const F = { vibe: "", culture: "", theme: "", first2: "", ends: "", len: "", last: "", religion: "", lang: "", text: "" };
  let pools = null, seen = new Set();
  const read = () => {
    F.culture = $("#fRoots").value; F.theme = $("#fTheme").value;
    F.first2 = fold($("#fStart").value); F.ends = fold($("#fEnd").value); F.len = $("#fLen").value; F.last = $("#fLast").value.trim();
    F.religion = $("#fFaith").value; F.text = $("#fText").value; F.lang = $("#fLang").value;
  };
  const pressVibe = () => $$('#quick [data-key="vibe"] button').forEach(b => b.setAttribute("aria-pressed", b.dataset.v === F.vibe));
  $('#quick [data-key="vibe"]').addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b) return;
    F.vibe = b.dataset.v; pressVibe(); MB.ensure(); MB.pluck(4 + Math.floor(Math.random() * 6), .45);
    if (!$("#findOut").hidden) { read(); search(); }
  });
  // once there are results, every change updates them
  $("#quick").addEventListener("change", () => { if (!$("#findOut").hidden) { read(); search(); } });
  $("#quick").addEventListener("submit", e => {
    e.preventDefault(); read(); MB.ensure(); MB.tick(.6);
    search();
    $("#findOut").scrollIntoView({ behavior: "smooth", block: "start" });
  });
  $("#findReset").onclick = () => {
    $("#quick").reset(); F.vibe = ""; pressVibe(); read(); fitAll();
    if (!$("#findOut").hidden) search();
  };
  pressVibe();
  const f = () => ({ ...F, first2: F.first2 });
  function search() {
    seen = new Set(); pools = buildPools(f());
    const out = $("#findRows"), head = $("#findHead");
    $("#findOut").hidden = false;
    if (!poolsLeft(pools)) {
      const c = closest(f()), made = compose(f());
      const of = t => shuffle(c.items.filter(x => (x.type === "attested" ? "db" : x.type) === t));
      pools = { real: of("real"), db: of("db"), root: of("root"), invented: of("invented"), ptr: { real: 0, db: 0, root: 0, invented: 0 } };
      const list = c.loosened.length > 1 ? c.loosened.slice(0, -1).join(", ") + " and " + c.loosened.slice(-1) : c.loosened[0];
      head.innerHTML = `<p class="relax">Nothing fits all of that at once, so these let go of <b>${esc(list || "nothing")}</b> and kept the rest.</p>`;
      fillRows(out, [...made, ...drawFrom(pools, 8 - made.length, seen)], () => drawFrom(pools, 1, seen)[0]);
    } else {
      const fmt = n => n.toLocaleString();
      head.innerHTML = `<p class="count"><b>${fmt(poolsTotal(pools))}</b> tunes match · ${fmt(pools.real.length)} with stories · ${fmt(pools.db.length)} from official records · ${fmt(pools.root.length)} from roots · ${fmt(pools.invented.length)} invented${taste.hate.length ? ` · ${taste.hate.length} you turned down are steering it` : ""}</p>`;
      fillRows(out, drawFrom(pools, 8, seen), () => drawFrom(pools, 1, seen)[0]);
    }
    $("#findMore").classList.toggle("hidden", !poolsLeft(pools));
  }
  $("#findMore").onclick = () => { $("#findRows").insertAdjacentHTML("beforeend", drawFrom(pools, 8, seen).map(x => rowHTML(x)).join("")); $("#findMore").classList.toggle("hidden", !poolsLeft(pools)); };
  addEventListener("namesdb", () => { if (!$("#findOut").hidden) search(); });
  return { refresh: () => { if (!$("#findOut").hidden) search(); }, surname: () => capName(F.last || Duet.surname() || "") };
})();

// ─────────────────────────────────────────────────────────────
// TWO NAMES. TWO MELODIES. One piano, Mom's notes and Dad's, then what they make together
// ─────────────────────────────────────────────────────────────
const Duet = (() => {
  const mom = $("#mom"), dad = $("#dad");
  const val = el => capName(el.value.trim());
  function keys() {
    const a = val(mom), b = val(dad), voices = [a && Piano.voice(a, "a"), b && Piano.voice(b, "b")].filter(Boolean);
    $("#duetPiano").innerHTML = Piano.html(voices);
    $("#duetLegend").innerHTML = a || b ? `<span class="lg a">${esc(a || "Mom")}</span><span class="lg b">${esc(b || "Dad")}</span><span class="lg both">both</span>` : `<span>type both names to hear them on the keys</span>`;
  }
  [mom, dad].forEach(el => el.addEventListener("input", () => { clearTimeout(el._t); el._t = setTimeout(keys, 200); }));
  [mom, dad].forEach(el => el.addEventListener("keydown", e => { if (e.key === "Enter") together(); }));
  // the extras live behind "+ Add something meaningful"
  $("#duetAdd").addEventListener("click", e => {
    const b = e.target.closest("[data-extra]"); if (!b) return;
    const clause = $(`#x-${b.dataset.extra}`); clause.hidden = false; b.hidden = true;
    const f = clause.querySelector("input, select"); f && f.focus();
    if (!$$("#duetAdd [data-extra]").some(x => !x.hidden)) $("#duetAddWrap").hidden = true;
  });
  const filt = () => ({ vibe: $("#dVibe").value, theme: $("#dTheme").value, culture: $("#dRoots").value, lang: $("#dLang").value, religion: $("#dFaith").value, text: $("#dText").value, len: $("#dLen").value, first2: "", ends: "" });
  const surname = () => $("#x-last").hidden ? "" : $("#dLast").value.trim();
  function together() {
    const a = val(mom), b = val(dad);
    if (!a || !b) return (a ? dad : mom).focus();
    MB.ensure(); keys();
    const p = $("#duetPiano .piano");
    $("#duetResult").hidden = true;
    const dur = Piano.play(p, [Piano.voice(a, "a"), Piano.voice(b, "b")]);
    $("#duetTogether").classList.add("playing");
    setTimeout(() => { $("#duetTogether").classList.remove("playing"); run(true); }, dur * 1000 + 250);
  }
  function run(reveal = false) {
    const a = val(mom), b = val(dad);
    if (!a || !b) return;
    const extra = $("#x-honor").hidden ? [] : $("#dHonor").value.split(/[,;]+|\s+/).map(t => t.trim()).filter(t => /^[\p{L}'-]{2,}$/u.test(t));
    let { picks, rest, log, total } = blend({ a, b, extra, mode: $("#dMode").value, honor: extra.length ? 1 : .5 }, filt(), capName(surname()));
    // "a lot of both": each parent gives at least a third of the letters
    if ($("#dShare").value === "lot") { const both = x => x.contrib[0] >= .3 && x.contrib[1] >= .3; picks = picks.filter(both); rest = rest.filter(both); }
    picks = picks.filter(x => !tasteHated(x.n)); rest = rest.filter(x => !tasteHated(x.n));
    const box = $("#duetResult");
    box.hidden = false;
    $("#duetLog").innerHTML = log.map(([s, n]) => `<div><span>${esc(s)}</span><i></i><b>${esc(n)}</b></div>`).join("");
    if (!picks.length) { $("#duetBest").innerHTML = `<p class="relax">Nothing survived those wishes. Try “a little of both”, or let go of a wish.</p>`; $("#duetRows").innerHTML = ""; return; }
    const best = picks[0];
    $("#duetBest").innerHTML = `<p class="kick">${esc(best.pick || "Best overall")} · ${esc(best.badge)}</p><h3 class="duet-name">${coloredName(best.n, ownersOf(best))}</h3><p class="row-where">${esc(whereOf(best))} · ${Math.round(best.contrib[0] * 100)}% ${esc(a)}, ${Math.round(best.contrib[1] * 100)}% ${esc(b)}</p>`;
    const queue = [...picks.slice(1), ...rest];
    fillRows($("#duetRows"), [best, ...queue.splice(0, 5)], () => queue.shift());
    const first = $("#duetRows .row");
    first.classList.add("big");
    if (reveal) { box.classList.remove("descend"); void box.offsetWidth; box.classList.add("descend"); setTimeout(() => openRow(first), 500); }
  }
  $("#duetTogether").onclick = together;
  $("#duetShare").onclick = () => {
    const u = new URL(location.href); u.search = ""; u.hash = "duet";
    u.searchParams.set("mom", val(mom)); u.searchParams.set("dad", val(dad)); u.searchParams.set("g", gender);
    navigator.clipboard?.writeText(u.toString());
    $("#duetShare").textContent = "link copied · send it to your partner";
  };
  $("#duetPiano").addEventListener("click", e => { const s = e.target.closest(".syl"); if (s) { const own = s.classList.contains("o-b") ? "b" : "a"; Piano.play($("#duetPiano .piano"), [Piano.voice(val(own === "b" ? dad : mom), own)]); } });
  addEventListener("namesdb", () => { if (!$("#duetResult").hidden) run(); });
  keys();
  return { run, surname, keys };
})();

// ─────────────────────────────────────────────────────────────
// THE NAMES WE ONCE SANG: a time machine, year by year, from official birth records only.
// Turn the knob back and the years go with it. Each place keeps its own publication rules,
// so a name that isn't listed reads "not published", never "0 babies".
// ─────────────────────────────────────────────────────────────
const Charts = (() => {
  let place = null, years = [], at = 0, timer = 0, angle = 0;
  const STEP = .35;                                                // radians of knob turn per year
  const sex = () => gender === "boy" ? 1 : 0;
  function ready() {
    const groups = {};
    YEARS.places.forEach(p => (groups[p.group] = groups[p.group] || []).push(p));
    $("#chCountry").innerHTML = Object.entries(groups).map(([g, ps]) => {
      const opts = ps.map(p => `<option value="${p.key}">${esc(p.label)}</option>`).join("");
      return g ? `<optgroup label="${esc(g)}">${opts}</optgroup>` : opts;
    }).join("");
    setPlace("us");
  }
  function setPlace(k) {
    const keepYear = place ? years[at] : null;
    place = YEARS.places.find(p => p.key === k);
    $("#chCountry").value = k; fit($("#chCountry"));
    years = Object.keys(place.years).map(Number).sort((a, b) => a - b);
    // stay in the same year if this place has it, else the nearest
    at = keepYear ? years.reduce((b, y, i) => Math.abs(y - keepYear) < Math.abs(years[b] - keepYear) ? i : b, 0) : years.length - 1;
    const range = $("#chRange");
    range.min = 0; range.max = years.length - 1; range.value = at;
    $("#chTicks").innerHTML = years.filter((y, i) => i === 0 || y % 20 === 0 || i === years.length - 1).map(y => `<button data-year="${y}">${y}</button>`).join("");
    $("#chSource").innerHTML = `${esc(place.agency)} · ${esc(place.dataset)} · ${esc(place.license)}`;
    draw(true);
  }
  function draw(quiet) {
    if (!YEARS || !place) return;
    const y = years[at], full = place.years[y][sex()], list = full.slice(0, 7);
    $("#chYear").textContent = y;
    $("#chRange").value = at;
    $("#chNote").textContent = place.rule;
    $$("#chTicks button").forEach(b => b.setAttribute("aria-current", +b.dataset.year === y));
    if (!full.length) { Hang.render($("#chMobile"), []); $("#chList").innerHTML = `<li class="none">Not published for ${y}.</li>`; return; }
    const max = full[0][1];
    Hang.render($("#chMobile"), list.map(([n, ct], k) => ({ key: y + n, len: 40 + k * 22 + (k % 2) * 14,
      html: `<button class="charm" data-play-name="${esc(n)}"><small>${k + 1}</small><span>${esc(n)}</span><em>${ct.toLocaleString()}</em></button>` })), { stagger: 60 });
    $("#chList").innerHTML = full.map(([n, ct], k) => `<li><span>${k + 1}</span><b>${esc(n)}</b><i style="--w:${(ct / max * 100).toFixed(1)}%"></i><em>${ct.toLocaleString()}${place.rounded ? "*" : ""}</em></li>`).join("");
    clearTimeout(timer);
    if (!quiet && MB.on) timer = setTimeout(() => playName(list[0][0]), 650);
  }
  function go(i, quiet) { i = Math.max(0, Math.min(years.length - 1, i)); if (i !== at) { angle += (i - at) * STEP; $("#chKnob").style.setProperty("--a", angle + "rad"); at = i; MB.tick(.6); draw(quiet); } }
  // the crank: turn it counterclockwise to go back in time
  const knob = $("#chKnob");
  let drag = null;
  knob.addEventListener("pointerdown", e => { const r = knob.getBoundingClientRect(); drag = { cx: r.left + r.width / 2, cy: r.top + r.height / 2, a: Math.atan2(e.clientY - (r.top + r.height / 2), e.clientX - (r.left + r.width / 2)), acc: 0 }; knob.setPointerCapture(e.pointerId); MB.ensure(); });
  knob.addEventListener("pointermove", e => {
    if (!drag) return;
    const a = Math.atan2(e.clientY - drag.cy, e.clientX - drag.cx);
    let d = a - drag.a; if (d > Math.PI) d -= 2 * Math.PI; if (d < -Math.PI) d += 2 * Math.PI;
    drag.a = a; drag.acc += d;
    while (drag.acc > STEP) { drag.acc -= STEP; go(at + 1); }
    while (drag.acc < -STEP) { drag.acc += STEP; go(at - 1); }
  });
  const up = () => { drag = null; };
  knob.addEventListener("pointerup", up); knob.addEventListener("pointercancel", up);
  knob.addEventListener("keydown", e => {
    const d = { ArrowLeft: -1, ArrowDown: -1, ArrowRight: 1, ArrowUp: 1, PageDown: -10, PageUp: 10 }[e.key];
    if (d) { e.preventDefault(); go(at + d); }
  });
  $("#chRange").addEventListener("input", e => go(+e.target.value, true));
  $("#chRange").addEventListener("change", () => draw());
  $("#chTicks").addEventListener("click", e => { const b = e.target.closest("[data-year]"); if (b) go(years.indexOf(+b.dataset.year)); });
  $("#chBack").onclick = () => go(at - 1);
  $("#chFwd").onclick = () => go(at + 1);
  $("#chCountry").onchange = e => setPlace(e.target.value);
  async function playYear() {
    MB.ensure();
    const tags = $$("#chMobile .hc:not(.rise)").slice(0, 5);
    for (const t of tags) { t.classList.add("lit"); Hang.nudge(t.firstChild, .12); await new Promise(r => setTimeout(r, MB.play(MB.melody(t.querySelector("span").textContent)) * 1000 + 80)); t.classList.remove("lit"); }
  }
  $("#chPlay").onclick = playYear;
  return { ready, draw: () => draw(true) };
})();
function playName(n) {
  MB.ensure();
  const tag = $$(".hc:not(.rise)").find(el => el.querySelector(`[data-play-name="${CSS.escape(n)}"]`));
  if (tag) { tag.classList.add("lit"); Hang.nudge(tag.firstChild, .14); setTimeout(() => tag.classList.remove("lit"), MB.melody(n).steps * MB.STEP * 1000); }
  MB.play(MB.melody(n));
}
document.addEventListener("click", e => {
  const p = e.target.closest("[data-play-name]"); if (p) return playName(p.dataset.playName);
  const u = e.target.closest("[data-untie]");
  if (u) { Cradle.toggle(u.dataset.untie); }
});
$("#cradlePlay").onclick = () => Cradle.playAll();

// ─────────────────────────────────────────────────────────────
// EXPLORE: the mobile unfolds, and every charm is a room
// ─────────────────────────────────────────────────────────────
// the explore mobile, drawn: one felt charm per room, on a beech dowel
(() => {
  const ROOMS = [["stage", "Play a name", "star", "#e6cf9f", 150], ["find", "Find their lullaby", "cloud", "#f4ebdc", 250], ["duet", "Two names, two melodies", "moon", "#cdbfa9", 300], ["spell", "Same song, different letters", "bird", "#b7c5aa", 210], ["charts", "The names we once sang", "sun", "#e6cf9f", 270], ["cradle", "The cradle", "bell", "#a3b7c6", 170]];
  const SH = {
    star: `<polygon points="${Array.from({ length: 10 }, (_, k) => { const a = -Math.PI / 2 + k * Math.PI / 5, r = k % 2 ? .46 : 1; return (Math.cos(a) * r).toFixed(3) + "," + (Math.sin(a) * r).toFixed(3); }).join(" ")}"/>`,
    cloud: `<circle cx="-.55" cy=".12" r=".45"/><circle cx="-.15" cy="-.2" r=".55"/><circle cx=".32" cy="-.1" r=".5"/><circle cx=".62" cy=".18" r=".38"/><circle cx="0" cy=".22" r=".5"/>`,
    drop: `<path d="M0,-1.1 C.4,-.5 .85,0 .8,.35 A.8,.8 0 0 1 -.8,.35 C-.85,0 -.4,-.5 0,-1.1Z"/>`,
    moon: `<path d="M.3,-.95 A1,1 0 1,0 .95,.3 A.8,.8 0 1,1 .3,-.95Z"/>`,
    bird: `<ellipse rx=".95" ry=".6"/><circle cx=".72" cy="-.42" r=".38"/><polygon points="-.8,-.1 -1.45,-.55 -1.3,.15"/>`,
    sun: `<polygon points="${Array.from({ length: 24 }, (_, k) => { const a = k / 24 * Math.PI * 2, r = k % 2 ? .74 : 1; return (Math.cos(a) * r).toFixed(3) + "," + (Math.sin(a) * r).toFixed(3); }).join(" ")}"/>`,
    bell: `<path d="M-.7,.5 C-.7,-.6 -.4,-.9 0,-.9 C.4,-.9 .7,-.6 .7,.5 L.85,.7 L-.85,.7Z"/><circle cy=".85" r=".18"/>`,
  };
  const defs = ROOMS.map(([go, , , c]) => `<radialGradient id="ex-${go}" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="${c}" stop-opacity=".75"/><stop offset=".55" stop-color="${c}"/><stop offset="1" stop-color="#8a7466" stop-opacity=".55"/></radialGradient>`).join("")
    + `<linearGradient id="ex-wood" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ecd2b0"/><stop offset="1" stop-color="#b98c5e"/></linearGradient>`;
  const charm = (go, label, shape, x, top, y, r, k, lx, anchor) => `<g class="ex-charm" tabindex="0" role="button" aria-label="${label}" data-go="${go}" style="transform-origin:${x}px ${top}px;--d:${k * 70}ms">
      <line x1="${x}" y1="${top}" x2="${x}" y2="${y - r * .8}"/>
      <circle class="bead" cx="${x}" cy="${top + (y - top) * .45}" r="7"/>
      <g class="shape" transform="translate(${x} ${y}) scale(${r})" fill="url(#ex-${go})">${SH[shape]}</g>
      <text class="lbl" x="${lx ?? x}" y="${lx == null ? y + r + 34 : y + 8}" text-anchor="${anchor || "middle"}">${label}</text>
    </g>`;
  let narrow = null;
  function build() {
    if (narrow === innerWidth < 760) return;
    narrow = innerWidth < 760;
    if (narrow) {
      // on a phone the charms hang one under another, down a long ribbon of string
      const H = 60 + ROOMS.length * 92;
      $("#exMobile").innerHTML = `<svg viewBox="0 0 340 ${H}"><defs>${defs}</defs><rect class="dowel" x="20" y="10" width="110" height="10" rx="5" fill="url(#ex-wood)"/>${
        ROOMS.map(([go, label, shape], k) => charm(go, label, shape, 50 + (k % 2) * 40, 20, 70 + k * 92, 28, k, 150, "start")).join("")}</svg>`;
    } else {
      const W = 1000, gap = W / (ROOMS.length + 1);
      $("#exMobile").innerHTML = `<svg viewBox="0 0 ${W} 460"><defs>${defs}</defs><line class="hook" x1="500" y1="0" x2="500" y2="62"/><rect class="dowel" x="${gap * .5}" y="62" width="${W - gap}" height="12" rx="6" fill="url(#ex-wood)"/>${
        ROOMS.map(([go, label, shape, , len], k) => charm(go, label, shape, gap * (k + 1), 70, 70 + len, shape === "cloud" ? 46 : 40, k)).join("")}</svg>`;
    }
    bindExplore();
  }
  addEventListener("resize", build);
  setTimeout(build);
})();
function openExplore() { document.body.classList.add("exploring"); $("#exploreBtn").setAttribute("aria-expanded", "true"); setTimeout(() => $("#explore .ex-charm").focus(), 300); MB.on && MB.pluck(7, .4); }
function closeExplore() { document.body.classList.remove("exploring"); $("#exploreBtn").setAttribute("aria-expanded", "false"); }
$("#exploreBtn").onclick = () => document.body.classList.contains("exploring") ? closeExplore() : openExplore();
$("#exploreClose").onclick = closeExplore;
addEventListener("keydown", e => { if (e.key === "Escape") closeExplore(); });
function bindExplore() { $$(".ex-charm").forEach((el, k) => {
  el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); el.dispatchEvent(new MouseEvent("click", { bubbles: true })); } });
  el.addEventListener("mouseenter", () => { if (MB.on) MB.pluck([7, 9, 5, 11, 4, 8, 2][k % 7], .45); });
  el.addEventListener("click", () => {
    closeExplore();
    const go = el.dataset.go;
    if (go === "spell") return Spell.open(Hero.name || "Layla");
    setTimeout(() => $("#" + go).scrollIntoView({ behavior: "smooth" }), 250);
    if (go === "stage") setTimeout(() => $("#heroName").focus({ preventScroll: true }), 800);
  });
}); }

// ─────────────────────────────────────────────────────────────
// SOUND: the first thing the site asks
// ─────────────────────────────────────────────────────────────
function soundUI() { $("#soundBtn").classList.toggle("off", !MB.on); $("#soundBtn").setAttribute("aria-pressed", MB.on); }
$("#soundBtn").onclick = () => { MB.setOn(!MB.on); soundUI(); if (MB.on) MB.pluck(7, .6); };
function enter(withSound) {
  MB.setOn(withSound); soundUI();
  if (withSound) [0, 4, 7].forEach((i, k) => MB.pluck(i + 2, .55, MB.ensure().currentTime + k * .12));
  $("#gate").classList.add("gone");
  store.set("lullabyte-entered", true);
  setTimeout(() => { $("#gate").hidden = true; Hero.demo(); }, 500);
}
$("#gateSound").onclick = () => enter(true);
$("#gateQuiet").onclick = () => enter(false);
if (store.get("lullabyte-entered", false)) { $("#gate").hidden = true; setTimeout(Hero.demo, 600); }
soundUI();

// the top bar turns to paper once you leave the box
new IntersectionObserver(([en]) => $("#topbar").classList.toggle("solid", !en.isIntersecting), { rootMargin: "-64px 0px 0px 0px" }).observe($("#stage"));
$("#cradleBtn").onclick = () => $("#cradle").scrollIntoView({ behavior: "smooth" });
addEventListener("namesdb", () => {
  const gen = ROOT_NAMES.length + ["girl", "boy", "either"].reduce((s, g) => s + invented(g).length, 0);
  $("#totalLine").textContent = `${(REAL.length + DB.length + gen).toLocaleString()} names · every one plays its own song`;
});

// shared link: ?mom=Priya&dad=Daniel&g=girl opens straight into the duet
(() => {
  const q = new URLSearchParams(location.search);
  fillSelects(); fillThemes(); fitAll();
  if (["girl", "boy", "either"].includes(q.get("g"))) setGender(q.get("g"));
  if (q.get("mom") && q.get("dad")) {
    $("#mom").value = q.get("mom"); $("#dad").value = q.get("dad"); fitAll(); Duet.keys();
    setTimeout(() => { $("#duet").scrollIntoView(); Duet.run(true); }, 400);
  }
  Cradle.save();
  document.fonts && document.fonts.ready.then(() => { fitAll(); Mobile.resize(); });
})();
