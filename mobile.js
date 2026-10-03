// ─────────────────────────────────────────────────────────────
// THE MOBILE: the first screen. A wooden crib mobile with a little music box.
// Every note of a name is a felt charm on a string: low notes hang long, high notes hang short,
// so the name's melody is the shape of the mobile. It turns slowly; play it and each charm
// bobs and chimes in order. Drag sideways to spin it, tap to play.
// ─────────────────────────────────────────────────────────────
const Mobile = (() => {
  const cv = document.getElementById("mobile");
  if (!cv) return null;
  const ctx = cv.getContext("2d");
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const TAU = Math.PI * 2;
  const DEMO = ["Amara", "Theo", "Inaya", "Leo", "Mira", "Kabir", "Elodie", "Zayn", "Aurelia", "Rumi", "Noor", "Ezra", "Isla", "Arjun"];
  // felt and crochet colors: muted rainbow, from low notes (earthy) to high (airy)
  const FELT = ["#9c8576", "#c8644f", "#d9a441", "#e3a9a0", "#9bb08f", "#7fa6b8", "#9c86b5", "#f3ead9"];
  const WOOD = ["#e2c29d", "#d1a87c", "#b98c5e"];
  let W = 0, H = 0, dpr = 1, S = 1, hx = 0, hookY = 0, ringY = 0, rx = 0, ry = 0;
  let name = "", mel = null, strands = [], rot = 0, spin = .12, drag = null, user = false, born = 0, demoI = 0;
  let playing = null, last = performance.now(), visible = true, raf = 0, idleNext = 0;
  const listeners = [], sparks = [];

  function size() {
    const r = cv.getBoundingClientRect();
    dpr = Math.min(devicePixelRatio || 1, 2); W = r.width; H = r.height;
    cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    S = Math.min(W / 1100, H / 760, 1.25); S = Math.max(S, .55);
    hx = W < 720 ? W * .54 : W * .6; hookY = H * .1; ringY = hookY + 170 * S; rx = 235 * S; ry = 42 * S;
    cv.parentElement.style.setProperty("--drum-bottom", (H - 185) + "px");
  }

  // a name → its strands: one charm per note, the string length set by its pitch
  function load(n) {
    name = n; mel = MB.melody(n || " ");
    const notes = mel.ev.map((e, k) => ({ ...e, k })).filter(e => e.kind === "main" || e.kind === "home");
    const N = Math.max(7, Math.min(10, notes.length));
    strands = Array.from({ length: N }, (_, j) => {
      const e = notes[j];
      const i = e ? e.i : 3 + (j * 5) % 7;                                   // pitch, or a quiet filler strand
      return {
        a: j / N * TAU, len: (e ? 70 : 40) + (14 - i) * 13, i, k: e ? e.k : -1, note: !!e, home: e && e.kind === "home",
        kind: e && e.kind === "home" ? "star" : e ? ["cloud", "moon", "cloud", "star", "cloud", "moon"][j % 6] : "pom",
        color: e ? ["#f4ebdc", "#a89484", "#e2c3b5", "#cdbfa9", "#b9c6ae"][j % 5] : FELT[(j * 3) % 7 + 1], beads: e ? 2 + (i % 2) : 3,
        swing: 0, vs: 0, bob: 0, vb: 0, glow: 0,
      };
    });
    born = performance.now();
    listeners.forEach(f => f(name, mel));
  }
  const nextDemo = () => load(DEMO[demoI++ % DEMO.length]);

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
  function felt(color, x, y, r) {
    const g = ctx.createRadialGradient(x - r * .3, y - r * .35, r * .1, x, y, r * 1.1);
    g.addColorStop(0, shade(color, 18)); g.addColorStop(1, shade(color, -14));
    return g;
  }
  function shade(hex, p) {
    const n = parseInt(hex.slice(1), 16), f = v => Math.max(0, Math.min(255, v + p * 2.55 | 0));
    return `rgb(${f(n >> 16)},${f(n >> 8 & 255)},${f(n & 255)})`;
  }
  function cloud(x, y, r, color) {
    ctx.fillStyle = felt(color, x, y, r);
    ctx.beginPath();
    for (const [dx, dy, rr] of [[-.55, .12, .45], [-.15, -.2, .55], [.32, -.1, .5], [.62, .18, .38], [0, .22, .5]]) ctx.moveTo(x + dx * r + rr * r, y + dy * r), ctx.arc(x + dx * r, y + dy * r, rr * r, 0, TAU);
    ctx.fill();
    ctx.strokeStyle = "rgba(90,70,55,.28)"; ctx.setLineDash([2, 3]); ctx.lineWidth = 1;   // a little embroidery
    ctx.beginPath(); ctx.moveTo(x - r * .45, y + r * .15); ctx.quadraticCurveTo(x, y - r * .15, x + r * .45, y + r * .12); ctx.stroke(); ctx.setLineDash([]);
  }
  function moon(x, y, r, color) {
    ctx.fillStyle = felt(color, x, y, r);
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.arc(x - r * .42, y - r * .22, r * .8, 0, TAU, true); ctx.fill("evenodd");
    ctx.save(); ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.arc(x - r * .42, y - r * .22, r * .8, 0, TAU, true); ctx.clip("evenodd");
    ctx.strokeStyle = "rgba(110,85,65,.35)"; ctx.lineWidth = 1.3;            // stitched stripes
    for (let k = -2; k <= 3; k++) { ctx.beginPath(); ctx.moveTo(x + k * r * .25, y - r); ctx.quadraticCurveTo(x + k * r * .25 + r * .25, y, x + k * r * .25, y + r); ctx.stroke(); }
    ctx.restore();
  }
  function star(x, y, r, color, wood) {
    ctx.fillStyle = wood ? felt("#d6ad80", x, y, r) : felt(color, x, y, r);
    ctx.beginPath();
    for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + k * Math.PI / 5, rr = k % 2 ? r * .45 : r; ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); }
    ctx.closePath(); ctx.fill();
  }
  function pom(x, y, r, color) {
    ctx.fillStyle = felt(color, x, y, r); ctx.beginPath(); ctx.arc(x, y, r * .9, 0, TAU); ctx.fill();
    ctx.strokeStyle = shade(color, 22); ctx.lineWidth = 1.2;            // fluffy edge
    for (let k = 0; k < 40; k++) { const a = k / 40 * TAU, j = (k * 37 % 7) / 7; ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * r * .7, y + Math.sin(a) * r * .7); ctx.lineTo(x + Math.cos(a) * r * (1.02 + j * .12), y + Math.sin(a) * r * (1.02 + j * .12)); ctx.stroke(); }
  }
  function bead(x, y, r, color) {
    ctx.fillStyle = felt(color, x, y, r); ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    ctx.fillStyle = "rgba(255,255,255,.22)";                              // crochet stitches
    for (let k = 0; k < 6; k++) { ctx.beginPath(); ctx.arc(x + Math.cos(k) * r * .5, y + Math.sin(k * 1.7) * r * .45, r * .12, 0, TAU); ctx.fill(); }
  }

  function draw(now) {
    const t = now / 1000;
    ctx.clearRect(0, 0, W, H);
    // soft shadow of the mobile on the wall
    let g = ctx.createRadialGradient(hx + 30 * S, ringY + 220 * S, 10, hx + 30 * S, ringY + 220 * S, rx * 1.6);
    g.addColorStop(0, "rgba(120,90,60,.10)"); g.addColorStop(1, "rgba(120,90,60,0)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);

    // the arm: a pole from the cot, a ball joint, and a long beech arm up to the hook
    const jx = hx - 330 * S, jy = ringY + 120 * S, tx = hx + 26 * S, ty = hookY - 34 * S;
    woodStroke(jx, H + 40, jx, jy, 22 * S); woodStroke(jx, jy, tx, ty, 15 * S); ball(jx, jy, 26 * S); ball(tx, ty, 17 * S);
    // hook and the wooden music box
    ctx.strokeStyle = "#8d8f93"; ctx.lineWidth = 1.6 * S; ctx.beginPath(); ctx.moveTo(hx, ty + 8 * S); ctx.quadraticCurveTo(hx + 8 * S, hookY, hx, hookY + 10 * S); ctx.stroke();
    const py = hookY + 54 * S, prx = 38 * S, pry = 46 * S;
    g = ctx.createLinearGradient(hx - prx, py, hx + prx, py); g.addColorStop(0, WOOD[2]); g.addColorStop(.35, "#ecd2b0"); g.addColorStop(1, WOOD[1]);
    ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(hx, py, prx, pry, 0, 0, TAU); ctx.fill();
    ctx.strokeStyle = "rgba(140,100,60,.25)"; ctx.lineWidth = 1;
    for (let k = -3; k <= 3; k++) { ctx.beginPath(); ctx.ellipse(hx + k * 2, py, prx * (.25 + Math.abs(k) * .2), pry * .92, 0, -1.2, 1.2); ctx.stroke(); }
    ctx.font = `italic ${Math.round(12 * S)}px "Instrument Serif", Georgia, serif`; ctx.textAlign = "center"; ctx.fillStyle = "rgba(110,75,40,.55)";
    ctx.fillText("♪", hx, py + 4 * S);
    // strings from the music box to the ring
    const knotY = py + pry + 26 * S;
    ctx.strokeStyle = "#e9dcc6"; ctx.lineWidth = 2 * S; ctx.beginPath(); ctx.moveTo(hx, py + pry); ctx.lineTo(hx, knotY); ctx.stroke();
    const pts = strands.map(s => { const a = s.a + rot; return { s, x: hx + Math.cos(a) * rx, y: ringY + Math.sin(a) * ry, d: Math.sin(a) }; });
    ctx.strokeStyle = "rgba(225,210,185,.9)"; ctx.lineWidth = 1.2;
    for (const p of pts) { ctx.beginPath(); ctx.moveTo(hx, knotY); ctx.lineTo(p.x, p.y); ctx.stroke(); }

    // ring (back half), strands back to front, ring (front half)
    const ring = (a0, a1) => {                                                 // a beech hoop: a band with a lit top edge
      ctx.strokeStyle = WOOD[2]; ctx.lineWidth = 14 * S; ctx.beginPath(); ctx.ellipse(hx, ringY + 3 * S, rx, ry, 0, a0, a1); ctx.stroke();
      ctx.strokeStyle = WOOD[1]; ctx.lineWidth = 11 * S; ctx.beginPath(); ctx.ellipse(hx, ringY, rx, ry, 0, a0, a1); ctx.stroke();
      ctx.strokeStyle = "rgba(255,240,215,.75)"; ctx.lineWidth = 2.5 * S; ctx.beginPath(); ctx.ellipse(hx, ringY - 4 * S, rx, ry, 0, a0, a1); ctx.stroke(); };
    ring(Math.PI, TAU);
    const order = [...pts].sort((a, b) => a.d - b.d);
    for (const p of order) {
      const s = p.s, depth = .82 + .18 * (p.d + 1) / 2;
      const pop = Math.min(1, Math.max(0, (now - born - strands.indexOf(s) * 70) / 420));
      const L = s.len * S * (.6 + .4 * pop) + s.bob;
      const ex = p.x + Math.sin(s.swing) * L, ey = p.y + Math.cos(s.swing) * L;
      ctx.globalAlpha = .55 + .45 * depth;
      ctx.strokeStyle = "rgba(205,188,160,.95)"; ctx.lineWidth = 1.1; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(ex, ey); ctx.stroke();
      for (let b = 0; b < s.beads; b++) {                                      // crochet and wooden beads threaded on the string
        const f = .28 + b * .2, bx = p.x + (ex - p.x) * f, by = p.y + (ey - p.y) * f;
        bead(bx, by, (b % 2 ? 7 : 10) * S * depth, b % 2 ? "#d9bf9a" : FELT[(s.i + b * 3 + 1) % 7 + 1]);
      }
      const r = (s.note ? 48 : 22) * S * depth * (1 + s.glow * .2) * pop;
      if (s.glow > .02) { const gl = ctx.createRadialGradient(ex, ey, 0, ex, ey, r * 2.2); gl.addColorStop(0, `rgba(255,236,190,${.55 * s.glow})`); gl.addColorStop(1, "rgba(255,236,190,0)"); ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(ex, ey, r * 2.2, 0, TAU); ctx.fill(); }
      if (r > .5) {
        if (s.kind === "cloud") cloud(ex, ey + r * .3, r, s.color);
        else if (s.kind === "moon") moon(ex, ey + r * .5, r * .9, s.color);
        else if (s.kind === "star") star(ex, ey + r * .6, r * .8, s.color, s.home);
        else pom(ex, ey + r * .55, r * .6, s.color === "#efe4d3" ? "#f6f0e6" : s.color);
      }
      ctx.globalAlpha = 1;
    }
    ring(0, Math.PI);
    // sparkles when a charm chimes
    for (let k = sparks.length - 1; k >= 0; k--) {
      const q = sparks[k]; q.life -= .016; if (q.life <= 0) { sparks.splice(k, 1); continue; }
      q.x += q.vx; q.y += q.vy; q.vy += .02;
      ctx.fillStyle = `rgba(217,164,65,${q.life})`; ctx.font = `${Math.round(12 * S)}px serif`; ctx.fillText(q.c, q.x, q.y);
    }
  }

  // ── motion ──
  function chime(s, e, audible) {
    s.vs += .1 + (14 - s.i) * .004; s.vb += 6 * S; s.glow = 1;
    if (audible) MB.pluck(e.i, e.v);
    const p = { x: hx + Math.cos(s.a + rot) * rx, y: ringY + Math.sin(s.a + rot) * ry + s.len * S };
    for (let k = 0; k < 3; k++) sparks.push({ x: p.x + (Math.random() - .5) * 30, y: p.y, vx: (Math.random() - .5) * .8, vy: -1 - Math.random(), life: 1, c: k % 2 ? "✦" : "♪" });
  }
  function frame(now) {
    const dt = Math.min(.05, (now - last) / 1000); last = now;
    if (!drag) { rot += spin * dt * (still ? 0 : 1); spin += (.12 - spin) * dt * .6; }
    for (const s of strands) {                                                // gentle pendulums
      s.vs += (-s.swing * 9 - s.vs * 1.4) * dt; s.swing += s.vs * dt * 3;
      s.vb += (-s.bob * 40 - s.vb * 5) * dt; s.bob += s.vb * dt;
      s.glow *= Math.pow(.2, dt);
      if (!still) s.swing += Math.sin(now / 1300 + s.a * 3) * .0006;
    }
    if (playing) {
      const el = (now - playing.t0) / 1000 / MB.STEP;
      for (const e of mel.ev) if (!playing.done.has(e) && e.t <= el) {
        playing.done.add(e);
        const s = strands.find(x => x.k === mel.ev.indexOf(e)) || strands.find(x => x.i === e.i);
        if (s && (e.kind === "main" || e.kind === "home")) chime(s, e, false);
      }
      if (el > mel.steps + 1) { playing = null; listeners.forEach(f => f(name, mel, "done")); idleNext = now + 5000; }
    } else if (!user && !still && now > idleNext && idleNext) { nextDemo(); idleNext = now + 6000; }
    draw(now);
    raf = visible ? requestAnimationFrame(frame) : 0;
  }
  function play() {
    if (!mel) return;
    MB.ensure(); spin = .9;
    MB.play(mel);
    playing = { t0: performance.now() + 60, done: new Set() };
  }
  function set(n) { user = !!n; if (n) load(n); else { nextDemo(); idleNext = performance.now() + 6000; } }

  // drag sideways to spin it; a tap plays it
  cv.addEventListener("pointerdown", e => { MB.ensure(); drag = { x: e.clientX, t: performance.now(), moved: 0, v: 0 }; cv.setPointerCapture(e.pointerId); });
  cv.addEventListener("pointermove", e => {
    if (!drag) return;
    const now = performance.now(), d = (e.clientX - drag.x) / (rx || 1);
    rot += d; drag.v = d / Math.max(.008, (now - drag.t) / 1000); drag.t = now; drag.x = e.clientX; drag.moved += Math.abs(d);
    for (const s of strands) s.vs -= d * .4;
  });
  const release = () => { if (!drag) return; if (drag.moved < .02) play(); else spin = Math.max(-4, Math.min(4, drag.v)); drag = null; };
  cv.addEventListener("pointerup", release); cv.addEventListener("pointercancel", release);

  addEventListener("resize", size);
  new IntersectionObserver(([en]) => { visible = en.isIntersecting; if (visible && !raf) { last = performance.now(); raf = requestAnimationFrame(frame); } }).observe(cv);
  size(); nextDemo(); idleNext = performance.now() + 6000;
  document.fonts && document.fonts.ready.then(() => draw(performance.now()));
  raf = requestAnimationFrame(frame);
  return { set, play, onName: f => listeners.push(f), get name() { return name; }, get user() { return user; }, get playing() { return !!playing; } };
})();
const Drum = Mobile;  // the page talks to the hero as "Drum"
