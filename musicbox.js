// ─────────────────────────────────────────────────────────────
// THE MUSIC BOX: every name is a lullaby.
// A name is split into syllables; each vowel sound picks a tooth on a 15-tooth comb,
// the consonant before it colors the attack, and every tune comes home to low C.
// Names that sound alike (Layla / Leila / Laila) punch the same holes.
// ─────────────────────────────────────────────────────────────
const MB = (() => {
  // 15 teeth, C major from C5 (0) to C7 (14)
  const COMB = [72, 74, 76, 77, 79, 81, 83, 84, 86, 88, 89, 91, 93, 95, 96];
  const NOTE_NAMES = ["C5", "D5", "E5", "F5", "G5", "A5", "B5", "C6", "D6", "E6", "F6", "G6", "A6", "B6", "C7"];
  const STEP = 0.21; // seconds per step: an unhurried lullaby
  const flat = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z]/g, "");
  const V = "aeiouy";
  const isV = (w, i) => V.includes(w[i]) && !(w[i] === "y" && (i === 0 || V.includes(w[i + 1] || "") && w[i + 1] !== "y"));
  const ONSET2 = new Set("bl br ch cl cr dr fl fr gl gr kh kl kr ph pl pr sc sh sk sl sm sn sp st sw th tr tw wh bh dh gh jh".split(" "));

  // Notes live on a pentatonic ladder (no note can clash): C D E G A, over two octaves.
  const PENTA = [0, 1, 2, 4, 5, 7, 8, 9, 11, 12, 14];
  // vowel sound → rung on the ladder (one rung, or a glide of two)
  function nucleus(v, magic) {
    if (magic) return { a: [4, 6], i: [4, 7], o: [3], u: [2], e: [7], y: [4, 7] }[v[0]] || [4];
    if (/^(ai|ay|ei|ey|ae)/.test(v)) return [4, 6];   // Layla, Jayden: ah → ay glide
    if (/^(oi|oy)/.test(v)) return [3, 7];
    if (/^(au|aw)/.test(v)) return [3];
    if (/^(oo|ou|u|ew)/.test(v)) return [2];          // dark and round
    if (/^(ee|ea|ie|i|y)/.test(v)) return [7];        // bright
    if (v[0] === "o") return [3];
    if (v[0] === "e") return [5];
    return [4];                                        // open "ah", the middle of the comb
  }
  // the consonant before the vowel bends the note: lips low, tongue-tip high
  function lean(on) {
    const c = on.replace(/^h/, "")[0];
    if (!c) return 0;
    if ("bpmfvw".includes(c)) return -1;
    if ("lr".includes(c)) return 1;
    if ("dtnszx".includes(c)) return 2;
    return /^(sh|ch|th)/.test(on) ? 2 : "kgcqjy".includes(c) ? 3 : 0;
  }
  const rung = r => PENTA[Math.max(0, Math.min(PENTA.length - 1, r))];

  // Split a name into syllables, keeping letter positions so Mom + Dad colors line up.
  function syllables(word) {
    const w = flat(word).replace(/([aeiou])h$/, "$1"); // Sarah = Sara, Laylah = Layla
    const runs = [];
    for (let i = 0; i < w.length;) {
      if (!isV(w, i)) { i++; continue; }
      let j = i; while (j < w.length && isV(w, j)) j++;
      const r = w.slice(i, j);
      // two-vowel runs that are really two syllables: Mi·a, Ame·li·a, Jul·i·o, Josh·u·a, Zo·e
      if (r.length === 2 && (/^[ieu][ao]$/.test(r) || r === "oe" && j === w.length)) { runs.push([i, i + 1]); runs.push([i + 1, j]); }
      else runs.push([i, j]);
      i = j;
    }
    if (!runs.length) return { w, syl: [{ s: 0, e: w.length, on: w, nuc: "a", co: "" }] };
    // silent final e (Grace, Jane): drop it and make the vowel before it long
    let magic = false;
    const lastR = runs[runs.length - 1];
    if (runs.length > 1 && w.endsWith("e") && lastR[0] === w.length - 1 && !isV(w, w.length - 2)) {
      const prev = runs[runs.length - 2];
      const gap = w.slice(prev[1], w.length - 1);
      runs.pop();
      magic = gap.length === 1 && prev[1] - prev[0] === 1 && !/^(elle|ette)$/.test(w.slice(-4));
    }
    const syl = runs.map(([s, e], k) => ({ ns: s, ne: e, nuc: w.slice(s, e) }));
    // hand the consonants between vowels to the syllables around them
    for (let k = 0; k < syl.length; k++) {
      const a = syl[k], b = syl[k + 1];
      if (k === 0) a.s = 0;
      if (!b) { a.e = w.length; continue; }
      const mid = w.slice(a.ne, b.ns);
      let cut = a.ne;
      if (mid.length === 1) cut = a.ne;
      else if (mid.length >= 2) cut = ONSET2.has(mid.slice(-2)) ? b.ns - 2 : b.ns - 1;
      a.e = cut; b.s = cut;
    }
    for (const x of syl) { x.on = w.slice(x.s, x.ns); x.co = w.slice(x.ne, x.e); }
    if (magic) syl[syl.length - 1].magic = true;
    return { w, syl };
  }

  // name → events on the comb. t is in steps, i is the tooth, v is how hard it's plucked.
  function phrase(word, t0, ev, owners) {
    const { syl } = syllables(word);
    let t = t0;
    syl.forEach((x, k) => {
      const first = k === 0, last = k === syl.length - 1;
      const rungs = nucleus(x.nuc, x.magic).map(r => r + lean(x.on)), teeth = rungs.map(rung);
      const on = x.on.replace(/^h/, "");
      const hard = /^(b|d|g|k|p|t|c(?![eiyh])|q|j|x)/.test(on), hiss = /^(s|z|sh|ch|f|v|th|c(?=[eiy]))/.test(on);
      const v = first ? 1 : last ? .82 : .74;
      const len = first && syl.length > 1 ? 2 : last ? (x.co ? 2 : 3) : 1;
      const own = owners ? majority(owners, x.s, x.e) : "";
      teeth.forEach((i, g) => {
        ev.push({ t: t + g * .5, i, v: g ? v * .8 : v, kind: "main", syl: k, own });
      });
      if (hard) ev.push({ t, i: rung(rungs[0] - 2), v: v * .55, kind: "pluck", syl: k, own });
      if (hiss && rungs[0] + 5 < PENTA.length) ev.push({ t, i: rung(rungs[0] + 5), v: v * .32, kind: "spark", syl: k, own });
      t += Math.max(len, teeth.length > 1 ? 1.5 : 1);
    });
    return { t, syl };
  }
  const majority = (owners, s, e) => {
    const c = {}; for (let i = s; i < e; i++) if (owners[i]) c[owners[i]] = (c[owners[i]] || 0) + 1;
    return Object.entries(c).sort((a, b) => b[1] - a[1])[0]?.[0] || "";
  };

  const cache = new Map();
  // melody("Amara") or melody("Amara", "Tiwari"); owners = per-letter source for Mom + Dad
  function melody(first, last = "", owners = null) {
    const key = first + "|" + last + "|" + (owners ? owners.join("") : "");
    if (cache.has(key)) return cache.get(key);
    const ev = [];
    const words = first.split(/[\s-]+/).filter(Boolean);
    let t = .5, off = 0, syl = [];
    for (const wd of words) {
      const own = owners ? owners.slice(off, off + flat(wd).length) : null;
      off += flat(wd).length;
      const p = phrase(wd, t, ev, own); syl.push(...p.syl); t = p.t + .5;
    }
    if (last) { t += .5; t = phrase(last, t, ev, null).t + .5; }
    ev.push({ t: t + .5, i: 0, v: .5, kind: "home" }); // every tune comes home to low C
    const m = { ev, steps: t + 2, syl };
    cache.set(key, m);
    return m;
  }

  // ── sound ──
  let ctx = null, bus = null;
  const PREF = "lullabyte-sound";
  let on = (() => { try { return localStorage.getItem(PREF) !== "off"; } catch { return true; } })();
  function ensure() {
    if (ctx) { if (ctx.state === "suspended") ctx.resume(); return ctx; }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
    const comp = ctx.createDynamicsCompressor(); comp.threshold.value = -16; comp.ratio.value = 3;
    bus = ctx.createGain(); bus.gain.value = .9;
    // a small warm room: generated impulse, mixed in quietly
    const verb = ctx.createConvolver(), len = ctx.sampleRate * 2.2, ir = ctx.createBuffer(2, len, ctx.sampleRate);
    for (let c = 0; c < 2; c++) { const d = ir.getChannelData(c); for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len) ** 3.2; }
    verb.buffer = ir;
    const wet = ctx.createGain(); wet.gain.value = .28;
    bus.connect(comp); bus.connect(verb); verb.connect(wet); wet.connect(comp); comp.connect(ctx.destination);
    return ctx;
  }
  // a music-box tine: bright attack, glassy partials, long soft ring
  function pluck(i, v = 1, when = 0) {
    if (!on || !ensure()) return;
    const t = Math.max(ctx.currentTime, when || ctx.currentTime) + .005;
    const f = 440 * 2 ** ((COMB[i] - 69) / 12), ring = 2.4 - i * .07;
    for (const [r, a] of [[1, 1], [2.001, .34], [3.02, .1], [4.17, .05], [5.43, .025]]) {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = "sine"; o.frequency.value = f * r;
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(.11 * v * a, t + .003);
      g.gain.exponentialRampToValueAtTime(.0001, t + ring / (r * .8));
      o.connect(g); g.connect(bus); o.start(t); o.stop(t + ring + .1);
    }
  }
  // tiny mechanical sounds: the crank's ratchet, the paper
  function tick(v = .4) {
    if (!on || !ensure()) return;
    const t = ctx.currentTime, b = ctx.createBuffer(1, 600, ctx.sampleRate), d = b.getChannelData(0);
    for (let k = 0; k < d.length; k++) d[k] = (Math.random() * 2 - 1) * (1 - k / d.length) ** 6;
    const s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain();
    f.type = "bandpass"; f.frequency.value = 3200; f.Q.value = 2; g.gain.value = .18 * v;
    s.buffer = b; s.connect(f); f.connect(g); g.connect(bus); s.start(t);
  }
  function setOn(v) { on = v; try { localStorage.setItem(PREF, v ? "on" : "off"); } catch {} if (v) ensure(); dispatchEvent(new Event("mbsound")); }

  // schedule a whole melody; returns its length in seconds
  function play(m, speed = 1) {
    const c = on && ensure(), t0 = c ? c.currentTime + .06 : 0;
    if (c) for (const e of m.ev) pluck(e.i, e.v, t0 + e.t * STEP / speed);
    return m.steps * STEP / speed;
  }

  // ── the paper strip: night-velvet paper, every note a lit hole, a gold thread through the tune ──
  const FILL = { a: "mom", b: "dad", f: "fam" };
  let defsDone = false;
  function defs() {
    if (defsDone || typeof document === "undefined" || !document.body) return;
    defsDone = true;
    const d = document.createElement("div");
    // felt beads: muted rainbow by pitch (low notes earthy, high notes airy), rose for Mom, blue for Dad, oat for family
    const felts = [["p0", "#b9a596", "#9c8576", "#7e6858"], ["p1", "#e08a76", "#c8644f", "#a44c3a"], ["p2", "#ecc06a", "#d9a441", "#b5832a"], ["p3", "#f0c4bc", "#e3a9a0", "#c4867c"],
      ["p4", "#b8cbad", "#9bb08f", "#7c9271"], ["p5", "#a6c4d2", "#7fa6b8", "#5f8698"], ["p6", "#bcaad3", "#9c86b5", "#7d6896"], ["p7", "#fbf5ea", "#efe4d3", "#d6c6ae"],
      ["mom", "#ef9aae", "#d26a83", "#a94c64"], ["dad", "#9cc3e0", "#5f8fb6", "#43708f"], ["fam", "#f0d59a", "#d9b46a", "#b48d43"], ["hole", "#f0d6b4", "#d1a87c", "#a87a4f"]];
    d.innerHTML = `<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>${
      felts.map(([id, a, b, c]) => `<radialGradient id="mb-${id}" cx=".38" cy=".34" r=".75"><stop offset="0" stop-color="${a}"/><stop offset=".6" stop-color="${b}"/><stop offset="1" stop-color="${c}"/></radialGradient>
          <radialGradient id="mb-${id}-halo"><stop offset="0" stop-color="#ffd98a" stop-opacity=".55"/><stop offset=".45" stop-color="#ffd98a" stop-opacity=".15"/><stop offset="1" stop-color="#ffd98a" stop-opacity="0"/></radialGradient>`).join("")
    }</defs></svg>`;
    document.body.prepend(d.firstElementChild);
  }
  // a smooth curve through points (Catmull-Rom → Bézier)
  function curve(P) {
    if (P.length < 2) return "";
    let d = `M${P[0][0].toFixed(1)},${P[0][1].toFixed(1)}`;
    for (let i = 0; i < P.length - 1; i++) {
      const p0 = P[i - 1] || P[i], p1 = P[i], p2 = P[i + 1], p3 = P[i + 2] || p2;
      d += ` C${(p1[0] + (p2[0] - p0[0]) / 6).toFixed(1)},${(p1[1] + (p2[1] - p0[1]) / 6).toFixed(1)} ${(p2[0] - (p3[0] - p1[0]) / 6).toFixed(1)},${(p2[1] - (p3[1] - p1[1]) / 6).toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
    }
    return d;
  }
  // rows are teeth (high notes at the top), columns are steps
  function stripSVG(m, o = {}) {
    defs();
    const cw = o.cw || 28, rh = o.rh || 7, pad = o.pad ?? rh, H = rh * 15 + pad * 2;
    const W = Math.ceil((m.steps + 1) * cw);
    const X = e => cw * .9 + e.t * cw + (e.kind === "home" ? cw * .3 : 0), Y = e => pad + (14 - e.i) * rh + rh / 2;
    const r = Math.min(rh * 1.3, cw * .34);
    const thread = curve(m.ev.filter(e => e.kind === "main" || e.kind === "home").sort((a, b) => a.t - b.t).map(e => [X(e), Y(e)]));
    const notes = m.ev.map((e, k) => {
      const x = X(e).toFixed(1), y = Y(e).toFixed(1), f = FILL[e.own] || "p" + Math.min(7, Math.round(e.i / 2)), own = e.own ? " o-" + e.own : "";
      if (e.kind === "home") return `<g class="n home" data-k="${k}"><circle class="halo" cx="${x}" cy="${y}" r="${r * 2.4}" fill="url(#mb-hole-halo)"/><circle class="ring" cx="${x}" cy="${y}" r="${r * .85}"/><circle class="core" cx="${x}" cy="${y}" r="${r * .26}" fill="url(#mb-hole)"/></g>`;
      if (e.kind !== "main") return `<g class="n ${e.kind}${own}" data-k="${k}"><circle class="core" cx="${x}" cy="${y}" r="${r * .4}" fill="url(#mb-${f})"/></g>`;
      return `<g class="n main${own}" data-k="${k}"><circle class="halo" cx="${x}" cy="${y}" r="${r * 2.7}" fill="url(#mb-${f}-halo)"/><ellipse class="shadow" cx="${(+x + r * .18).toFixed(1)}" cy="${(+y + r * .55).toFixed(1)}" rx="${r * .9}" ry="${r * .55}"/><circle class="core" cx="${x}" cy="${y}" r="${r}" fill="url(#mb-${f})"/><circle class="stitch" cx="${x}" cy="${y}" r="${r * .62}"/></g>`;
    }).join("");
    return { svg: `<svg class="holes" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" aria-hidden="true"><path class="thread" d="${thread}"/>${notes}</svg>`, W, H, cw };
  }
  const label = m => m.ev.filter(e => e.kind === "main").map(e => NOTE_NAMES[e.i]).join(" ");

  // Play a strip element: holes light up as a soft beam of light crosses the paper.
  let playing = null;
  function playEl(el, m, speed = 1) {
    if (playing) playing.stop();
    const band = el.querySelector(".band"), beam = el.querySelector(".beam");
    const byK = {}; el.querySelectorAll(".n").forEach(n => byK[n.dataset.k] = n);
    const cw = +(band && band.dataset.cw) || 28, dur = play(m, speed), t0 = performance.now() + 60;
    el.querySelectorAll(".n.lit").forEach(h => h.classList.remove("lit"));
    el.classList.add("playing");
    let raf = 0, done = false;
    const lit = new Set();
    const frame = now => {
      const s = (now - t0) / 1000 / (STEP / speed);
      if (beam) beam.style.transform = `translateX(${Math.max(0, cw * .9 + s * cw)}px)`;
      m.ev.forEach((e, k) => {
        if (e.t <= s && !lit.has(k)) {
          lit.add(k);
          const h = byK[k]; if (h) { h.classList.remove("lit"); void h.getBBox?.(); h.classList.add("lit"); }
          if (e.kind === "main" || e.kind === "home") dispatchEvent(new CustomEvent("mbnote", { detail: { i: e.i, el } }));
        }
      });
      if ((now - t0) / 1000 < dur + .3 && !done) raf = requestAnimationFrame(frame); else stop();
    };
    const stop = () => { if (done) return; done = true; cancelAnimationFrame(raf); el.classList.remove("playing"); setTimeout(() => el.querySelectorAll(".n.lit").forEach(h => h.classList.remove("lit")), 900); if (playing && playing.el === el) playing = null; };
    raf = requestAnimationFrame(frame);
    playing = { el, stop };
    return dur;
  }

  return { melody, syllables, stripSVG, play, playEl, pluck, tick, ensure, label, STEP, COMB, NOTE_NAMES,
    get on() { return on; }, setOn, stopAll: () => playing && playing.stop() };
})();
