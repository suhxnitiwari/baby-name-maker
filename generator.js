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
  ["Brave & fierce", /brave|bold|warrior|battle|\bwar\b|fierce|lion|wolf|\bbear\b|spear|sword|hero|valor|courage|fight|eagle|hunt|thunder|army|compeller/],
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
