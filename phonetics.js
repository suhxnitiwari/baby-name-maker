// ─────────────────────────────────────────────────────────────
// HOW A NAME SOUNDS: pronunciation first, spelling second.
// A name becomes phonemes (ARPAbet), then syllables with stress, then the music box plays those.
//   1. a pronunciation dictionary when it knows the name (CMU Pronouncing Dictionary, data/pron.json)
//   2. otherwise the sound rules of the name's language (Spanish j is h, Italian ci is chee, German w is v…)
//   3. or how YOU say it: when a name has more than one honest reading, you pick, and it's remembered
// Language decides the sounds. The same sound-to-music rules then apply to every name.
// ─────────────────────────────────────────────────────────────
const PH = (() => {
  let DICT = null;
  const KEY = "lullabyte-say";
  let chosen = (() => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch { return {}; } })();
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(chosen)); } catch {} };
  const fold = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[æǣǽ]/g, "a").replace(/[øǿ]/g, "o").replace(/œ/g, "oe").replace(/[ðđ]/g, "th").replace(/þ/g, "th").replace(/ß/g, "ss").replace(/ł/g, "l").replace(/ı/g, "i").replace(/ŋ/g, "ng").replace(/[^a-z]/g, "");   // for sound: Bjørn is bjorn, Þóra and Sigríðr have a th, Ælfric's æ is the a in cat

  // ── the sounds ──
  const VOWELS = new Set("AA AE AH AO AW AY EH ER EY IH IY OW OY UH UW O E".split(" "));
  // where each vowel sits on the pentatonic ladder (0 = C5 … 10 = C7): back/round vowels low, front/high vowels high.
  // A glide (diphthong) moves between two rungs.
  const RUNG = { UW: [2], UH: [2], OW: [3, 2], AO: [3], O: [3], AA: [4], AH: [4], ER: [4], AE: [5], EH: [5], E: [5], IH: [6], IY: [7], EY: [5, 7], AY: [4, 7], AW: [4, 2], OY: [3, 7] };
  const VOWEL_SAY = { UW: "“oo”, round and back", UH: "“uu”, round and back", OW: "“oh” gliding to “oo”", AO: "“aw”, open and back", O: "“o”, round", AA: "“ah”, open", AH: "“uh”, the middle of the mouth", ER: "“er”",
    AE: "“a” as in cat, front", EH: "“eh”, front", E: "“e”, front", IH: "“ih”, high and front", IY: "“ee”, the highest, frontmost vowel", EY: "“ay”, gliding up to “ee”", AY: "“eye”, gliding from “ah” to “ee”", AW: "“ow”, gliding from “ah” to “oo”", OY: "“oy”, gliding from “oh” to “ee”" };
  const PLACE = p => /^(P|B|M|F|V|W)$/.test(p) ? "lips" : /^(L|R)$/.test(p) ? "lr" : /^(T|D|N|S|Z|TH|DH|SH|ZH|CH|JH)$/.test(p) ? "tip" : /^(K|G|NG|Y)$/.test(p) ? "back" : p === "HH" ? "h" : "none";
  const LEAN = { lips: -1, lr: 1, tip: 2, back: 3, h: 0, none: 0 };                  // a small pitch nudge from where the consonant is made
  const LEAN_SAY = { lips: "made at the lips, it eases the note down a step", lr: "the L or R lifts it a step", tip: "made with the tongue tip, it lifts it two", back: "made at the back of the mouth, it lifts it three" };
  // how the note is played, from the consonant's manner: flowing sounds glide in, stops strike, fricatives breathe
  const MANNER = p => !p ? "soft" : /^(M|N|NG|L|R|W|Y)$/.test(p) ? "soft" : /^(B|D|G|JH)$/.test(p) ? "warm" : /^(P|T|K|CH)$/.test(p) ? "crisp" : "airy";
  const ART_SAY = { soft: "a soft, flowing start", warm: "a warm, voiced start", crisp: "a crisp, struck start", airy: "an airy, breathy start" };
  const ROUND = new Set("UW UH OW AO O OY M N NG L R W B D G".split(" ")), SHARP = new Set("IY IH EY EH E AE P T K CH S Z SH F TH".split(" "));

  // ── syllables from phonemes: every vowel is a nucleus; consonants between go to the next syllable when they can start one ──
  const ONSETS = new Set(("P R|B R|T R|D R|K R|G R|F R|TH R|SH R|P L|B L|K L|G L|F L|S L|S P|S T|S K|S M|S N|S W|T W|K W|D W|G W|TH W|" +
    "P Y|B Y|K Y|G Y|M Y|N Y|F Y|V Y|L Y|HH Y|S P R|S T R|S K R|S P L|S K W").split("|"));
  function syllabify(ph) {
    const out = []; let on = [];
    for (let k = 0; k < ph.length; k++) {
      const p = ph[k].replace(/\d/, "");
      if (!VOWELS.has(p)) { on.push(p); continue; }
      out.push({ on, v: p, co: [], stress: /\d/.test(ph[k]) ? +ph[k].match(/\d/)[0] : 0 });
      on = [];
    }
    if (!out.length) return [];
    out[out.length - 1].co = on;
    // split the consonants between two vowels: the longest legal onset goes right, the rest closes the syllable before
    for (let k = 1; k < out.length; k++) {
      const c = out[k].on;
      let take = 0;
      for (let n = Math.min(3, c.length); n >= 1; n--) if (n === 1 || ONSETS.has(c.slice(-n).join(" "))) { take = n; break; }
      out[k - 1].co = c.slice(0, c.length - take); out[k].on = c.slice(c.length - take);
    }
    return out;
  }

  // ── sound rules by language: letters → phonemes ──
  const PROFILE_OF = {
    en: "English American British Welsh", ga: "Irish Scottish Celtic Gaelic Breton",
    es: "Spanish Latin American Mexican Argentine Colombian Cuban Dominican Puerto Rican Catalan Galician Basque Filipino Chilean",
    it: "Italian Latin", pt: "Portuguese Brazilian", fr: "French",
    de: "German Dutch Austrian Swiss Afrikaner Frisian Yiddish",
    nordic: "Nordic Norse Swedish Norwegian Danish Icelandic Faroese Finnish Estonian Sámi Greenlandic",
    pl: "Polish", slavic: "Slavic Russian Ukrainian Czech Slovak Serbian & Croatian Slovene Bulgarian Macedonian Belarusian Latvian Lithuanian Baltic",
    hu: "Hungarian", gr: "Greek", tr: "Turkish Azerbaijani Kazakh Uzbek Turkmen Kyrgyz Tatar Bashkir Central Asian Mongolian",
    fa: "Persian Afghan Kurdish Tajik Pashtun", ar: "Arab Arabic Urdu Somali Sudanese South Sudanese Nubian Muslim",
    he: "Hebrew Israeli Jewish Aramaic",
    in: "South Asian Indian Hindi Bengali Tamil Telugu Punjabi Gujarati Marathi Malayali Kannada Nepali Sanskrit Odia Assamese Sindhi Sinhala Tibetan",
    even: "Japanese Korean Chinese Vietnamese Thai Lao Khmer Burmese Yoruba Igbo Akan Ewe Hausa Taiwanese Indigenous",
    pac: "Hawaiian Māori Samoan Tongan Fijian Pacific Malay Indonesian Javanese",
    af: "African Swahili Zulu Xhosa Sotho Tswana Shona Kikuyu Chewa Ethiopian Oromo Congolese",
  };
  const PROFILE = {};
  for (const [p, list] of Object.entries(PROFILE_OF)) for (const c of list.split(" ")) PROFILE[c] = p;
  // multi-word culture names
  Object.assign(PROFILE, { "Old French": "fr", "Anglo-Norman": "fr", "Medieval English": "en", "Old English": "en", "Old Norse": "nordic", "Old Swedish": "nordic", "Azerbaijani": "tr",
    "Latin American": "es", "Puerto Rican": "es", "South Asian": "in", "Central Asian": "tr", "Serbian & Croatian": "slavic", "South Sudanese": "ar", "Taiwanese Indigenous": "even" });
  const LANG_NAME = { en: "English", ga: "Irish", es: "Spanish", it: "Italian", pt: "Portuguese", fr: "French", de: "German", nordic: "Nordic", pl: "Polish", slavic: "Slavic", hu: "Hungarian", gr: "Greek", tr: "Turkish", fa: "Persian", ar: "Arabic", he: "Hebrew", in: "South Asian", even: "", pac: "Pacific", af: "African" };

  // stress: where each language puts it
  const STRESS = { en: "en", ga: "first", de: "first", nordic: "first", hu: "first", es: "es", it: "penult", pt: "es", pl: "penult", slavic: "penult", gr: "penult", fr: "final", tr: "final", fa: "final", he: "final", ar: "weight", in: "weight", even: "even", pac: "penult", af: "penult" };

  function g2p(word, prof) {
    const accents = [];
    const raw = word.toLowerCase();
    raw.normalize("NFD").replace(/[a-z][́]/g, (m, i) => (accents.push(m[0]), m));        // an acute accent marks stress (José, Sofía)
    const acc = raw.normalize("NFD").replace(/[^a-ź]/g, "");
    let w = fold(word);
    if (!w) return [];
    const ph = [];
    const P = (...x) => ph.push(...x);
    const en = prof === "en" || prof === "ga";
    const pure = !en;
    const V = { a: pure ? "AA" : null, e: pure ? "EH" : null, i: "IY", o: pure ? "O" : null, u: "UW", y: "IY" };
    // English silent final e (Grace, Jane): the vowel before it says its name
    let magic = -1;
    if (en && /[aeiou][^aeiouy]e$/.test(w) && w.length > 3) magic = w.length - 3;
    if (prof === "fr" && /e$/.test(w) && w.length > 2) w = w.slice(0, -1);                   // French final e is silent
    if (prof === "fr") w = w.replace(/(?<=[aeiou][^aeiou]*)[stdxzp]$/, "");                   // …and most final consonants
    for (let k = 0; k < w.length;) {
      const r = w.slice(k), c = w[k], next = w[k + 1] || "", prev = w[k - 1] || "";
      const two = r.slice(0, 2), three = r.slice(0, 3), last = k === w.length - 1;
      const isV = ch => "aeiouy".includes(ch);
      // ── vowels ──
      if (isV(c) && !(c === "y" && isV(next))) {                                                // a y before a vowel is a consonant (Maya, Yara)
        if (prof === "fr" && (three === "eau")) { P("O"); k += 3; continue; }
        if (prof === "fr" && two === "ou") { P("UW"); k += 2; continue; }
        if (prof === "fr" && two === "oi") { P("W", "AA"); k += 2; continue; }
        if (prof === "fr" && (two === "au" || two === "eu")) { P(two === "au" ? "O" : "ER"); k += 2; continue; }
        if (prof === "fr" && two === "ai") { P("EH"); k += 2; continue; }
        if ((prof === "de" || prof === "nordic") && two === "ei") { P("AY"); k += 2; continue; }
        if ((prof === "de" || prof === "nordic") && two === "ie") { P("IY"); k += 2; continue; }
        if (prof === "de" && (two === "eu")) { P("OY"); k += 2; continue; }
        if (/^(ai|ay)/.test(r) && !(isV(w[k + 2] || "") && r[1] === "y")) { P(en ? "EY" : "AY"); k += 2; continue; }
        if (/^(ei|ey)/.test(r) && !(en && r === "ey")) { P("EY"); k += 2; continue; }
        if (/^(au|aw)/.test(r)) { P(en ? "AO" : "AW"); k += 2; continue; }
        if (/^(oi|oy)/.test(r) && !isV(w[k + 2] || "")) { P("OY"); k += 2; continue; }
        if (/^(ou|ow)/.test(r)) { P(en ? (last || k + 2 === w.length ? "OW" : "AW") : "UW"); k += 2; continue; }
        if (/^(ee|ea|ie)/.test(r) && !(two === "ie" && pure && k + 2 < w.length)) { P("IY"); k += 2; continue; }
        if (/^(oo|ue|ew)/.test(r)) { P("UW"); k += 2; continue; }
        if (/^(aa|ii|uu)/.test(r)) { P({ a: "AA", i: "IY", u: "UW" }[c]); k += 2; continue; }
        if (two === "oa") { P(en ? "OW" : "O", ...(en ? [] : ["AA"])); k += 2; continue; }
        if (k === magic) { P({ a: "EY", e: "IY", i: "AY", o: "OW", u: "UW", y: "AY" }[c]); k++; continue; }
        if (en && c === "e" && last && magic >= 0) { k++; continue; }
        if (en) {
          // English single vowels: closed syllables are short, open ones long, a final a is "uh"
          const closed = !isV(next) && next && (!isV(w[k + 2] || "") || next === w[k + 2]);
          const v = c === "a" ? (last ? "AH" : closed ? "AE" : "AA") : c === "e" ? (last ? "IY" : closed ? "EH" : "EH") :
            c === "i" ? (last || !closed ? "IY" : "IH") : c === "o" ? (closed ? "AA" : "OW") : c === "u" ? (closed ? "AH" : "UW") : (last ? "IY" : "IH");
          P(v); k++; continue;
        }
        P(V[c] || { a: "AA", e: "EH", o: "O" }[c]); k++; continue;
      }
      // ── consonants ──
      if (c === next && !isV(c)) { k++; continue; }                                            // doubled letters sound once
      if (three === "sch") { P(prof === "de" ? "SH" : "S", "K"); k += 3; continue; }
      if (prof === "it" && three.match(/^sc[ei]/)) { P("SH"); k += 2; continue; }
      if (prof === "it" && /^[cg]i[aeou]/.test(three)) { P(c === "c" ? "CH" : "JH"); k += 2; continue; }  // Giulia: the i only softens the g
      if (prof === "it" && three === "gli") { P("L", "Y"); k += 2; continue; }
      if ((prof === "it" || prof === "fr" || prof === "es") && two === "gn") { P("N", "Y"); k += 2; continue; }
      if (prof === "es" && two === "ll") { P("Y"); k += 2; continue; }
      if (two === "ph") { P(prof === "in" ? "P" : "F"); k += 2; continue; }
      if (two === "th") { P(en || prof === "gr" ? "TH" : "T"); k += 2; continue; }
      if (two === "sh") { P("SH"); k += 2; continue; }
      if (two === "ch") { P(prof === "fr" ? "SH" : prof === "de" || prof === "it" || prof === "nordic" || prof === "slavic" || prof === "pl" ? "K" : "CH"); k += 2; continue; }
      if (two === "zh") { P("ZH"); k += 2; continue; }
      if (two === "kh" || two === "gh") { P(c === "k" ? "K" : "G"); k += 2; continue; }
      if (/^[bdj]h/.test(two) && prof === "in") { P({ b: "B", d: "D", j: "JH" }[c]); k += 2; continue; }
      if (two === "ck") { P("K"); k += 2; continue; }
      if (two === "qu") { P(prof === "es" || prof === "fr" || prof === "pt" ? "K" : "K", ...(prof === "es" || prof === "fr" || prof === "pt" ? [] : ["W"])); k += 2; continue; }
      if (two === "wh") { P("W"); k += 2; continue; }
      if (two === "kn" && k === 0) { P("N"); k += 2; continue; }
      if (two === "ng" && !isV(w[k + 2] || "")) { P("NG"); k += 2; continue; }
      if (c === "c") { P(/[eiy]/.test(next) ? (prof === "it" ? "CH" : prof === "slavic" || prof === "pl" ? "T" : "S") : "K"); if (/[eiy]/.test(next) && (prof === "slavic" || prof === "pl")) P("S"); k++; continue; }
      if (c === "g") { P(/[eiy]/.test(next) && (prof === "it" || prof === "en" && k === 0) ? "JH" : /[eiy]/.test(next) && prof === "es" ? "HH" : /[eiy]/.test(next) && (prof === "fr" || prof === "pt") ? "ZH" : "G"); k++; continue; }
      if (c === "j") { P(prof === "es" ? "HH" : prof === "fr" || prof === "pt" ? "ZH" : "de nordic slavic pl hu".includes(prof) ? "Y" : "JH"); k++; continue; }
      if (c === "h") { if (prof !== "fr" && prof !== "es" && prof !== "it" && prof !== "pt" && !(k > 0 && !isV(prev))) P("HH"); k++; continue; }
      if (c === "w") { P("de nordic pl slavic".includes(prof) ? "V" : "W"); k++; continue; }
      if (c === "v") { P(prof === "de" ? "F" : "V"); k++; continue; }
      if (c === "x") { P(k === 0 ? "Z" : "K", ...(k === 0 ? [] : ["S"])); k++; continue; }
      if (c === "q") { P("K"); k++; continue; }
      if (c === "z") { P(prof === "de" || prof === "it" ? "T" : prof === "es" ? "S" : "Z", ...(prof === "de" || prof === "it" ? ["S"] : [])); k++; continue; }
      if (c === "y") { P("Y"); k++; continue; }
      if (c === "s") { P(prof === "hu" ? "SH" : "S"); k++; continue; }
      P({ b: "B", d: "D", f: "F", k: "K", l: "L", m: "M", n: "N", p: "P", r: "R", t: "T" }[c] || c.toUpperCase()); k++;
    }
    const syl = syllabify(ph);
    // stress
    const rule = STRESS[prof] || "penult";
    const n = syl.length, heavy = s => s.co.length > 0 || /^(AY|EY|OY|AW|OW|IY|UW)$/.test(s.v);
    let at = -1;
    const accented = accents.length ? (() => { const vs = (acc.match(/[aeiouy]́?/g) || []); const idx = vs.findIndex(v => v.length > 1); return idx; })() : -1;
    if (accented >= 0 && accented < n && /^(es|pt|it|gr)$/.test(prof)) at = accented;          // only there does an accent mark stress
    else if (n === 1 || rule === "first") at = 0;
    else if (rule === "final") at = n - 1;
    else if (rule === "penult") at = n - 2;
    else if (rule === "es") at = /[aeiouns]$/.test(w) ? n - 2 : n - 1;
    else if (rule === "weight") at = heavy(syl[n - 2]) || n === 2 ? n - 2 : Math.max(0, n - 3);
    else if (rule === "en") at = n >= 3 && /(ia|ea|io|ie)$/.test(w) ? n - 3 : n >= 3 && /(ina|ella|etta|anna|ana|ena|ara|ora|ita|ica)$/.test(w) ? n - 2 : 0;
    syl.forEach((s, k) => { s.stress = rule === "even" ? 0 : k === at ? 1 : 0; });
    // English: unstressed a / o / u reduce to "uh"
    if (en) syl.forEach((s, k) => { if (!s.stress && /^(AA|AE|O|OW)$/.test(s.v) && k > 0 && !(k === n - 1 && s.v === "OW")) s.v = "AH"; });
    return syl;
  }

  // ── how a pronunciation is written back for people: MY-uh, LAY-lah, NEEV ──
  const SAY_V = { AA: "ah", AE: "a", AH: "uh", AO: "aw", AW: "ow", AY: "eye", EH: "eh", ER: "er", EY: "ay", IH: "ih", IY: "ee", OW: "oh", OY: "oy", UH: "uu", UW: "oo", O: "o", E: "e" };
  const SAY_C = { CH: "ch", SH: "sh", TH: "th", DH: "th", ZH: "zh", JH: "j", NG: "ng", HH: "h" };
  function respell(syl) {
    return syl.map(s => {
      const on = s.on.map(p => SAY_C[p] || p.toLowerCase()).join(""), co = s.co.map(p => SAY_C[p] || p.toLowerCase()).join("");
      let v = SAY_V[s.v] || s.v.toLowerCase();
      if (s.v === "AY" && on) v = "y";                                                   // MY, not MEYE
      const t = on + v + co;
      return s.stress === 1 && syl.length > 1 ? t.toUpperCase() : t;
    }).join("-");
  }
  // and the other way: a respelling someone types ("mah-YAH") back into sounds
  const READ_V = [["eye", "AY"], ["ay", "EY"], ["ee", "IY"], ["ih", "IH"], ["eh", "EH"], ["ah", "AA"], ["aw", "AO"], ["oh", "OW"], ["oo", "UW"], ["ow", "AW"], ["oy", "OY"], ["uh", "AH"], ["er", "ER"], ["uu", "UH"], ["a", "AE"], ["e", "EH"], ["i", "IH"], ["o", "O"], ["u", "AH"], ["y", "AY"]];
  function read(text) {
    const parts = text.trim().split(/[-·\s]+/).filter(Boolean);
    const anyCaps = parts.some(p => p === p.toUpperCase() && /[A-Z]/.test(p)) && parts.some(p => p !== p.toUpperCase());
    return parts.map((part, k) => {
      const p = part.toLowerCase(), ph = [];
      let v = null;
      for (let i = 0; i < p.length;) {
        const hit = !v && READ_V.find(([s]) => p.startsWith(s, i) && !(s === "y" && i === 0));
        if (hit) { v = hit[1]; ph.push("|" + v); i += hit[0].length; continue; }
        const two = p.slice(i, i + 2), c = { ch: "CH", sh: "SH", th: "TH", zh: "ZH", ng: "NG" }[two];
        if (c) { ph.push(c); i += 2; continue; }
        ph.push({ j: "JH", h: "HH", y: "Y", c: "K", q: "K", x: "K" }[p[i]] || p[i].toUpperCase()); i++;
      }
      const vi = ph.findIndex(x => x[0] === "|");
      if (vi < 0) return null;
      return { on: ph.slice(0, vi), v: ph[vi].slice(1), co: ph.slice(vi + 1), stress: anyCaps ? (part === part.toUpperCase() ? 1 : 0) : k === 0 ? 1 : 0 };
    }).filter(Boolean);
  }

  // ── the name's language, from what Lullabyte knows about it ──
  function cultures(name) {
    if (typeof BY_NAME === "undefined") return [];
    const xs = BY_NAME.get(fold(name)) || [];
    return [...new Set(xs.flatMap(x => [x.o, ...(x.oo || [])]).filter(Boolean))];
  }
  const profileOf = name => { for (const c of cultures(name)) if (PROFILE[c]) return PROFILE[c]; return null; };

  // every honest reading of a name, best first
  function options(word) {
    const k = fold(word), out = [], seen = new Set();
    const add = (syl, source) => { if (!syl.length) return; const r = respell(syl); if (seen.has(r.toLowerCase())) return; seen.add(r.toLowerCase()); out.push({ syl, source, say: r }); };
    const prof = profileOf(word);
    const dict = DICT && DICT[k];
    const native = prof && prof !== "en" && prof !== "ga";
    // a name the dictionary knows is a name in everyday English use: its usual reading leads, its language's reading follows.
    // A name it doesn't know is sounded out by the rules of its own language first.
    if (dict) dict.forEach((p, i) => p[0] === "!" ? add(syllabify(p.slice(1).split(" ")), "checked by hand") : add(syllabify(p.split(" ")), i ? "another common way" : "usual English pronunciation"));
    if (native) add(g2p(word, prof), `${LANG_NAME[prof] || cultures(word)[0]} pronunciation`);
    if (!dict && !native) add(g2p(word, prof || "en"), prof === "ga" ? "sounded out" : "sounded out the English way");
    if (native && !dict) add(g2p(word, "en"), "sounded out the English way");
    return out;
  }
  // the reading to use: yours if you chose one, else the first
  function word(w) {
    const k = fold(w), opts = options(w);
    const mine = chosen[k];
    if (mine) {
      const hit = opts.find(o => o.say.toLowerCase() === mine.toLowerCase());
      if (hit) return { ...hit, mine: true, opts };
      const own = read(mine);
      if (own.length) return { syl: own, source: "how you say it", say: respell(own), mine: true, opts };
    }
    return { ...(opts[0] || { syl: [], source: "", say: "" }), opts };
  }
  // round ◯ … sharp ◇: from the name's sounds (an artistic reading of sound symbolism, not a verdict)
  function shape(syl) {
    let r = 0, s = 0;
    for (const x of syl) for (const p of [...x.on, x.v, ...x.co]) { if (ROUND.has(p)) r++; if (SHARP.has(p)) s++; }
    return (s - r) / (r + s + 2);                                                       // a short name only leans a little
  }
  function choose(w, say) { const k = fold(w); if (say) chosen[k] = say; else delete chosen[k]; save(); if (typeof MB !== "undefined") MB.reset(); dispatchEvent(new CustomEvent("say", { detail: w })); }
  function load(d) { DICT = d; if (typeof MB !== "undefined") MB.reset(); dispatchEvent(new Event("pron")); }

  return { word, options, respell, read, shape, choose, load, PLACE, LEAN, MANNER, RUNG, VOWEL_SAY, LEAN_SAY, ART_SAY, get ready() { return !!DICT; } };
})();
