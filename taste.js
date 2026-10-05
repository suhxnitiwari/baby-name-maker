// ─────────────────────────────────────────────────────────────
// TASTE MODEL: learns from names you love and don't, then recommends with reasons.
// Uses globals from app.js (fold, vibeOf, popRanks, BY_NAME, gender, soundKey) and MB.
// ─────────────────────────────────────────────────────────────
const TASTE_KEY = "bnm-taste-v1";
let taste = (() => { try { return JSON.parse(localStorage.getItem(TASTE_KEY)) || null; } catch { return null; } })()
  || { love: [], hate: [], banCultures: [], maxLen: 0, minLen: 0, popCap: 0, log: [] };
const saveTaste = () => { try { localStorage.setItem(TASTE_KEY, JSON.stringify(taste)); } catch {} };

const cap1 = s => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
const parseNames = s => [...new Set(s.split(/[\s,;]+/).map(t => t.trim()).filter(t => /^[\p{L}'-]{2,}$/u.test(t)).map(cap1))];

// Turn a typed name into a name object: our data if we have it, otherwise a plain record.
function nameObj(n) {
  const known = (BY_NAME.get(fold(n)) || []).find(x => x.g === gender || x.g === "either") || (BY_NAME.get(fold(n)) || [])[0];
  return known || { n, g: gender, o: "", l: "", r: [], m: "", src: "", type: "attested" };
}
const sylOf = n => (fold(n).replace(/y(?=[aeiou])/g, "Y").match(/[aeiouy]+/g) || []).length;
function endClass(n) {
  const w = fold(n);
  if (/(a|ah|aa)$/.test(w)) return "a";
  if (/(i|ee|y|ie|ey)$/.test(w)) return "i";
  if (/e$/.test(w)) return "e";
  if (/o$/.test(w)) return "o";
  return "consonant";
}
const END_LABEL = { a: "an open “-a” ending", i: "an “-ee” ending", e: "an “-e” ending", o: "an “-o” ending", consonant: "a consonant ending" };
const bigrams = n => { const w = "^" + fold(n) + "$"; const s = new Set(); for (let i = 0; i < w.length - 1; i++) s.add(w.slice(i, i + 2)); return s; };
const dice = (a, b) => { let k = 0; for (const x of a) if (b.has(x)) k++; return (2 * k) / (a.size + b.size || 1); };
const bestRank = n => (popRanks(n, gender)[0] || [0, 99999])[1];
const mean = a => a.reduce((s, x) => s + x, 0) / (a.length || 1);
const mode = a => { const c = {}; a.forEach(x => c[x] = (c[x] || 0) + 1); return Object.entries(c).sort((p, q) => q[1] - p[1])[0]; };

// ── 1. Learn the profile ──
function buildProfile() {
  const L = taste.love.map(nameObj), D = taste.hate.map(nameObj);
  if (!L.length) return null;
  const V = L.map(vibeOf), syl = L.map(x => sylOf(x.n)), len = L.map(x => fold(x.n).length);
  const ends = L.map(x => endClass(x.n)), [endTop, endN] = mode(ends);
  const cultures = {}; L.forEach(x => x.o && (cultures[x.o] = (cultures[x.o] || 0) + 1));
  const ranks = L.map(x => Math.min(bestRank(x.n), 3000)).sort((a, b) => a - b);
  const medRank = ranks[Math.floor(ranks.length / 2)];
  const soft = mean(V.map(v => v.soft)), modern = mean(V.map(v => v.modern)), elegant = mean(V.map(v => v.elegant));
  const spread = Math.sqrt(mean(V.map(v => (v.soft - soft) ** 2)));
  const p = {
    L, D, soft, modern, elegant, endTop, endShare: endN / L.length,
    sylMin: Math.min(...syl), sylMax: Math.max(...syl), sylMode: +mode(syl)[0], lenAvg: mean(len),
    cultures: Object.entries(cultures).sort((a, b) => b[1] - a[1]).map(c => c[0]).filter(c => !taste.banCultures.includes(c)),
    medRank, rarity: Math.min(1, Math.log10(medRank) / Math.log10(3000)),
    bgL: L.map(x => bigrams(x.n)), bgD: D.map(x => bigrams(x.n)),
    confidence: Math.round(Math.min(96, 38 + L.length * 8 + D.length * 3 - spread * 60)),
  };
  return p;
}

// ── 2. Score a candidate: five signals, 0–100 each ──
function scoreName(x, p) {
  const v = vibeOf(x), bg = bigrams(x.n), syl = sylOf(x.n), len = fold(x.n).length;
  const phon = Math.min(1, Math.max(...p.bgL.map(b => dice(bg, b))) * 1.6);
  const feel = 1 - (Math.abs(v.soft - p.soft) + Math.abs(v.modern - p.modern) + Math.abs(v.elegant - p.elegant)) / 3;
  const lengthFit = syl >= p.sylMin && syl <= p.sylMax ? 1 : Math.max(0, 1 - .35 * Math.min(Math.abs(syl - p.sylMin), Math.abs(syl - p.sylMax)));
  const endFit = endClass(x.n) === p.endTop ? 1 : p.endShare < .5 ? .7 : .35;
  const culture = !p.cultures.length ? .7 : p.cultures.includes(x.o) ? 1 : !x.o ? .55 : .3;
  const r = Math.min(bestRank(x.n), 3000);
  const rarity = 1 - Math.min(1, Math.abs(Math.log10(r) - Math.log10(p.medRank)) / 1.6);
  let total = 100 * (phon * .26 + feel * .22 + lengthFit * .17 + endFit * .13 + culture * .12 + rarity * .10);
  // things you've told it you don't want
  const hateSim = p.bgD.length ? Math.max(...p.bgD.map(b => dice(bg, b))) : 0;
  total -= hateSim > .5 ? 30 * hateSim : 0;
  if (taste.banCultures.includes(x.o)) total -= 40;
  if (taste.maxLen && len > taste.maxLen) total -= 35;
  if (taste.minLen && len < taste.minLen) total -= 35;
  if (taste.popCap && r <= taste.popCap) total -= 30;
  if (x.type === "invented") total -= 6; // prefer attested names
  return { total: Math.max(0, Math.min(99.9, total)), parts: { phon, feel, lengthFit, endFit, culture, rarity } };
}

// Candidates: our names + every real name in the official popularity data.
function candidates() {
  const mine = [...taste.love, ...taste.hate];
  const seen = new Set(mine.map(fold));
  // also skip respellings of your own names (Inaya → Inayah, Leila → Laila)
  const sounds = new Set(mine.map(soundKey));
  mine.forEach(n => (FAMILY_OF.get(fold(n)) || []).forEach(v => seen.add(fold(v))));
  const out = [];
  const add = x => { const k = fold(x.n); if (seen.has(k) || sounds.has(soundKey(x.n)) || wrongGender(x.n)) return; seen.add(k); out.push(x); };
  [...REAL, ...ROOT_NAMES].filter(genderOk).forEach(add);
  // real names from the official database (single-word names 30+ people have, matching gender)
  for (const e of DB) if (e.g && genderOk(e) && e.cnt >= 30 && !e.n.includes(" ")) add(e);
  invented(gender).slice(0, 25000).forEach(add);
  return out;
}

// ── 3. Explain ──
function explain(p) {
  const bits = [];
  const sylTxt = p.sylMin === p.sylMax ? `${p.sylMin} syllable${p.sylMin > 1 ? "s" : ""}` : `${p.sylMin}–${p.sylMax} syllables`;
  bits.push(sylTxt);
  if (p.endShare >= .5) bits.push(END_LABEL[p.endTop]);
  bits.push(p.soft > .62 ? "soft, flowing sounds" : p.soft < .38 ? "crisp, strong sounds" : "a balance of soft and strong sounds");
  if (p.cultures.length) bits.push(`${p.cultures.slice(0, 2).join(" + ")} roots`);
  bits.push(p.medRank > 800 ? "rare names" : p.medRank > 150 ? "familiar-but-not-everywhere names" : "well-known names");
  return bits;
}
// ── 4. Use it ──
// Every "love" and "not for me" anywhere on the site lands here, and quietly steers every later search.
function tasteSet(n, how) {
  n = cap1(n);
  taste.love = taste.love.filter(x => fold(x) !== fold(n));
  taste.hate = taste.hate.filter(x => fold(x) !== fold(n));
  if (how === "love") taste.love.push(n);
  if (how === "hate") taste.hate.push(n);
  saveTaste();
}
const tasteHated = n => taste.hate.some(h => fold(h) === fold(n));
// how much a name should sink because it sounds like ones you turned down (0 = not at all, 1 = gone)
function tasteSink(n) {
  if (!taste.hate.length) return 0;
  if (tasteHated(n)) return 1;
  const sk = soundKey(n), bg = bigrams(n);
  let worst = 0;
  for (const h of taste.hate) worst = Math.max(worst, soundKey(h) === sk ? .9 : dice(bg, bigrams(h)));
  return worst > .55 ? worst : 0;
}
// "not for me", with a reason: the model changes in a way you can see
function reject(name, reason) {
  const x = nameObj(name), len = fold(name).length, r = bestRank(name);
  tasteSet(name, "hate");
  const msg = {
    "too popular": () => { taste.popCap = Math.max(taste.popCap, Math.min(r, 3000) + 50); return `skipping the top ${taste.popCap} most popular names`; },
    "too long": () => { taste.maxLen = len - 1; return `names up to ${len - 1} letters`; },
    "too short": () => { taste.minLen = len + 1; return `names of ${len + 1} letters or more`; },
    "wrong roots": () => { if (x.o) taste.banCultures.push(x.o); return x.o ? `fewer ${x.o} names` : "noted"; },
    "the sound": () => `fewer names that sound like ${name}`,
  }[reason];
  const said = msg ? msg() : `fewer names like ${name}`;
  taste.log.push(said); saveTaste();
  return said;
}
const tasteReset = () => { taste = { love: [], hate: [], banCultures: [], maxLen: 0, minLen: 0, popCap: 0, log: [] }; saveTaste(); };
// does a melody climb, fall or stay level? (the shape of its last step)
function contour(n) {
  const t = MB.melody(n).ev.filter(e => e.kind === "main").map(e => e.i);
  if (t.length < 2) return 0;
  return Math.sign(t[t.length - 1] - t[0]);
}
function tasteMatches(k = 6) {
  const p = buildProfile();
  if (!p) return { p: null, list: [] };
  const list = candidates().map(x => ({ x, s: scoreName(x, p) })).sort((a, b) => b.s.total - a.s.total).slice(0, k)
    .map(({ x, s }) => Object.assign(Object.create(x), x, { match: s }));
  const c = taste.love.map(contour), up = c.filter(v => v > 0).length, down = c.filter(v => v < 0).length;
  p.melody = up > down * 1.5 ? "melodies that rise" : down > up * 1.5 ? "melodies that settle down" : "melodies that stay close to home";
  return { p, list };
}
