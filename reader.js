// ─────────────────────────────────────────────────────────────
// THE READER: what a parent's own words ask for, as the filters Find already understands.
// The assistant (worker/lullabyte-ai.js) does this with a language model; this file is the plain version that runs
// on the device when the assistant can't be reached, and the one the local test worker stands in with.
// Both answers pass through Reader.clean, so only these keys and values ever reach the search:
//   { gender, syl: [lo, hi], len, feel, origins: [], meanings: [], like: [], notLike: [], easy, notPopular, starts, ends }
// It never names a name of its own: like and notLike only hold names the parent wrote.
// ─────────────────────────────────────────────────────────────
(() => {
  const FEELS = ["soft", "bold", "elegant", "timeless", "modern", "playful", "rare"];
  const LENS = ["3-4", "5-6", "7-8", "9-99"];
  const NUM = { one: 1, two: 2, three: 3, four: 4, five: 5, single: 1, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5 };
  const word = s => String(s || "").normalize("NFC").trim();
  const nameLike = s => /^[\p{L}][\p{L}'’-]{0,24}$/u.test(s);
  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
  const uniqBy = (a, k = x => x.toLowerCase()) => a.filter((x, i) => a.findIndex(y => k(y) === k(x)) === i);

  // anything, from the model or from here, becomes this shape or is dropped
  function clean(raw) {
    const r = raw && typeof raw === "object" ? raw : {};
    const list = (v, max, ok) => uniqBy((Array.isArray(v) ? v : typeof v === "string" ? v.split(/[,;/]| or | and /) : []).map(word).filter(ok)).slice(0, max);
    const out = {};
    if (["girl", "boy", "either"].includes(r.gender)) out.gender = r.gender;
    const syl = Array.isArray(r.syl) ? r.syl.map(Number) : null;
    if (syl && syl.length === 2 && syl.every(n => Number.isInteger(n) && n >= 1 && n <= 6) && syl[0] <= syl[1]) out.syl = syl;
    if (LENS.includes(r.len)) out.len = r.len;
    if (FEELS.includes(r.feel)) out.feel = r.feel;
    out.origins = list(r.origins, 4, s => /^[\p{L} '’-]{2,30}$/u.test(s)).map(cap);
    out.meanings = list(r.meanings, 4, s => /^[\p{L} '’-]{2,24}$/u.test(s)).map(s => s.toLowerCase());
    out.like = list(r.like, 6, nameLike).map(cap);
    out.notLike = list(r.notLike, 6, nameLike).map(cap);
    if (r.easy === true) out.easy = true;
    if (r.notPopular === true) out.notPopular = true;
    const letters = (v, max) => typeof v === "string" && /^[a-z]{1,5}$/i.test(v.replace(/^-|-$/g, "")) ? v.replace(/^-|-$/g, "").toLowerCase().slice(0, max) : "";
    if (letters(r.starts, 3)) out.starts = letters(r.starts, 3);
    if (letters(r.ends, 5)) out.ends = letters(r.ends, 5);
    return out;
  }

  // origins people say, in their own words (the page maps them onto its cultures)
  const ORIGIN_WORDS = ["Arabic", "Hindi", "Indian", "Sanskrit", "Hebrew", "Greek", "Latin", "Irish", "Gaelic", "Celtic", "Welsh", "Scottish", "English",
    "Persian", "Turkish", "Urdu", "Punjabi", "Tamil", "Telugu", "Bengali", "Gujarati", "Marathi", "Japanese", "Korean", "Chinese", "Vietnamese", "Filipino",
    "Spanish", "French", "Italian", "Portuguese", "German", "Dutch", "Norse", "Scandinavian", "Swedish", "Norwegian", "Danish", "Finnish", "Russian", "Slavic",
    "Polish", "Ukrainian", "Armenian", "Georgian", "African", "Yoruba", "Igbo", "Swahili", "Akan", "Zulu", "Hawaiian", "Māori", "Maori", "Pacific", "Biblical", "Muslim", "Hindu", "Jewish", "Sikh"];
  const FEEL_WORDS = [[/\b(soft|sweet|gentle|delicate)\b/, "soft"], [/\b(strong|bold|powerful|fierce)\b/, "bold"], [/\b(romantic|elegant|graceful|pretty)\b/, "elegant"],
    [/\b(classic|timeless|traditional|old[- ]fashioned|vintage)\b/, "timeless"], [/\b(modern|trendy|fresh|contemporary)\b/, "modern"], [/\b(playful|cute|fun|spunky)\b/, "playful"],
    [/\b(rare|unique|unusual|uncommon|different)\b/, "rare"]];
  const STOP = new Set("a an the something anything like that which with and or but not no our we us i my me for of to in on it is be our".split(" "));

  function read(text) {
    const t = " " + word(text).replace(/[“”]/g, '"') + " ", low = t.toLowerCase(), out = {};
    if (/\b(gender[- ]neutral|unisex|either|neutral|for any gender)\b/.test(low)) out.gender = "either";
    else if (/\b(girl|daughter|she|her)\b/.test(low)) out.gender = "girl";
    else if (/\b(boy|son|he|him|his)\b/.test(low)) out.gender = "boy";
    // syllables: "two syllables", "no more than 3 syllables", "one or two syllables"; "short" alone means one or two
    const range = low.match(/\b(one|two|three|four|1|2|3|4)\s*(?:or|to|-)\s*(two|three|four|five|2|3|4|5)\s+syllables?/);
    const most = low.match(/\b(?:no more than|at most|up to|max(?:imum)?)\s+(one|two|three|four|1|2|3|4)\s+syllables?/);
    const exact = low.match(/\b(one|two|three|four|single|1|2|3|4)[- ]syllables?\b/) || low.match(/\b(one|two|three|four|1|2|3|4)\s+syllables?/);
    if (range) out.syl = [NUM[range[1]], NUM[range[2]]];
    else if (most) out.syl = [1, NUM[most[1]]];
    else if (exact) out.syl = [NUM[exact[1]], NUM[exact[1]]];
    else if (/\b(short|little|tiny|simple)\b/.test(low) && !/\bshort (form|for)\b/.test(low)) out.syl = [1, 2];
    else if (/\b(long|grand|longer)\b/.test(low)) out.syl = [3, 6];
    for (const [re, f] of FEEL_WORDS) if (re.test(low)) { out.feel = f; break; }
    out.origins = ORIGIN_WORDS.filter(o => new RegExp(`\\b${o}\\b`, "i").test(t));
    // "means light or moon", "meaning peace", "a name that means 'gift of god'"
    const mean = low.match(/\bmean(?:s|ing)?\s+(?:something\s+(?:like|about)\s+)?([^.;!?]+)/);
    if (mean) out.meanings = mean[1].split(/\b(?:for|starts?|starting|ends?|ending|with|but|that)\b/)[0].split(/,|\bor\b|\band\b|\//).filter(p => !/spell|syllab|root|short|long|letter|start|end|popular|sound|\blike\b/.test(p))
      .flatMap(p => p.replace(/["'‘’]/g, "").trim().split(/\s+/).filter(w => w && !STOP.has(w)));
    // names they wrote: after love / like / similar to / such as, and the ones to stay away from
    const names = (re) => [...t.matchAll(re)].flatMap(m => m[1].split(/,|\band\b|\bor\b|&|\//)).map(s => s.trim().split(/\s+/)[0]).filter(s => /^[A-ZÀ-ÖØ-Þ][\p{L}'’-]+$/u.test(s));
    out.notLike = names(/\b(?:[Nn]ot|[Nn]othing|[Nn]o)\s+(?:like|similar to)?\s*((?:[A-Z][\p{L}'’-]+(?:\s*,\s*|\s+(?:and|or)\s+)?)+)/gu);
    const loved = names(/\b(?:[Ll]ove|loves|[Ll]ike|liked|[Aa]dore|[Ss]imilar to|[Ss]uch as|along the lines of|vibe of|feel of)\s+((?:[A-Z][\p{L}'’-]+(?:\s*,\s*|\s+(?:and|or)\s+|\s*&\s*)?)+)/gu);
    out.like = loved.filter(n => !out.notLike.includes(n) && !ORIGIN_WORDS.includes(n));
    if (/\beasy\s+to\s+spell|\beasy\s+spelling|\bsimple\s+spelling|\bspell(?:ed)?\s+easily|\bno one will misspell\b/.test(low)) out.easy = true;
    if (/\bnot\s+(?:too\s+)?(?:popular|common|trendy)|\bnot in the top\b|\bnobody else has\b/.test(low)) out.notPopular = true;
    const st = low.match(/\bstart(?:s|ing)?\s+with\s+(?:an?\s+)?["']?([a-z]{1,3})\b/), en = low.match(/\bend(?:s|ing)?\s+(?:in|with)\s+(?:an?\s+)?["'-]?([a-z]{1,5})\b/);
    if (st && (st[1].length <= 2 || !STOP.has(st[1]))) out.starts = st[1];
    if (en && !STOP.has(en[1])) out.ends = en[1];
    return clean(out);
  }

  const Reader = { read, clean, FEELS, LENS };
  if (typeof module !== "undefined") module.exports = Reader;
  globalThis.Reader = Reader;
})();
