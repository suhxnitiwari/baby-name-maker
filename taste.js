// ─────────────────────────────────────────────────────────────
// TASTE: remembers the names you turned down, and sinks names that sound like them.
// Uses globals from app.js (fold, vibeOf, popRanks, BY_NAME, gender, soundKey) and MB.
// ─────────────────────────────────────────────────────────────
const TASTE_KEY = "bnm-taste-v1";
let taste = (() => { try { return JSON.parse(localStorage.getItem(TASTE_KEY)) || null; } catch { return null; } })()
  || { love: [], hate: [], banCultures: [], maxLen: 0, minLen: 0, popCap: 0, log: [] };
const saveTaste = () => { try { localStorage.setItem(TASTE_KEY, JSON.stringify(taste)); } catch {} };

const cap1 = s => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();

// Turn a typed name into a name object: our data if we have it, otherwise a plain record.
function nameObj(n) {
  const known = (BY_NAME.get(fold(n)) || []).find(x => x.g === gender || x.g === "either") || (BY_NAME.get(fold(n)) || [])[0];
  return known || { n, g: gender, o: "", l: "", r: [], m: "", src: "", type: "attested" };
}
const bigrams = n => { const w = "^" + fold(n) + "$"; const s = new Set(); for (let i = 0; i < w.length - 1; i++) s.add(w.slice(i, i + 2)); return s; };
const dice = (a, b) => { let k = 0; for (const x of a) if (b.has(x)) k++; return (2 * k) / (a.size + b.size || 1); };
const bestRank = n => (popRanks(n, gender)[0] || [0, 99999])[1];

// ── Use it ──
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
