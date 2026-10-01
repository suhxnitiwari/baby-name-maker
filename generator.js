// ─────────────────────────────────────────────────────────────
// 1. ROOT NAMES: built the traditional way, from meaningful parts.
//    Sanskrit, Greek, Germanic and Norse names really were formed by
//    joining two elements (Dev + ansh, Theo + dora, Wil + helm, Thor + stein),
//    and many Arabic names are "servant of" one of God's names.
// ─────────────────────────────────────────────────────────────
const parse = s => s.trim().split(/\s*;\s*/).map(x => x.split("|"));
const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
const isVowel = c => "aeiou".includes(c);
// Join two parts; when vowel meets vowel, drop the first one (Chandra + esh → Chandresh).
const glue = (a, b) => isVowel(a.slice(-1)) && isVowel(b[0]) ? a.slice(0, -1) + b : a + b;
const fill = (tpl, p) => tpl.replace("{p}", p);

const ROOTS = {
  sanskrit: {
    culture: "Indian", lang: "Sanskrit",
    pre: parse(`Dev|the gods|H; Raj|kings; Surya|the sun|H; Chandra|the moon|H; Indra|Indra|H; Hari|Vishnu|H; Shiv|Shiva|H;
      Gyan|knowledge; Prem|love; Jay|victory; Anand|joy; Amar|immortality; Arun|the dawn; Ravi|the sun; Kiran|light;
      Krishna|Krishna|H; Ram|Rama|H; Shri|radiance; Satya|truth; Dharma|righteousness; Shubh|good fortune; Param|the supreme;
      Divya|the divine; Madhu|sweetness; Sundar|beauty; Hem|gold; Kamal|the lotus; Megh|the clouds; Akash|the sky;
      Agni|fire|H; Sagar|the ocean; Shant|peace; Daya|compassion; Man|the heart; Yash|glory; Rup|beauty; Tej|brilliance;
      Bhanu|the sun; Som|the moon; Nav|newness; Jeev|life; Uday|the rising sun; Vidya|learning; Neel|the blue sky;
      Rishi|the sages; Sukh|happiness; Vir|bravery; Nand|delight; Pran|the life breath; Gopal|Krishna|H; Ganga|the Ganges|H;
      Shakti|strength|H; Bal|strength; Vasu|wealth; Jyoti|light; Kirti|fame; Shobha|splendor; Padma|the lotus;
      Kusum|flowers; Mani|jewels; Hans|the swan; Sur|the gods|H; Mahi|the earth; Ujjwal|brightness`),
    boy: parse(`esh|lord of {p}; endra|chief of {p}; ansh|part of {p}; raj|king of {p}; deep|lamp of {p}; nath|master of {p};
      kant|beloved of {p}; pal|protector of {p}; anand|joy of {p}; prakash|light of {p}; kumar|prince of {p}; dutt|gift of {p};
      jeet|victorious through {p}; sagar|ocean of {p}; bhushan|ornament of {p}; vardhan|one who increases {p};
      tej|brilliance of {p}; veer|hero of {p}; mitra|friend of {p}; dev|god of {p}`),
    girl: parse(`ika|little one of {p}; ini|full of {p}; shree|radiance of {p}; priya|beloved of {p}; lata|vine of {p};
      mala|garland of {p}; rekha|ray of {p}; prabha|glow of {p}; kala|art of {p}; nandini|daughter of {p};
      sudha|nectar of {p}; jyoti|light of {p}; tara|star of {p}; vati|full of {p}; leela|play of {p}; gita|song of {p};
      devi|goddess of {p}; kanti|beauty of {p}; rani|queen of {p}; mukhi|with a face like {p}`),
    religion: p => p[2] === "H" ? ["Hindu"] : [],
  },
  greek: {
    culture: "Greek", lang: "Greek",
    pre: parse(`Theo|God|theo; Philo|love|phil; Niko|victory|nik; Alexi|defense; Kalli|beauty; Agatho|goodness; Andro|courage|andr;
      Christo|Christ|C; Demo|the people|dem; Kleo|glory|kle; Eu|goodness|eu; Aristo|excellence; Dio|Zeus|M; Lysi|freedom;
      Pan|all; Poly|many; Timo|honor|tim; Xeno|guests; Chryso|gold; Leo|the lion; Hiero|the sacred; Thrasy|boldness`),
    boy: parse(`dore|gift of {p}; krates|power of {p}; kles|glory of {p}|kle; nikos|victory of {p}|nik; medes|counsel of {p};
      genes|born of {p}; phanes|shining with {p}; machos|fighting with {p}; philos|friend of {p}|phil; demos|{p} of the people|dem;
      laos|{p} of the people|dem; stratos|{p} of the army; doulos|servant of {p}; ander|man of {p}|andr; timos|honoring {p}|tim`),
    girl: parse(`dora|gift of {p}; kleia|glory of {p}|kle; nike|victory of {p}|nik; phila|beloved of {p}|phil;
      thea|goddess of {p}|theo; doxa|praise of {p}; mache|battle of {p}`),
    religion: p => p[2] === "C" ? ["Christian"] : p[2] === "M" ? ["Greek myth"] : [],
  },
  germanic: {
    culture: "German", lang: "Germanic", plain: true,
    pre: parse(`Adal|noble; Bern|bear; Ed|wealthy; Alf|elf; Os|divine; Wil|will; Hild|battle|hild; Ger|spear|gar; Gund|war|gund;
      Ro|fame; Sieg|victory; Fried|peace|fred; Hein|home; Lud|renowned; Ric|ruler|ric; Diet|the people; Wolf|wolf|ulf;
      Arn|eagle; Bald|bold; Ethel|noble; Leof|dear; Mild|gentle`),
    boy: parse(`bert|bright; helm|protection; mund|protector; ric|ruler|ric; wald|power; win|friend; ward|guardian;
      fred|peace|fred; hard|strong; mar|famous; ulf|wolf|ulf; gar|spear|gar; wig|warrior`),
    girl: parse(`hild|battle|hild; gard|protection; trude|strength; burga|fortress; lind|gentle; run|secret;
      wina|friend; frida|peace|fred; gund|war|gund`),
    religion: () => [],
  },
  norse: {
    culture: "Norse", lang: "Old Norse", plain: true,
    pre: parse(`Thor|Thor|M; Sig|victory; Ragn|counsel of the gods; Ulf|wolf|ulf; As|divine; Ing|the god Ing|M; Gud|God;
      Hall|rock; Arn|eagle; Frey|lord Freyr|M; Sol|sun; Svan|swan; Kol|dark; Vig|battle; Bjorn|bear|bjorn; Gunn|war; Stein|stone|stein`),
    boy: parse(`vald|ruler; mund|protection; leif|heir; ulf|wolf|ulf; bjorn|bear|bjorn; geir|spear; stein|stone|stein;
      var|guardian; fast|firm; kel|helmet; rik|ruler`),
    girl: parse(`hild|battle; run|secret lore; dis|goddess; veig|strength; frid|beauty; laug|devoted; gerd|protection; borg|help`),
    religion: p => p[2] === "M" ? ["Norse myth"] : [],
  },
};

function buildRootNames() {
  const out = [];
  for (const sys of Object.values(ROOTS)) {
    for (const gender of ["boy", "girl"]) {
      for (const p of sys.pre) for (const s of sys[gender]) {
        // skip the same root twice (Niko + nikos)
        if (p[2] && s[2] && p[2] === s[2]) continue;
        if (p[0].toLowerCase() === s[0]) continue;
        const n = cap(glue(p[0], s[0]));
        if (n.length > 13 || /(.)\1\1/i.test(n) || /[^aeiouy]{4}/i.test(n)) continue;
        const m = sys.plain ? `${p[1]}, ${s[1]}` : fill(s[1], p[1]);
        out.push({ n, g: gender, o: sys.culture, l: sys.lang, r: sys.religion(p), m,
          src: `built from ${sys.lang} roots: ${p[0].toLowerCase()} + ${s[0]}`, type: "root" });
      }
    }
  }
  // Arabic: Abdul + a name of God, X + uddin ("of the faith"), X + ullah ("of God")
  const GOD = parse(`Rahman|the Most Merciful; Rahim|the Most Compassionate; Malik|the King; Quddus|the Most Holy;
    Salam|the Source of Peace; Aziz|the Almighty; Jabbar|the Compeller; Khaliq|the Creator; Bari|the Originator;
    Ghaffar|the Ever-Forgiving; Wahhab|the Bestower; Razzaq|the Provider; Fattah|the Opener; Alim|the All-Knowing;
    Basit|the Expander; Latif|the Gentle; Khabir|the All-Aware; Halim|the Forbearing; Azim|the Magnificent;
    Ghafur|the Forgiving; Shakur|the Appreciative; Ali|the Most High; Kabir|the Most Great; Hafiz|the Preserver;
    Karim|the Most Generous; Mujib|the Responsive; Hakim|the All-Wise; Wadud|the Most Loving; Majid|the Glorious;
    Haqq|the Truth; Wakil|the Trustee; Hamid|the Praiseworthy; Hayy|the Ever-Living; Qayyum|the Self-Sustaining;
    Wahid|the One; Samad|the Eternal; Qadir|the All-Powerful; Nur|the Light; Hadi|the Guide; Badi|the Incomparable;
    Baqi|the Everlasting; Rashid|the Rightly Guiding; Sabur|the Patient; Jalil|the Majestic; Rauf|the Kind;
    Ghani|the Self-Sufficient; Muizz|the Honorer; Tawwab|the Accepter of Repentance`);
  for (const [w, m] of GOD) out.push({ n: `Abdul ${w}`, g: "boy", o: "Arab", l: "Arabic", r: ["Islamic"],
    m: `servant of ${m}`, src: `Abd (servant) + al-${w}, one of the 99 names of God`, type: "root" });
  const DIN = parse(`Salah|righteousness; Nur|light; Shams|sun; Jamal|beauty; Kamal|perfection; Najm|star; Saif|sword;
    Imad|pillar; Zia|radiance; Fakhr|pride; Moin|helper; Nasir|helper; Qamar|moon; Taj|crown; Badr|full moon;
    Izz|glory; Sharaf|honor; Hisam|sword; Siraj|lamp; Bahá|splendor`);
  for (const [w, m] of DIN) out.push({ n: `${w}uddin`, g: "boy", o: "Arab", l: "Arabic", r: ["Islamic"],
    m: `${m} of the faith`, src: `${w} + ad-Din (of the faith)`, type: "root" });
  const ULLAH = parse(`Habib|beloved; Rahmat|mercy; Saif|sword; Asad|lion; Fazl|grace; Hidayat|guidance; Inayat|favor;
    Karam|generosity; Nasr|victory; Ata|gift; Khalil|friend; Fath|victory; Ruh|spirit; Wali|friend; Aman|protection;
    Ihsan|excellence; Barakat|blessings; Amin|trust; Najib|nobility; Ubayd|little servant`);
  for (const [w, m] of ULLAH) out.push({ n: `${w}ullah`, g: "boy", o: "Arab", l: "Arabic", r: ["Islamic"],
    m: `${m} of God`, src: `${w} + Allah (God)`, type: "root" });
  const NOOR = parse(`Huda|guidance; Iman|faith; Ain|the eye; Jannah|paradise; Hayat|life; Sabah|the morning; Qamar|the moon; Islam|Islam`);
  for (const [w, m] of NOOR) out.push({ n: `Noor ul ${w}`, g: "girl", o: "Arab", l: "Arabic", r: ["Islamic"],
    m: `light of ${m}`, src: `Noor (light) + ${w}`, type: "root" });
  return out;
}

// ─────────────────────────────────────────────────────────────
// 2. INVENTED NAMES: syllable mashups, 100,000+ per gender.
// ─────────────────────────────────────────────────────────────
const PARTS = {
  girl: {
    start: `A Ad Al Am An Ar Au Bel Bri Ca Cal Ce Cla Co Da Del E El Em Ev Fa Fe Flo Gi Gwen Ha I Il Is Ja Jo Ka Ki La Le Li
      Lu Ma Mi Mo Na Ne No O Pe Ri Ro Sa Se Si So Ta Te Va Ve Vi Wi Ya Za Ze Ry Ari Eli Cora Lo Mei Noe Rae Tia Bea Fio Gia
      Lia Mae Sky Ash Ivy Bry Cle Dae Ema Fay Gem Hal Jes Kae Lyr Mar Nev Per Rhi Sel Tal Val Wyn Yva Zin`,
    mid: "la li le lo na ni ne no ra ri re ro ma mi me ta ti sa si se da di va vi ve ya ca ce ci ba be bi ly ny ry lia ria ola ena ise ana eli",
    end: "a ah ia ie y ey elle ella etta ette ina ine lyn ne na ra ssa ya ara ora ise anne aya ena ica ika ila ily essa iana ielle ri ani ali ari eya ova une isa lie lee nie sha",
  },
  boy: {
    start: `A Ab Al An Ar As Au Ba Be Bo Bra Ca Cal Cas Co Cy Da Dar De Do Dra E Ed El Em Ez Fa Fe Fin Gra Ha He Hu I Ja Je
      Jo Ju Ka Ke Ko La Le Lu Ma Mar Mi Na Ni O Or Ra Re Ro Sa Se Si Ta Te Tho Ty Va Vi Wil Za Ze Bren Cor Dex Gav Jas Kel
      Ron Tav Zan Ben Ash Bar Cad Dom Fen Gid Hal Jor Kas Lan Mal Nas Pax Ros Sev Tor Vas Wes Xan Yor Zev
      Bas Ely Hen Kal Lev Mat Nol Rad Sam Tam Vic Zak`,
    mid: "ba bi da de di do ga ka ki la le li lo ma mi mo na ne ni no ra re ri ro sa se si ta te ti to va vi za zi dri bri the xa",
    end: "an en in on er el ar or us as is os o io iel ius ian ias ett ton son den ric rick mir vin win ard ald iah ix ex ax ek ik ir ul ent eon ael ito ando ren dan ro ver",
  },
  either: {
    start: `A Al Ar Ash Au Bel Bo Ca Co Da Dar E El Em Ev Fin Ha I Is Ja Jo Ka Ke Ki La Le Lu Ma Mi Mo Na No O Pe Re Ri Ro
      Sa Se Sky Ta Te Va Vi Wil Wy Za Ze Ari Bri Cy Dex Ky Lo Max Nyx Quin Rae Ren Sol Tay`,
    mid: "la li le lo na ni ne no ra ri re ro ma mi ta ti sa si da di va vi ya ca ce ly ry ke ko ze",
    end: "i y ey en an er el is ie o ee ley ry rin lan ai ix ar ion yn",
  },
};

const OK_PAIRS = new Set(("bl br ch ck cl cr dr fl fr gl gr gw kl kr lb ld lf lk ll lm ln ls lt lv mb mm mp nd ng nn ns nt nc nz " +
  "ph pl pr rb rc rd rg rk rl rm rn rs rt rv sc sh sk sl sm sn sp ss st th tr tt wh ks").split(" "));
const OK_VOWELS = new Set("ia ie io ea ei au ai ue ua oe ae ee".split(" "));
const isV = c => "aeiouy".includes(c);

function sayable(name) {
  const w = name.toLowerCase();
  if (w.length < 3 || w.length > 10) return false;
  if (/(.)\1\1/.test(w) || /[aeiou]{3}/.test(w) || /[^aeiouy]{3}/.test(w)) return false;
  for (let i = 1; i < w.length; i++) {
    const a = w[i - 1], b = w[i], pair = a + b;
    if (!isV(a) && !isV(b) && !OK_PAIRS.has(pair)) return false;
    if (isVowel(a) && isVowel(b) && !OK_VOWELS.has(pair)) return false;
    if (a === "y" && b === "y") return false;
  }
  return true;
}

function join(parts) {
  return parts.reduce((acc, p) => {
    const last = acc.slice(-1).toLowerCase();
    return isV(last) && last === p[0] ? acc + p.slice(1) : acc + p;
  });
}

function vibe(name) {
  const w = name.toLowerCase();
  const soft = (w.match(/[lmnvwyh]/g) || []).length, hard = (w.match(/[kdtxzgbrp]/g) || []).length;
  if (w.length <= 4) return "short & sweet";
  if (soft > hard + 1) return "soft & melodic";
  if (hard > soft + 1) return "strong-sounding & bold";
  if (/(elle|ette|ine)$/.test(w)) return "elegant, French-inspired sound";
  if (/(ia|ella|ina|ara|ora)$/.test(w)) return "lyrical & romantic";
  if (/(us|ius|ian|ias)$/.test(w)) return "classical & regal sound";
  return "fresh & balanced";
}

function buildInvented(gender, taken) {
  const P = PARTS[gender], split = s => [...new Set(s.trim().split(/\s+/))];
  const starts = split(P.start), mids = split(P.mid), ends = split(P.end);
  const out = new Set();
  for (const s of starts) for (const e of ends) {
    const two = join([s, e]);
    if (sayable(two)) out.add(two);
    for (const m of mids) {
      const three = join([s, m, e]);
      if (sayable(three)) out.add(three);
    }
  }
  return [...out].filter(n => !taken.has(n.toLowerCase()))
    .map(n => ({ n, g: gender, o: "", l: "", r: [], m: vibe(n), src: "", type: "invented" }));
}

// ─────────────────────────────────────────────────────────────
// 3. MEANING THEMES: group meanings into feelings.
// ─────────────────────────────────────────────────────────────
const THEMES = [
  ["Beautiful", /beaut|pretty|lovel|handsome|\bfair\b|splendor|charm|ornament|jewel/],
  ["Feminine & graceful", /grace|gracious|lady|delicate|elegant|sweet|fairy|flower|blossom|\brose\b|jasmine|tulip|lotus|orchid|dove|swan|princess|vine|garland|goddess/],
  ["Kind & gentle", /kind|gentle|compassion|merc|caring|\bcare\b|generous|benevol|patient|forbear|tender|\bgood|pure|friend|helper|forgiv/],
  ["Strong", /strong|strength|might|power|steadfast|firm|endur|stone|rock|invincib|constant|holding fast|fortress|protect|guard|defen|helmet|pillar|almighty/],
  ["Brave & fierce", /brave|bold|warrior|battle|\bwar\b|fierce|lion|wolf|\bbear\b|spear|sword|\bhero\b|valor|courage|fight|eagle|hunt|thunder|army|compeller/],
  ["Wise", /wis|knowledge|counsel|intellect|\bmind|sage|learn|guid|truth|poet|seeing|scripture|knowing|aware/],
  ["Divine & faith", /\bgod|divine|holy|sacred|bless|heaven|angel|faith|worship|christ|anoint|paradise|spirit|prophet|servant of|saint|devot|prayer|enlighten|vishnu|shiva|krishna|rama\b|zeus|freyr|\bing\b|\bthor\b/],
  ["Light & sun", /light|bright|shin|radian|\bsun|dawn|lamp|glow|gold|torch|fire|\bray|brillian|morning/],
  ["Moon & stars", /moon|star|\bsky|pleiades|constellation|night|heavens/],
  ["Nature", /tree|leaf|laurel|\boak|earth|\bland\b|cloud|rain|snow|forest|wood|bird|river|\bsea\b|ocean|water|island|mountain|wind|breeze|green|garden|lotus|deer|seal|flower|palm|tulip|jasmine|orchid|swan|dove|ganges/],
  ["Royal & noble", /king|queen|prince|royal|ruler|\brule|noble|\blord|crown|commander|chief|well-born|regal|master|supreme|exalted|empress|majest|\bgreat|venerable/],
  ["Peace & calm", /peace|calm|tranquil|quiet|\brest\b|serene|\bsafe/],
  ["Love & joy", /love|beloved|joy|happ|laugh|bliss|delight|\bdear|cheer|lucky|pleasant|sweet/],
  ["Victory & glory", /victor|glory|fame|famous|renown|prais|honor|triumph|success|prosper|fortune|wealth|\brich|conquer|glorious/],
  ["Life & hope", /hope|\blife|living|alive|reborn|resurrection|spring|\bnew|immortal|nectar|everlasting|eternal/],
];
const THEME_ORDER = {
  girl: ["Beautiful", "Feminine & graceful", "Kind & gentle", "Love & joy", "Light & sun", "Moon & stars", "Nature", "Divine & faith",
    "Wise", "Royal & noble", "Peace & calm", "Life & hope", "Victory & glory", "Strong", "Brave & fierce"],
  boy: ["Strong", "Brave & fierce", "Royal & noble", "Victory & glory", "Wise", "Divine & faith", "Light & sun", "Nature",
    "Peace & calm", "Kind & gentle", "Love & joy", "Life & hope", "Beautiful", "Moon & stars", "Feminine & graceful"],
};
THEME_ORDER.either = THEMES.map(t => t[0]);

function themesOf(x) {
  if (x.t) return x.t;
  if (x.type === "invented") return (x.t = []);
  const text = `${x.m} ${x.src}`.toLowerCase().replace(/built from .* roots: .*/, "");
  return (x.t = THEMES.filter(([, re]) => re.test(text)).map(([name]) => name));
}

if (typeof module !== "undefined") module.exports = { buildRootNames, buildInvented, themesOf, sayable };

// ─────────────────────────────────────────────────────────────
// 4. SPELLING VARIATIONS: swap letter groups that sound the same.
//    Jayden ↔ Jaiden ↔ Jaydon, Myra ↔ Maira, Suhani ↔ Suhaani ↔ Suhanee
// ─────────────────────────────────────────────────────────────
const isCons = c => !!c && /[a-z]/.test(c) && !"aeiouy".includes(c);
// Each rule looks at position i of word w and returns [length matched, alternative spellings] or null.
const SPELL_RULES = [
  (w, i) => w.startsWith("aa", i) ? [2, ["aa", "a"]] : null,
  (w, i) => { // ai / ay before a consonant: Jaiden ↔ Jayden ↔ Jaeden, Maira ↔ Myra
    const g = w.slice(i, i + 2), next = w[i + 2];
    if ((g !== "ai" && g !== "ay") || !(isCons(next) || next === undefined)) return null;
    const opts = ["ai", "ay"];
    if (next && i > 0) opts.push("ae");
    if (isCons(w[i - 1]) && "rl".includes(next || "-")) opts.push("y");
    return [2, opts];
  },
  (w, i) => { // y between consonants: Myra ↔ Maira ↔ Mayra
    if (w[i] !== "y" || !isCons(w[i - 1]) || !isCons(w[i + 1])) return null;
    return [1, "rl".includes(w[i + 1]) ? ["y", "ai", "ay", "i"] : ["y", "i"]];
  },
  (w, i) => w.startsWith("ee", i) && i + 2 < w.length ? [2, ["ee", "i", "ea"]] : null,
  (w, i) => w.startsWith("oo", i) ? [2, ["oo", "u"]] : null,
  (w, i) => w.slice(i) === "iya" ? [3, ["iya", "ia", "iyah"]] : null, // Priya ↔ Pria
  (w, i) => w.startsWith("ah", i) && i + 2 === w.length ? [2, ["ah", "a"]] : null,
  (w, i) => (w.startsWith("ia", i) || w.startsWith("ya", i)) && i > 0 && isCons(w[i - 1]) ? [2, ["ia", "ya"]] : null,
  (w, i) => { // final -en/-an/-on/-yn: Jayden ↔ Jaydon ↔ Jaydyn
    const g = w.slice(i);
    if (w.length < 5 || !/^[aeoy]n$/.test(g) || !isCons(w[i - 1])) return null;
    return [2, ["en", "an", "on", "yn"]];
  },
  (w, i) => { // final -i/-ee/-y/-ie: Suhani ↔ Suhanee, Avery ↔ Averie
    const g = w.slice(i);
    if (w.length < 4 || !["i", "ee", "y", "ie"].includes(g) || !isCons(w[i - 1])) return null;
    return [g.length, g === "i" ? ["i", "ee", "ie"] : ["y", "ie", "ee", "i"]];
  },
  (w, i) => w[i] === "a" && i === w.length - 1 && w.length > 3 && isCons(w[i - 1]) ? [1, ["a", "ah"]] : null,
  (w, i) => w.startsWith("ck", i) ? [2, ["ck", "k"]] : null,
  (w, i) => w.startsWith("ph", i) ? [2, ["ph", "f"]] : null,
  (w, i) => (w[i] === "c" || w[i] === "k") && "aou".includes(w[i + 1] || "-") ? [1, ["c", "k"]] : null,
  (w, i) => /^(ll|nn|mm|tt|ss|rr)/.test(w.slice(i)) && i > 0 ? [2, [w.slice(i, i + 2), w[i]]] : null,
  (w, i) => "ln".includes(w[i]) && i > 0 && "aeiou".includes(w[i - 1]) && i + 2 === w.length && w[i + 1] === "a" ? [1, [w[i], w[i] + w[i]]] : null, // Ana ↔ Anna
  (w, i) => w[i] === "a" && isCons(w[i - 1]) && isCons(w[i + 1]) && /^(i|ee|ika|ita|ini|ya)$/.test(w.slice(i + 2)) ? [1, ["a", "aa"]] : null, // Suhani ↔ Suhaani
  (w, i) => w[i] === "u" && isCons(w[i - 1]) && isCons(w[i + 1]) ? [1, ["u", "oo"]] : null,          // Suraj ↔ Sooraj
];

function spellings(name, max = 12) {
  const w = name.toLowerCase();
  // split the word into fixed letters and swappable slots
  const slots = [];
  for (let i = 0; i < w.length;) {
    const hit = SPELL_RULES.map(r => r(w, i)).find(Boolean);
    if (hit) { slots.push({ orig: w.slice(i, i + hit[0]), opts: hit[1] }); i += hit[0]; }
    else { slots.push({ orig: w[i], opts: [w[i]] }); i++; }
  }
  const out = new Map(); // spelling → number of changes
  const walk = (k, acc, changes) => {
    if (changes > 2) return;
    if (k === slots.length) { if (!out.has(acc) || out.get(acc) > changes) out.set(acc, changes); return; }
    for (const o of slots[k].opts) walk(k + 1, acc + o, changes + (o === slots[k].orig ? 0 : 1));
  };
  walk(0, "", 0);
  const fmt = s => s.replace(/(^|[\s-])([a-z])/g, (m, a, b) => a + b.toUpperCase());
  return [...out].filter(([s]) => s !== w && !/(.)\1\1|ii|yy|aaa|yi|iy|y[^aeiou]y$/.test(s))
    .sort((a, b) => a[1] - b[1] || a[0].length - b[0].length)
    .slice(0, max).map(([s]) => fmt(s));
}
if (typeof module !== "undefined") module.exports.spellings = spellings;

// ─────────────────────────────────────────────────────────────
// 5. SPELLING FAMILIES: real-world spellings that letter swaps can't reach.
// ─────────────────────────────────────────────────────────────
const SPELLING_FAMILIES = `
Muhammad Mohammed Mohammad Mohamed Muhammed Mohamad Mehmet
Ahmad Ahmed Ahmet
Hussein Husain Hussain Hossein Huseyin
Hassan Hasan Hasaan
Yusuf Yousef Youssef Yusef Yousuf Joseph Josef Yosef
Ibrahim Ebrahim Ibraheem Abraham Avraham
Umar Omar Omer
Ali Aly
Sulaiman Suleiman Sulayman Suleyman Solomon Shlomo
Dawud Dawood Daoud Davud David Dovid
Ismail Ismael Ishmael Esmail
Yahya Yehia Yehya
Isa Eesa Esa
Musa Moosa Moussa Moses Moshe
Zakariya Zakaria Zakariyya Zachariah Zechariah
Ayyub Ayub Ayoub Job
Yunus Younes Younis Jonah Yonah
Harun Haroon Haroun Aaron Aharon
Zayd Zaid Zayed Zeid
Hamza Hamzah
Bilal Belal
Karim Kareem
Rashid Rasheed Rashed
Amir Ameer Emir
Zain Zayn Zane
Khalid Khaled
Tariq Tarik Tareq
Rayyan Rayan Raiyan
Abdul Rahman Abdurrahman Abdelrahman Abdul Rehman
Abdullah Abdallah Abdollah
Aisha Ayesha Aysha Aishah Ayşe Aicha
Fatima Fatimah Fatema Fatma
Zainab Zaynab Zeinab
Khadija Khadijah Khadeeja Hatice
Maryam Mariam Meryem Miriam Myriam Mary Maria Marie
Layla Leila Laila Leyla Lyla Laylah
Yasmin Yasmine Yasmeen Jasmine Jasmin Yasemin
Noor Nur Nour
Amina Aminah Ameena
Safiya Safiyya Safia
Salma Selma
Hana Hanna Hannah Hanah Chana
Huda Houda
Iman Eman
Inaya Inaaya Enaya
Zahra Zehra Zahraa
Sara Sarah Sarai Sarra
Krishna Krishn Krisna
Lakshmi Laxmi Lakshmee
Lakshman Laxman Lakshmana
Shiva Siva Shiv
Ganesh Ganesha Ganesan
Aarav Arav Aaraav
Ishaan Ishan
Aditya Adithya Aaditya
Arjun Arjan
Priya Pria Preeya
Meera Mira Mirabai
Pooja Puja
Siddharth Siddhartha Sidharth Siddhart
Gautam Gautham Gotama
Suhani Suhaani Suhanee
Amaira Amyra Amayra Amairah
Myra Maira Mayra Mairah
Ananya Anannya
Kavya Kaavya Kavia
Riya Ria Rhea Reya
Diya Dia Deeya
Saanvi Sanvi
Anaya Anaaya Anaiya
Ayaan Ayan
Vihaan Vihan
Reyansh Rayansh
Deepak Dipak
Deepika Dipika
Preeti Priti Prity
Neel Nil Neil
Rohan Rohaan
Vikram Bikram
Durga Durgaa
Radha Raadha
Gurpreet Gurprit
Isaac Isaak Izaak Yitzhak Itzhak
Jacob Jakob Yaakov Jakub Yakub Yaqub
Elijah Elias Eliyahu Ilyas Elia
Noah Nuh Noach
Rebecca Rebekah Rebekka Rivka
Rachel Rachael Rahel
Leah Lea Lia Leia
Elizabeth Elisabeth Elisabet Elizabet
Catherine Katherine Kathryn Katharine Catharine Kathrine Katerina
Stephen Steven Stefan Stephan Stefano Esteban
Philip Phillip Filip Felipe
Jonathan Johnathan Jonathon Yonatan
Michael Mikael Mikhail Michal Micheal Mikail
Gabriel Gavriel Jibril Gabriele
Daniel Danyal Daniyal Danial
Eli Ely
Benjamin Binyamin
Matthew Mathew Matteo Mateo Mattias
John Jon Juan Jean Johan Ivan Yahya
Christopher Kristopher Christoffer
Aiden Aidan Ayden Aden Aydin
Jayden Jaden Jaiden Jaydon Jadon Jaydin
Brayden Braden Braeden Braydon
Kaitlyn Caitlin Katelyn Kaitlin Caitlyn
Zoe Zoey Zoë Zoie
Chloe Khloe Cloe
Sophia Sofia Sophie Sofie
Isabel Isabelle Isobel Izabel Isabella Isabela
Lily Lillie Lilly Lili
Emily Emilie Emely
Avery Averie Averi
Riley Rylee Ryleigh Reilly
Hailey Haley Hayley Haleigh Hailee
Ashley Ashleigh Ashlee
Sean Shaun Shawn Shane
Eric Erik Erich
Alan Allan Allen Alun
Brian Bryan Brien
Nicholas Nicolas Nikolas Nikolaos Nicola
Cameron Kameron Camron
Caleb Kaleb
Kylie Kylee Kiley Kyleigh
Madison Madisyn Madyson
Mackenzie McKenzie Makenzie
Kayla Kaila Kaylah
Camila Camilla Kamila
Valentina Valentine
Lucia Lucía Luciana
Juliette Juliet Julieta
Natalie Nathalie Natalia
Yiannis Giannis Ioannis
Georgios Giorgos Yiorgos George Jorge
Dimitrios Demetrius Dmitri Dimitri
Konstantinos Constantine Konstantin
Alexander Alexandre Aleksandr Alejandro Alessandro Iskandar Sikandar
Sophia Sofiya
Saoirse Seersha
Niamh Neve Neeve
Aoife Eefa
Caoimhe Keeva
Siobhan Shivaun Chevonne
Sinead Shinead
Oisin Osheen
Cillian Killian Kilian
Ronan Rónán
Darragh Dara
Eoin Owen Ewan Euan
Liam William Wilhelm Guillermo
Freya Freja Freyja
Astrid Astri
Sigrid Siri
Erik Eirik
Bjorn Björn Bjoern
Ingrid Inger
Kai Kye
Mila Milla
Natasha Natascha
Tenzin Tenzing
`;

const accentless = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const FAMILY_OF = new Map();
for (const line of SPELLING_FAMILIES.trim().split("\n")) {
  // multi-word names like "Abdul Rahman" are kept together by splitting on 2+ spaces or known word count
  const parts = line.includes("Abdul") ? line.match(/Abdul \w+|\w+/g) : line.trim().split(/\s+/);
  for (const p of parts) {
    const k = accentless(p).replace(/\s/g, "");
    FAMILY_OF.set(k, [...new Set([...(FAMILY_OF.get(k) || []), ...parts])]);
  }
}

// ─────────────────────────────────────────────────────────────
// 6. SOUNDS-LIKE CODE: names that are pronounced the same get the same code.
//    Layla / Leila / Laila → "lEl*",  Muhammad / Mohammed → "mUh*m*d"
// ─────────────────────────────────────────────────────────────
function soundKey(name) {
  let w = accentless(name).replace(/[^a-z]/g, "");
  w = w.replace(/ph/g, "f").replace(/ck|q/g, "k").replace(/c(?=[eiy])/g, "s").replace(/c/g, "k").replace(/x/g, "ks")
    .replace(/z/g, "s").replace(/v/g, "f").replace(/([kgtdbp])h/g, "$1").replace(/sch/g, "sh")
    .replace(/([a-z])\1+/g, "$1")                 // collapse doubles: mm → m
    .replace(/([aeiou])h$/, "$1")                  // Sarah → Sara
    .replace(/([^aeiouy])e$/, "$1")                // silent final e: Catherine → Catherin
    .replace(/^y(?=[aeiou])/, "Y");                // keep a starting y consonant
  let out = "", first = true;
  for (const m of w.match(/[aeiouy]+|[^aeiouy]+/g) || []) {
    if (!/[aeiouy]/.test(m)) { out += m; continue; }
    if (first) { // the first vowel sound is the one that matters most
      out += /^(ai|ay|ei|ey|aye|ae)/.test(m) ? "E" : /^(ee|ea|ie|i|y)/.test(m) ? "I" : /^(oo|ou|u|o)/.test(m) ? "U" : m[0] === "e" ? "e" : "A";
      first = false;
    } else out += "*";
  }
  return out;
}

// All spellings for a name: real-world family spellings + same-sounding known names first, then rule-based guesses.
function spellingsOf(name, known = []) {
  const k = accentless(name).replace(/\s/g, "");
  const seen = new Set([k]), out = [];
  const add = (n, common) => { const key = accentless(n).replace(/\s/g, ""); if (!seen.has(key)) { seen.add(key); out.push({ n, common }); } };
  (FAMILY_OF.get(k) || []).forEach(n => add(n, true));
  const sk = soundKey(name);
  known.filter(n => soundKey(n) === sk).forEach(n => add(n, true));
  spellings(name, 16).forEach(n => add(n, false));
  return out;
}
if (typeof module !== "undefined") Object.assign(module.exports, { spellingsOf, soundKey, FAMILY_OF });

// ─────────────────────────────────────────────────────────────
// 7. VIBES: what a name feels like, from how it sounds + what it means.
//    soft (0 strong … 1 soft), modern (0 classic … 1 modern), elegant (0 playful … 1 elegant)
// ─────────────────────────────────────────────────────────────
const AURAS = { // [color 1, color 2] for the card glow: muted, earthy warm tones
  celestial: ["#b8933f", "#6e3b36"], earthy: ["#8f7a4e", "#c9ad7f"], regal: ["#a8843a", "#7d3b37"],
  fierce: ["#a4493a", "#c97a4a"], romantic: ["#c2685a", "#e0b39a"], spiritual: ["#c4843f", "#d9bf7a"],
  calm: ["#c9a07e", "#ddc9a8"], playful: ["#c9a24f", "#cf8a63"], modern: ["#b86a45", "#9a5a48"],
  timeless: ["#a88d70", "#d9c6a8"], bold: ["#9c3f33", "#c26a3d"], wise: ["#8a6436", "#c4a052"],
  warm: ["#c98652", "#dcb57c"], dreamy: ["#c47d66", "#d9b07a"], fresh: ["#b8933f", "#c98a5a"], strong: ["#8a3a30", "#b8743f"],
};
const THEME_VIBE = {
  "Moon & stars": "celestial", "Light & sun": "dreamy", "Nature": "earthy", "Royal & noble": "regal",
  "Brave & fierce": "fierce", "Strong": "bold", "Divine & faith": "spiritual", "Wise": "wise",
  "Love & joy": "warm", "Peace & calm": "calm", "Beautiful": "romantic", "Feminine & graceful": "romantic",
  "Kind & gentle": "calm", "Victory & glory": "regal", "Life & hope": "fresh",
};
// the most specific meaning wins the aura (Luna → celestial, not romantic)
const VIBE_PRIORITY = ["Moon & stars", "Light & sun", "Nature", "Wise", "Brave & fierce", "Divine & faith", "Royal & noble",
  "Peace & calm", "Love & joy", "Beautiful", "Feminine & graceful", "Strong", "Kind & gentle", "Victory & glory", "Life & hope"];
const clamp = v => Math.max(0, Math.min(1, v));

function vibeOf(x) {
  if (x.v) return x.v;
  const w = accentless(x.n).replace(/[^a-z]/g, ""), t = themesOf(x);
  const syl = (w.match(/[aeiouy]+/g) || []).length;
  const soft = (w.match(/[lmnvwyh]/g) || []).length, hard = (w.match(/[kdtxzgbpqc]/g) || []).length;
  const vow = (w.match(/[aeiou]/g) || []).length;
  let s = 0.45 + (soft + vow * 0.4 - hard * 1.1) / Math.max(w.length, 1) * 1.3 + (/[aeiy]$/.test(w) ? 0.15 : -0.05);
  if (t.includes("Strong") || t.includes("Brave & fierce")) s -= 0.25;
  if (t.includes("Feminine & graceful") || t.includes("Kind & gentle")) s += 0.2;
  let m = x.type === "invented" ? 0.72 : x.type === "root" ? 0.3 : x.r.length || x.src ? 0.22 : 0.42;
  if (/y[^aeiou]|(yn|lyn|den|don|ton|ley|lee|x|er|ix|ax)$/.test(w)) m += 0.18;
  if (w.length <= 3) m += 0.08;
  let e = 0.45 + (syl - 2) * 0.15 + (w.length >= 7 ? 0.1 : 0) - (w.length <= 4 ? 0.15 : 0);
  if (/(elle|ette|ia|ine|ora|ina|ius|ian|ienne|ique|anthe)$/.test(w)) e += 0.2;
  if (/(y|ie|ee|o|i|ix|ux)$/.test(w) && w.length <= 6) e -= 0.2;
  const v = { soft: clamp(s), modern: clamp(m), elegant: clamp(e) };
  // vibe words: meaning-based first, then sound-based
  const top = VIBE_PRIORITY.find(th => t.includes(th));
  const words = top ? [THEME_VIBE[top]] : [];
  const tough = words[0] === "bold" || words[0] === "fierce";
  if (v.soft > 0.66 && !tough) words.push(v.elegant > 0.6 ? "dreamy" : "soft");
  else if (v.soft < 0.34) words.push(t.includes("Brave & fierce") ? "fierce" : "bold");
  if (v.modern > 0.66) words.push(v.elegant < 0.4 ? "playful" : "modern");
  else if (v.modern < 0.34) words.push("timeless");
  if (v.elegant > 0.7 && !words.includes("dreamy")) words.push("elegant");
  else if (v.elegant < 0.3 && !words.includes("playful")) words.push("playful");
  const uniq = [...new Set(words)];
  if (uniq.length < 2) uniq.push(...(v.soft >= 0.5 ? ["warm", "fresh"] : ["strong", "bold"]).filter(x => !uniq.includes(x)).slice(0, 2 - uniq.length));
  v.words = uniq.slice(0, 3);
  v.aura = AURAS[v.words[0]] || AURAS.fresh;
  return (x.v = v);
}
if (typeof module !== "undefined") Object.assign(module.exports, { vibeOf });
