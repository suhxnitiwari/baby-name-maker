// ─────────────────────────────────────────────────────────────
// THE MOBILE: the first screen. Every name builds its own object.
// Each letter threads a bead onto the hoop; each syllable drops a felt charm on a string.
// The charm's shape is the vowel (oo moon, oh sun, ah cloud, eh drop, ee star, a glide is a bird),
// its color is the consonant before it, and its string length is the note: low notes hang long.
// No two names make the same mobile. Play it and the charms light up in order; drag to spin it.
// ─────────────────────────────────────────────────────────────
const Mobile = (() => {
  const cv = document.getElementById("mobile");
  if (!cv) return null;
  const ctx = cv.getContext("2d");
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const TAU = Math.PI * 2;
  const WOOD = ["#e2c29d", "#d1a87c", "#b98c5e"];
  // the consonant before a vowel colors its felt: lips rose, L/R wheat, tongue tip sage, back of the mouth slate, none cream
  const TINT = { lips: "#d9a79c", lr: "#e6cf9f", tip: "#b7c5aa", back: "#a3b7c6", h: "#d3c4ad", none: "#f4ebdc" };
  const cls = c => !c ? "none" : "bpmfvw".includes(c) ? "lips" : "lr".includes(c) ? "lr" : "dtnszx".includes(c) ? "tip" : c === "h" ? "h" : "back";
  const tintOf = on => TINT[cls(on.replace(/^h(?=.)/, "")[0])];
  const beadColor = c => "aeiouy".includes(c) ? null : TINT[cls(c)];
  const SHAPE = { 2: "moon", 3: "sun", 4: "cloud", 5: "drop", 7: "star" };
  const REST = [["cloud", 7, TINT.none], ["moon", 1, "#cdbfa9"], ["star", 10, "#e6cf9f"], ["cloud", 4, "#e2c3b5"], ["sun", 0, "#f4ebdc"], ["drop", 8, "#b9c6ae"]];

  let W = 0, H = 0, dpr = 1, S = 1, hx = 0, hookY = 0, ringY = 0, rx = 0, ry = 0, narrow = false;
  let name = "", mel = null, rot = .4, spin = .1, drag = null, tilt = 0, vtilt = 0, keyA = 0, hover = null;
  let strands = [], garland = [];
  const pendant = { len: 0, lenT: 0, v: 0, glow: 0, bob: 0, vb: 0 };
  let playing = null, last = performance.now(), visible = true, raf = 0;
  const noteFns = [], doneFns = [], sparks = [];

  function size() {
    const r = cv.getBoundingClientRect();
    dpr = Math.min(devicePixelRatio || 1, 2); W = r.width; H = r.height;
    cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    narrow = W < 760;
    hx = narrow ? W * .5 : W * .575;                          // the ring reaches back toward the headline
    rx = narrow ? Math.min(W * .36, 190) : Math.min(W * .285, H * .52, 480);
    S = rx / 300;
    ry = rx * .18;
    hookY = narrow ? 8 : 0;
    ringY = narrow ? H * .22 : H * .25;
    for (const s of strands) if (!s.dying) s.lenT = lenFor(s.i, s.rest);
    if (pendant.lenT) pendant.lenT = pendantLen();
  }
  // string length from the note: low notes hang long, so the melody is the mobile's silhouette
  // desktop strings run from ~half the screen to near the floor, so you stand underneath it
const lenFor = (i, rest) => (H - ringY) * (narrow ? .2 + (14 - i) / 14 * .42 : .3 + (14 - i) / 14 * .52) * (rest ? .95 : 1);
  const pendantLen = () => (H - ringY) * (.08 + Math.min(10, name.replace(/[^a-z]/gi, "").length) * .012);

  // ── a name → its parts ──
  function parts(n) {
    const words = n.split(/[\s-]+/).filter(Boolean), syl = [];
    for (const w of words) syl.push(...MB.syllables(w).syl.map(x => ({ ...x, letters: x.on + x.nuc + x.co })));
    return { syl, m: MB.melody(n || " "), letters: MB.syllables(words.join("")).w };
  }
  const makeStrand = o => ({ len: 0, lenT: 0, v: 0, swing: (Math.random() - .5) * .2, vs: 0, bob: 0, vb: 0, glow: 0, alpha: 1, dying: false, beads: [], ...o, aT: o.a });
  const nucRung = v => /^(oo|ou|u|ew)/.test(v) ? 2 : /^(ee|ea|ie|i|y)/.test(v) ? 7 : /^(au|aw)/.test(v) || v[0] === "o" ? 3 : v[0] === "e" ? 5 : 4;
  const retire = s => { s.dying = true; s.lenT = 0; };
  function load(n) {
    const prev = name;
    name = n;
    const { syl, m, letters } = parts(n);
    mel = m;
    if (!n) {
      // at rest: six quiet felt charms, the mobile before it has a name
      strands.filter(s => !s.dying && !s.rest).forEach(retire);
      if (!strands.some(s => s.rest && !s.dying)) REST.forEach(([kind, i, color], j) => strands.push(makeStrand({ rest: true, kind, i, color, a: j / REST.length * TAU, lenT: lenFor(i, true), r: 1, born: performance.now() + 200 + j * 110 })));
    } else {
      strands.filter(s => s.rest && !s.dying).forEach(retire);
      const mine = strands.filter(s => !s.dying && !s.rest), N = syl.length;
      syl.forEach((x, j) => {
        const notes = m.ev.filter(e => e.kind === "main" && e.syl === j);
        const i = notes.length ? notes[0].i : 4;
        const kind = notes.length > 1 ? "bird" : SHAPE[nucRung(x.nuc)];
        const r = (j === 0 && N > 1 ? 1.1 : 1) * (x.co && j === N - 1 ? .92 : 1);
        let s = mine[j];
        if (!s) { s = makeStrand({ i, a: j / N * TAU + .001 }); strands.push(s); }
        if (s.kind && s.kind !== kind) s.vs += .25;                        // a charm that changes shape swings
        Object.assign(s, { i, kind, color: tintOf(x.on), r, lenT: lenFor(i), aT: j / N * TAU, syl: j });
        // beads: one per letter of the syllable, falling into place on its string
        [...x.letters].forEach((c, b) => { if (!s.beads[b]) s.beads.push({ c, y: -.3, vy: 0 }); else s.beads[b].c = c; });
        s.beads.length = x.letters.length;
      });
      mine.slice(N).forEach(retire);
    }
    // the garland: every letter is a bead on the hoop
    const L = [...letters];
    const keep = garland.filter(g => !g.dying);
    L.forEach((c, k) => { if (!keep[k]) keep[k] = { c, dy: -80 * S, v: 0, alpha: 1 }; else keep[k].c = c; });
    keep.slice(L.length).forEach(g => Object.assign(g, { dying: true, v: 0 }));
    garland = [...keep.slice(0, L.length), ...keep.slice(L.length), ...garland.filter(g => g.dying)];
    // the hoop tips as weight goes on, then finds its balance
    if (n !== prev) { vtilt += (n.length >= prev.length ? 1 : -1) * .07 * (Math.random() * .6 + .7); pendant.lenT = n ? pendantLen() : 0; }
  }

  // ── drawing helpers ──
  function woodStroke(x1, y1, x2, y2, w) {
    const g = ctx.createLinearGradient(x1 - w, y1, x1 + w, y1 + w);
    g.addColorStop(0, WOOD[0]); g.addColorStop(.5, WOOD[1]); g.addColorStop(1, WOOD[2]);
    ctx.strokeStyle = g; ctx.lineWidth = w; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    ctx.strokeStyle = "rgba(255,255,255,.35)"; ctx.lineWidth = w * .18;
    ctx.beginPath(); ctx.moveTo(x1 - w * .2, y1 - w * .1); ctx.lineTo(x2 - w * .2, y2 - w * .1); ctx.stroke();
  }
  function ball(x, y, r) {
    const g = ctx.createRadialGradient(x - r * .35, y - r * .4, r * .1, x, y, r);
    g.addColorStop(0, "#f0d6b4"); g.addColorStop(.6, WOOD[1]); g.addColorStop(1, WOOD[2]);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
  }
  function shade(hex, p) {
    const n = parseInt(hex.slice(1), 16), f = v => Math.max(0, Math.min(255, v + p * 2.55 | 0));
    return `rgb(${f(n >> 16)},${f(n >> 8 & 255)},${f(n & 255)})`;
  }
  function felt(color, x, y, r) {
    const g = ctx.createRadialGradient(x - r * .3, y - r * .35, r * .1, x, y, r * 1.1);
    g.addColorStop(0, shade(color, 14)); g.addColorStop(1, shade(color, -16));
    return g;
  }
  const stitch = () => { ctx.strokeStyle = "rgba(90,70,55,.3)"; ctx.setLineDash([2, 3]); ctx.lineWidth = 1; };
  const unstitch = () => ctx.setLineDash([]);
  function cloud(x, y, r, color) {
    ctx.fillStyle = felt(color, x, y, r);
    ctx.beginPath();
    for (const [dx, dy, rr] of [[-.55, .12, .45], [-.15, -.2, .55], [.32, -.1, .5], [.62, .18, .38], [0, .22, .5]]) ctx.moveTo(x + dx * r + rr * r, y + dy * r), ctx.arc(x + dx * r, y + dy * r, rr * r, 0, TAU);
    ctx.fill();
    stitch(); ctx.beginPath(); ctx.moveTo(x - r * .45, y + r * .15); ctx.quadraticCurveTo(x, y - r * .15, x + r * .45, y + r * .12); ctx.stroke(); unstitch();
  }
  function moon(x, y, r, color) {
    ctx.fillStyle = felt(color, x, y, r);
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.arc(x - r * .42, y - r * .22, r * .8, 0, TAU, true); ctx.fill("evenodd");
    ctx.save(); ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.arc(x - r * .42, y - r * .22, r * .8, 0, TAU, true); ctx.clip("evenodd");
    ctx.strokeStyle = "rgba(110,85,65,.3)"; ctx.lineWidth = 1.2;
    for (let k = -2; k <= 3; k++) { ctx.beginPath(); ctx.moveTo(x + k * r * .25, y - r); ctx.quadraticCurveTo(x + k * r * .25 + r * .25, y, x + k * r * .25, y + r); ctx.stroke(); }
    ctx.restore();
  }
  const starPath = (x, y, r, inner) => { ctx.beginPath(); for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5, rr = k % 2 ? r * inner : r; ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } ctx.closePath(); };
  function star(x, y, r, color) {
    ctx.fillStyle = felt(color, x, y, r); starPath(x, y, r, .46); ctx.fill();
    stitch(); starPath(x, y, r * .72, .46); ctx.stroke(); unstitch();
  }
  function sun(x, y, r, color) {
    ctx.fillStyle = felt("#e6cf9f", x, y, r);
    ctx.beginPath();
    for (let k = 0; k < 24; k++) { const a = k / 24 * TAU, rr = k % 2 ? r * .74 : r; ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); }
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = felt(color, x, y, r * .6); ctx.beginPath(); ctx.arc(x, y, r * .58, 0, TAU); ctx.fill();
    stitch(); ctx.beginPath(); ctx.arc(x, y, r * .44, 0, TAU); ctx.stroke(); unstitch();
  }
  function drop(x, y, r, color) {
    ctx.fillStyle = felt(color, x, y + r * .2, r);
    ctx.beginPath(); ctx.moveTo(x, y - r * 1.05);
    ctx.bezierCurveTo(x + r * .35, y - r * .5, x + r * .85, y, x + r * .8, y + r * .35);
    ctx.arc(x, y + r * .35, r * .8, 0, Math.PI);
    ctx.bezierCurveTo(x - r * .85, y, x - r * .35, y - r * .5, x, y - r * 1.05); ctx.fill();
    stitch(); ctx.beginPath(); ctx.arc(x, y + r * .35, r * .5, Math.PI * .1, Math.PI * .9); ctx.stroke(); unstitch();
  }
  function bird(x, y, r, color) {
    ctx.fillStyle = felt(color, x, y, r);
    ctx.beginPath(); ctx.ellipse(x, y, r * .95, r * .6, 0, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.arc(x + r * .72, y - r * .42, r * .38, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.moveTo(x - r * .8, y - r * .1); ctx.lineTo(x - r * 1.45, y - r * .55); ctx.lineTo(x - r * 1.3, y + r * .15); ctx.closePath(); ctx.fill();
    ctx.fillStyle = "#c99a4c"; ctx.beginPath(); ctx.moveTo(x + r * 1.06, y - r * .5); ctx.lineTo(x + r * 1.32, y - r * .42); ctx.lineTo(x + r * 1.06, y - r * .32); ctx.fill();
    ctx.fillStyle = "rgba(90,70,55,.16)"; ctx.beginPath(); ctx.ellipse(x - r * .1, y - r * .05, r * .5, r * .3, -.4, 0, TAU); ctx.fill();
    ctx.fillStyle = "#3a2a24"; ctx.beginPath(); ctx.arc(x + r * .82, y - r * .48, r * .06, 0, TAU); ctx.fill();
  }
  function bead(x, y, r, color) {
    if (!color) { ball(x, y, r); return; }                                  // vowels are wooden beads, consonants felt
    ctx.fillStyle = felt(color, x, y, r); ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    ctx.fillStyle = "rgba(255,255,255,.22)";
    for (let k = 0; k < 5; k++) { ctx.beginPath(); ctx.arc(x + Math.cos(k * 1.3) * r * .5, y + Math.sin(k * 1.7) * r * .45, r * .12, 0, TAU); ctx.fill(); }
  }
  function charm(kind, x, y, r, color) {
    if (kind === "cloud") cloud(x, y + r * .3, r, color);
    else if (kind === "moon") moon(x, y + r * .55, r * .9, color);
    else if (kind === "star") star(x, y + r * .7, r * .85, color);
    else if (kind === "sun") sun(x, y + r * .75, r * .78, color);
    else if (kind === "drop") drop(x, y + r * .9, r * .72, color);
    else if (kind === "bird") bird(x, y + r * .55, r * .78, color);
  }
  // a point on the hoop, after the hoop's tilt
  const onRing = a => {
    const x = Math.cos(a + rot) * rx, y = Math.sin(a + rot) * ry;
    return { x: hx + x * Math.cos(tilt) - y * Math.sin(tilt), y: ringY + x * Math.sin(tilt) + y * Math.cos(tilt), d: Math.sin(a + rot) };
  };

  function draw() {
    ctx.clearRect(0, 0, W, H);
    const lift = Math.min(1, scrollY / (H || 1));
    // the mobile's soft shadow on the wall drifts as you scroll, like the light is moving
    let g = ctx.createRadialGradient(hx + 40 * S + lift * 60, ringY + 260 * S, 10, hx + 40 * S + lift * 60, ringY + 260 * S, rx * 1.7);
    g.addColorStop(0, `rgba(120,90,60,${.11 - lift * .05})`); g.addColorStop(1, "rgba(120,90,60,0)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);

    // the cot arm comes in from the right: a beech pole and a long arm up to the hook
    const box = hookY + 64 * S, prx = 40 * S, pry = 48 * S;
    if (!narrow) {
      const jx = Math.min(W - 46, hx + rx + 150 * S), jy = ringY + 70 * S, tx = hx + 30 * S, ty = Math.max(14, hookY + 12 * S);
      woodStroke(jx, H + 40, jx, jy, 22 * S); woodStroke(jx, jy, tx, ty, 15 * S); ball(jx, jy, 25 * S); ball(tx, ty, 16 * S);
      ctx.strokeStyle = "#8d8f93"; ctx.lineWidth = 1.6 * S; ctx.beginPath(); ctx.moveTo(tx, ty + 6 * S); ctx.quadraticCurveTo(hx + 10 * S, box - pry - 14 * S, hx, box - pry); ctx.stroke();
    } else { ctx.strokeStyle = "rgba(205,188,160,.9)"; ctx.lineWidth = 1.4; ctx.beginPath(); ctx.moveTo(hx, 0); ctx.lineTo(hx, box - pry); ctx.stroke(); }
    // the wooden music box, with a winding key that turns while it plays
    g = ctx.createLinearGradient(hx - prx, box, hx + prx, box); g.addColorStop(0, WOOD[2]); g.addColorStop(.35, "#ecd2b0"); g.addColorStop(1, WOOD[1]);
    ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(hx, box, prx, pry, 0, 0, TAU); ctx.fill();
    ctx.strokeStyle = "rgba(140,100,60,.25)"; ctx.lineWidth = 1;
    for (let k = -3; k <= 3; k++) { ctx.beginPath(); ctx.ellipse(hx + k * 2, box, prx * (.25 + Math.abs(k) * .2), pry * .92, 0, -1.2, 1.2); ctx.stroke(); }
    const kx = hx + prx + 12 * S, ky = box - 4 * S, kw = Math.abs(Math.cos(keyA)) * 9 * S;
    ctx.strokeStyle = "#a88a5c"; ctx.lineWidth = 3 * S; ctx.beginPath(); ctx.moveTo(hx + prx - 2 * S, ky); ctx.lineTo(kx, ky); ctx.stroke();
    ctx.fillStyle = "#c9a46a"; ctx.beginPath(); ctx.ellipse(kx + 2 * S, ky - 9 * S, Math.max(1.5, kw), 9 * S, 0, 0, TAU); ctx.ellipse(kx + 2 * S, ky + 9 * S, Math.max(1.5, kw), 9 * S, 0, 0, TAU); ctx.fill();
    ball(kx + 2 * S, ky, 4 * S);

    // strings from the box to the hoop
    const knotY = box + pry + 24 * S;
    ctx.strokeStyle = "#e9dcc6"; ctx.lineWidth = 2 * S; ctx.beginPath(); ctx.moveTo(hx, box + pry); ctx.lineTo(hx, knotY); ctx.stroke();
    ctx.strokeStyle = "rgba(225,210,185,.85)"; ctx.lineWidth = 1.1;
    for (const a of [0, TAU / 4, TAU / 2, TAU * .75]) { const p = onRing(a); ctx.beginPath(); ctx.moveTo(hx, knotY); ctx.lineTo(p.x, p.y); ctx.stroke(); }

    const ring = (a0, a1) => {
      ctx.save(); ctx.translate(hx, ringY); ctx.rotate(tilt);
      ctx.strokeStyle = WOOD[2]; ctx.lineWidth = 14 * S; ctx.beginPath(); ctx.ellipse(0, 3 * S, rx, ry, 0, a0, a1); ctx.stroke();
      ctx.strokeStyle = WOOD[1]; ctx.lineWidth = 11 * S; ctx.beginPath(); ctx.ellipse(0, 0, rx, ry, 0, a0, a1); ctx.stroke();
      ctx.strokeStyle = "rgba(255,240,215,.75)"; ctx.lineWidth = 2.5 * S; ctx.beginPath(); ctx.ellipse(0, -4 * S, rx, ry, 0, a0, a1); ctx.stroke();
      ctx.restore();
    };
    // what hangs from the hoop, sorted back to front: strands, the garland, the pendant in the middle
    const items = [];
    for (const s of strands) { const p = onRing(s.a); items.push({ d: p.d, f: () => drawStrand(s, p) }); }
    const live = garland.filter(b => !b.dying).length || 1;
    let k = 0;
    for (const b of garland) { const a = b.dying ? (b.a ?? .21) : (b.a = (k++ + .5) / live * TAU + .21), p = onRing(a); items.push({ d: p.d, f: () => drawBead(b, p) }); }
    items.push({ d: 0, f: drawPendant });
    ring(Math.PI, TAU);
    items.sort((a, b) => a.d - b.d).forEach(it => it.f());
    ring(0, Math.PI);

    for (let j = sparks.length - 1; j >= 0; j--) {
      const q = sparks[j]; q.life -= .014; if (q.life <= 0) { sparks.splice(j, 1); continue; }
      q.x += q.vx; q.y += q.vy; q.vy += .015;
      ctx.fillStyle = `rgba(201,154,76,${q.life})`; ctx.font = `${Math.round(13 * S + 4)}px serif`; ctx.textAlign = "center"; ctx.fillText(q.c, q.x, q.y);
    }
  }
  function drawStrand(s, p) {
    const depth = .8 + .2 * (p.d + 1) / 2, L = Math.max(0, s.len + s.bob);
    if (L < 1) return;
    const ex = p.x + Math.sin(s.swing) * L, ey = p.y + Math.cos(s.swing) * L;
    ctx.globalAlpha = Math.max(0, s.alpha) * (.6 + .4 * depth);
    ctx.strokeStyle = "rgba(205,188,160,.95)"; ctx.lineWidth = 1.1; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(ex, ey); ctx.stroke();
    const nb = s.beads.length;
    s.beads.forEach((b, k) => {
      const slot = .16 + (k + .5) / Math.max(nb, 1) * .5, f = b.y * slot;                 // b.y runs from above the hoop (<0) to its slot (1)
      const bx = b.y < 0 ? p.x : p.x + (ex - p.x) * f, by = b.y < 0 ? p.y + b.y * 140 * S : p.y + (ey - p.y) * f;
      bead(bx, by, ("aeiouy".includes(b.c) ? 10 : 8) * S * depth, beadColor(b.c));
    });
    const r = (s.rest ? 50 : 64) * (narrow ? 1.3 : 1) * S * depth * (s.r || 1) * (1 + s.glow * .18) * Math.min(1, L / (40 * S));
    if (s.glow > .02) { const gl = ctx.createRadialGradient(ex, ey + r * .6, 0, ex, ey + r * .6, r * 2.4); gl.addColorStop(0, `rgba(255,226,170,${.6 * s.glow})`); gl.addColorStop(1, "rgba(255,226,170,0)"); ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(ex, ey + r * .6, r * 2.4, 0, TAU); ctx.fill(); }
    if (r > 1) charm(s.kind, ex, ey, r, s.color || TINT.none);
    ctx.globalAlpha = 1;
    s.tip = { x: ex, y: ey + r * .6, r };
  }
  function drawBead(b, p) {
    ctx.globalAlpha = Math.max(0, b.alpha);
    bead(p.x, p.y + b.dy - 2 * S, ("aeiouy".includes(b.c) ? 10 : 8) * S, beadColor(b.c));
    ctx.globalAlpha = 1;
  }
  function drawPendant() {
    if (pendant.len < 2) return;
    const top = ringY - 40 * S, L = pendant.len + pendant.bob + 40 * S, cy = top + L + 14 * S;
    ctx.strokeStyle = "rgba(205,188,160,.9)"; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(hx, top); ctx.lineTo(hx, top + L); ctx.stroke();
    if (pendant.glow > .02) { const gl = ctx.createRadialGradient(hx, cy, 0, hx, cy, 60 * S); gl.addColorStop(0, `rgba(255,226,170,${.6 * pendant.glow})`); gl.addColorStop(1, "rgba(255,226,170,0)"); ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(hx, cy, 60 * S, 0, TAU); ctx.fill(); }
    ctx.fillStyle = felt("#d6ad80", hx, cy, 16 * S); starPath(hx, cy, 16 * S, .44); ctx.fill();
  }

  // ── motion: springs with weight; nothing bounces like an app ──
  function chime(s) {
    s.vs += .12 + (14 - s.i) * .004; s.vb += 5 * S; s.glow = 1;
    const p = s.tip || { x: hx, y: ringY + s.len, r: 30 };
    for (let k = 0; k < 2; k++) sparks.push({ x: p.x + (Math.random() - .5) * p.r, y: p.y - p.r * .4, vx: (Math.random() - .5) * .6, vy: -.8 - Math.random() * .6, life: 1, c: k % 2 ? "✦" : "♪" });
  }
  function frame(now) {
    const dt = Math.min(.05, (now - last) / 1000); last = now;
    const m = still ? 0 : 1;
    if (!drag) { rot += spin * dt * m; spin += ((playing ? .5 : .1) - spin) * dt * .7; }
    vtilt += (-tilt * 7 - vtilt * 1.6) * dt; tilt += vtilt * dt * (m || 0);
    if (playing) keyA += dt * 5;
    for (const s of strands) {
      if (s.born && now < s.born) continue;
      // the string drops and settles with a little overshoot, like something with weight
      s.v += ((s.lenT - s.len) * 38 - s.v * 7.5) * dt; s.len += s.v * dt;
      s.a += (s.aT - s.a) * Math.min(1, dt * 3.5);
      s.vs += (-s.swing * 9 - s.vs * 1.3) * dt; s.swing += s.vs * dt * 3;
      s.vb += (-s.bob * 40 - s.vb * 5) * dt; s.bob += s.vb * dt;
      s.glow *= Math.pow(.25, dt);
      if (!still) s.swing += Math.sin(now / 1400 + s.a * 3) * .0005;
      for (const b of s.beads) { b.vy += ((1 - b.y) * 55 - b.vy * 8.5) * dt; b.y += b.vy * dt; }
      if (s.dying) s.alpha -= dt * 1.6;
    }
    strands = strands.filter(s => !(s.dying && s.alpha <= 0));
    for (const b of garland) {
      if (b.dying) { b.v += 900 * S * dt; b.dy += b.v * dt; b.alpha -= dt * 2.2; }
      else { b.v += (-b.dy * 70 - b.v * 8) * dt; b.dy += b.v * dt; }
    }
    garland = garland.filter(b => !(b.dying && b.alpha <= 0));
    pendant.v += ((pendant.lenT - pendant.len) * 30 - pendant.v * 7) * dt; pendant.len += pendant.v * dt;
    pendant.vb += (-pendant.bob * 40 - pendant.vb * 5) * dt; pendant.bob += pendant.vb * dt; pendant.glow *= Math.pow(.25, dt);
    if (playing) {
      const el = (now - playing.t0) / 1000 / MB.STEP;
      for (const e of mel.ev) if (!playing.done.has(e) && e.t <= el) {
        playing.done.add(e);
        if (e.kind === "main") { const s = strands.find(x => !x.dying && x.syl === e.syl); if (s) chime(s); noteFns.forEach(f => f(e)); }
        if (e.kind === "home") { pendant.glow = 1; pendant.vb += 5 * S; noteFns.forEach(f => f(e)); }
      }
      if (el > mel.steps + 1) { playing = null; doneFns.forEach(f => f(name)); }
    }
    draw();
    raf = visible ? requestAnimationFrame(frame) : 0;
  }
  function play() {
    if (!mel || !name) return 0;
    MB.ensure(); spin = .9;
    const d = MB.play(mel);
    playing = { t0: performance.now() + 60, done: new Set() };
    return d;
  }

  // drag sideways to spin it; a tap plays it; brushing past a charm sways it
  cv.addEventListener("pointerdown", e => { MB.ensure(); drag = { x: e.clientX, t: performance.now(), moved: 0, v: 0 }; cv.setPointerCapture(e.pointerId); });
  cv.addEventListener("pointermove", e => {
    if (!drag) {
      const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
      const s = strands.find(s => s.tip && !s.dying && Math.hypot(s.tip.x - x, s.tip.y - y) < s.tip.r);
      if (s && s !== hover) s.vs += (e.movementX || 1) * .006 + .05;
      hover = s || null;
      return;
    }
    const now = performance.now(), d = (e.clientX - drag.x) / (rx || 1);
    rot += d; drag.v = d / Math.max(.008, (now - drag.t) / 1000); drag.t = now; drag.x = e.clientX; drag.moved += Math.abs(d);
    for (const s of strands) s.vs -= d * .35;
  });
  const release = () => { if (!drag) return; if (drag.moved < .02) play(); else spin = Math.max(-4, Math.min(4, drag.v)); drag = null; };
  cv.addEventListener("pointerup", release); cv.addEventListener("pointercancel", release);

  addEventListener("resize", size);
  new IntersectionObserver(([en]) => { visible = en.isIntersecting; if (visible && !raf) { last = performance.now(); raf = requestAnimationFrame(frame); } }).observe(cv);
  size(); load("");
  raf = requestAnimationFrame(frame);
  return {
    set: n => load(n), play, resize: size,
    onNote: f => noteFns.push(f), onDone: f => doneFns.push(f),
    get name() { return name; }, get playing() { return !!playing; }, get melody() { return mel; },
  };
})();
