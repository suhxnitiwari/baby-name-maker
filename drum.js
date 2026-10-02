// ─────────────────────────────────────────────────────────────
// THE DRUM: the first screen. A brass music-box cylinder in lamplight.
// Its pins are a name's notes; as it turns they pluck a steel comb.
// Grab the drum and spin it, or press play. Names engraved on the brass.
// ─────────────────────────────────────────────────────────────
const Drum = (() => {
  const cv = document.getElementById("drum");
  if (!cv) return null;
  const ctx = cv.getContext("2d");
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const TAU = Math.PI * 2, STRIKE = -1.22; // pins meet the comb a little above the front of the drum
  const DEMO = ["Amara", "Theo", "Inaya", "Leo", "Mira", "Kabir", "Elodie", "Zayn", "Aurelia", "Rumi", "Noor", "Ezra", "Isla", "Arjun"];
  let W = 0, H = 0, dpr = 1, L = 0, R = 0, x0 = 0, cy = 0;
  let mel = null, name = "", REV = 16, phase = -3, mode = "idle", vel = 0, drag = null, user = false, born = 0;
  let demoI = 0, last = performance.now(), visible = true, raf = 0, restAt = 0;
  const teeth = Array.from({ length: 15 }, () => ({ amp: 0, glow: 0 }));
  let sparks = [], glyphs = [];
  const dust = Array.from({ length: 46 }, () => ({ x: Math.random(), y: Math.random(), s: .4 + Math.random() * 1.4, v: .004 + Math.random() * .01, p: Math.random() * TAU }));
  const bokeh = Array.from({ length: 9 }, (_, k) => ({ x: Math.random(), y: .15 + Math.random() * .7, r: 30 + Math.random() * 90, p: Math.random() * TAU, h: k % 3 }));
  // the drum is drilled for other tunes too: tiny dimples that turn with it
  const dimples = Array.from({ length: 220 }, (_, k) => ({ i: k % 15, t: ((k * 7.31) % 1) * 64 + (k % 3) * .33 }));
  const listeners = [];
  // an invisible handle over the drum: it captures drags (so the page still scrolls everywhere else)
  const grip = document.createElement("div");
  grip.className = "grip"; grip.setAttribute("aria-hidden", "true");
  cv.parentElement.appendChild(grip);

  function size() {
    const r = cv.getBoundingClientRect();
    dpr = Math.min(devicePixelRatio || 1, 2); W = r.width; H = r.height;
    cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const narrow = W < 720;
    R = Math.max(46, Math.min(H * .115, 104, W * .19));
    L = Math.min(W * (narrow ? .9 : .64), 980) - (narrow ? R * .9 : 0);
    x0 = (W - L - (narrow ? R * .9 : 0)) / 2;
    cy = H * (narrow ? .56 : .565);
    cv.parentElement.style.setProperty("--drum-bottom", cy + R + R * .62 + 34 + "px");
    Object.assign(grip.style, { left: x0 - 30 + "px", top: cy - R * 1.7 + "px", width: L + R + 60 + "px", height: R * 2.9 + "px" });
  }

  function load(n) {
    name = n;
    mel = MB.melody(n || " ");
    REV = Math.max(16, Math.ceil(mel.steps + 5));
    phase = -2.6; born = performance.now();
    listeners.forEach(f => f(name, mel));
  }
  const nextDemo = () => load(DEMO[demoI++ % DEMO.length]);

  // ── pluck: sound, a shimmering tooth, a spark and a rising note ──
  function strike(e, audible) {
    const t = teeth[e.i];
    t.amp = Math.min(5, t.amp + 3.2 * e.v + 1); t.glow = 1;
    if (audible) MB.pluck(e.i, e.v);
    const x = x0 + (e.i + .5) * L / 15, y = cy + R * Math.sin(STRIKE);
    for (let k = 0; k < (e.kind === "main" || e.kind === "home" ? 7 : 3); k++) {
      const a = -Math.PI / 2 + (Math.random() - .5) * 2.2, s = .6 + Math.random() * 1.8;
      sparks.push({ x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, life: 1, r: .6 + Math.random() * 1.4 });
    }
    if (e.kind === "main" || e.kind === "home") glyphs.push({ x: x + (Math.random() - .5) * 10, y: y - 24, life: 1, g: Math.random() < .5 ? "♪" : "♫", d: (Math.random() - .5) * .5 });
  }
  function advance(d, audible) {
    if (!mel || !d) return;
    const p0 = phase; phase += d;
    if (d > 0) for (const e of mel.ev) if (e.t > p0 && e.t <= phase) strike(e, audible);
    // a ratchet tick each step while you turn it by hand
    if ((mode === "drag" || mode === "coast") && Math.floor(p0) !== Math.floor(phase) && d > 0) MB.tick(.22);
  }

  // ── drawing ──
  function brass(y0, y1, k = 1) {
    const g = ctx.createLinearGradient(0, y0, 0, y1);
    g.addColorStop(0, `rgba(48,30,12,${k})`); g.addColorStop(.12, `rgba(120,86,36,${k})`); g.addColorStop(.3, `rgba(246,221,160,${k})`);
    g.addColorStop(.38, `rgba(222,186,112,${k})`); g.addColorStop(.62, `rgba(150,108,44,${k})`); g.addColorStop(.86, `rgba(70,46,18,${k})`); g.addColorStop(1, `rgba(28,17,8,${k})`);
    return g;
  }
  function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x, y, w, h, r) : ctx.rect(x, y, w, h); }

  function draw(now) {
    const t = now / 1000;
    ctx.clearRect(0, 0, W, H);
    // lamplight
    const breathe = still ? 1 : .92 + .08 * Math.sin(t * .7);
    let g = ctx.createRadialGradient(W / 2, cy - R * .4, 10, W / 2, cy, Math.max(W, H) * .72);
    g.addColorStop(0, `rgba(196,128,62,${.42 * breathe})`); g.addColorStop(.3, `rgba(120,58,44,${.26 * breathe})`); g.addColorStop(.7, "rgba(40,16,24,.0)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // soft out-of-focus lights, like a nursery lamp behind glass
    for (const b of bokeh) {
      const bx = (b.x + (still ? 0 : Math.sin(t * .05 + b.p) * .02)) * W, by = (b.y + (still ? 0 : Math.cos(t * .04 + b.p) * .02)) * H;
      const a = .035 + .02 * Math.sin(t * .3 + b.p), col = ["255,196,120", "255,150,140", "255,214,160"][b.h];
      const bg = ctx.createRadialGradient(bx, by, b.r * .55, bx, by, b.r);
      bg.addColorStop(0, `rgba(${col},${a})`); bg.addColorStop(.85, `rgba(${col},${a * .8})`); bg.addColorStop(1, `rgba(${col},0)`);
      ctx.fillStyle = bg; ctx.beginPath(); ctx.arc(bx, by, b.r, 0, TAU); ctx.fill();
    }
    // dust in the light
    for (const p of dust) {
      if (!still) { p.y -= p.v * .016; p.x += Math.sin(t * .4 + p.p) * .0002; if (p.y < -.02) { p.y = 1.02; p.x = Math.random(); } }
      const px = p.x * W, py = p.y * H, d = Math.hypot(px - W / 2, (py - cy) * 1.4) / (W * .5);
      const a = Math.max(0, .5 - d * .5) * (.6 + .4 * Math.sin(t * 1.3 + p.p));
      if (a <= 0) continue;
      ctx.fillStyle = `rgba(255,222,160,${a})`; ctx.beginPath(); ctx.arc(px, py, p.s, 0, TAU); ctx.fill();
    }

    const span = L / 15, sy = cy + R * Math.sin(STRIKE);
    // a walnut box with a velvet bed and a brass inlay
    const bx = x0 - R * .75, bw = L + R * 1.5 + 44, by = cy + R * .5, bh = R * .62 + 40;
    g = ctx.createLinearGradient(0, by, 0, by + bh); g.addColorStop(0, "#5e2131"); g.addColorStop(.35, "#3a1019"); g.addColorStop(1, "#1a060c");
    rrect(bx, by, bw, bh * .45, 10); ctx.fillStyle = g; ctx.fill();
    const wy = by + bh * .38;
    g = ctx.createLinearGradient(0, wy, 0, by + bh); g.addColorStop(0, "#6a3d26"); g.addColorStop(.5, "#4a2818"); g.addColorStop(1, "#22110a");
    rrect(bx - 8, wy, bw + 16, bh * .62, 8); ctx.fillStyle = g; ctx.fill();
    ctx.save(); ctx.beginPath(); ctx.rect(bx - 8, wy, bw + 16, bh * .62); ctx.clip();
    for (let k = 0; k < 14; k++) {   // wood grain
      ctx.strokeStyle = `rgba(${k % 2 ? "20,8,4" : "150,96,60"},${.1 + (k % 3) * .04})`; ctx.lineWidth = .8 + (k % 3) * .4;
      ctx.beginPath(); const gy = wy + 3 + k * (bh * .62 / 14);
      for (let x = bx - 8; x <= bx + bw + 8; x += 24) ctx.lineTo(x, gy + Math.sin(x / (60 + k * 7) + k) * 2.2);
      ctx.stroke();
    }
    ctx.restore();
    rrect(bx - 8, wy, bw + 16, 2.5, 1); ctx.fillStyle = brass(wy - 1, wy + 3); ctx.fill();
    ctx.font = `italic ${Math.round(R * .2)}px "Instrument Serif", Georgia, serif`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillStyle = "rgba(255,220,160,.32)"; ctx.fillText("Lullabyte · No. 15 in C", W / 2, wy + bh * .34);
    // soft shadow under the drum
    g = ctx.createRadialGradient(W / 2, cy + R * .95, 4, W / 2, cy + R * .95, L * .55);
    g.addColorStop(0, "rgba(0,0,0,.55)"); g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.save(); ctx.scale(1, .16); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(W / 2, (cy + R * .95) / .16, L * .55, 0, TAU); ctx.fill(); ctx.restore();

    // comb plate (behind the teeth, above the drum)
    const py0 = cy - R - R * .5, ph = R * .14;
    rrect(x0 - 18, py0, L + 36, ph, 4); ctx.fillStyle = brass(py0, py0 + ph); ctx.fill();
    for (const sx of [x0 - 6, x0 + L * .33, x0 + L * .66, x0 + L + 6]) {
      ctx.fillStyle = "#3a2810"; ctx.beginPath(); ctx.arc(sx, py0 + ph / 2, 3.2, 0, TAU); ctx.fill();
      ctx.strokeStyle = "rgba(255,236,190,.5)"; ctx.lineWidth = .8; ctx.beginPath(); ctx.moveTo(sx - 2, py0 + ph / 2 - 1); ctx.lineTo(sx + 2, py0 + ph / 2 + 1); ctx.stroke();
    }

    // the cylinder
    g = brass(cy - R, cy + R); rrect(x0, cy - R, L, R * 2, 3); ctx.fillStyle = g; ctx.fill();
    // turned-brass rings at each tooth, and fine lathe lines
    ctx.lineWidth = 1;
    for (let i = 0; i <= 15; i++) { ctx.strokeStyle = "rgba(40,24,8,.13)"; ctx.beginPath(); ctx.moveTo(x0 + i * span, cy - R + 2); ctx.lineTo(x0 + i * span, cy + R - 2); ctx.stroke(); }
    for (let k = 0; k < 9; k++) { const yy = cy - R + (k + .5) * (2 * R / 9); ctx.strokeStyle = `rgba(255,240,200,${.025 + .02 * (k % 2)})`; ctx.beginPath(); ctx.moveTo(x0 + 2, yy); ctx.lineTo(x0 + L - 2, yy); ctx.stroke(); }
    const ang = e => { let a = STRIKE + (e.t - phase) * TAU / REV; a = ((a + Math.PI) % TAU + TAU) % TAU - Math.PI; return a; };
    // the name, engraved on the brass, turning with the drum
    if (mel && name) {
      const a = ang({ t: -1.2 });
      if (Math.cos(a) > .12) {
        const c = Math.cos(a);
        ctx.save(); ctx.translate(W / 2, cy + R * Math.sin(a)); ctx.scale(1, c);
        ctx.font = `italic ${Math.round(R * .42)}px "Instrument Serif", Georgia, serif`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillStyle = `rgba(255,240,205,${.35 * c})`; ctx.fillText(name, 0, 1.2);
        ctx.fillStyle = `rgba(62,38,12,${.62 * c})`; ctx.fillText(name, 0, 0);
        ctx.restore();
      }
    }
    // dimples where other tunes' pins would sit
    for (const d of dimples) {
      const a = ang({ t: d.t % REV }), c = Math.cos(a);
      if (c < .15) continue;
      const x = x0 + (d.i + .5) * span, y = cy + R * Math.sin(a);
      ctx.fillStyle = `rgba(58,36,12,${.32 * c})`; ctx.beginPath(); ctx.ellipse(x, y, 1.5, 1.5 * c, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = `rgba(255,240,200,${.18 * c})`; ctx.beginPath(); ctx.ellipse(x + .5, y + 1, 1, .8 * c, 0, 0, TAU); ctx.fill();
    }
    // pins
    if (mel) mel.ev.forEach((e, k) => {
      const a = ang(e), c = Math.cos(a);
      if (c < .02) return;
      const pop = Math.min(1, Math.max(0, (now - born - k * 45) / 380));
      if (!pop) return;
      const x = x0 + (e.i + .5) * span, y = cy + R * Math.sin(a);
      const big = e.kind === "main" || e.kind === "home", r = (big ? 6 : 3.6) * (.55 + .45 * c) * (pop < 1 ? 1 + Math.sin(pop * Math.PI) * .8 : 1);
      const hot = Math.max(0, 1 - Math.abs(a - STRIKE) * 3.2);
      const hr = r * (3.6 + hot * 5);
      const halo = ctx.createRadialGradient(x, y, 0, x, y, hr);
      halo.addColorStop(0, `rgba(255,226,150,${Math.min(1, .4 * c + hot * .7)})`); halo.addColorStop(1, "rgba(255,226,150,0)");
      ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(x, y, hr, 0, TAU); ctx.fill();
      ctx.fillStyle = `rgba(40,24,8,${.45 * c})`; ctx.beginPath(); ctx.ellipse(x + 1, y + r * .55, r, r * .6, 0, 0, TAU); ctx.fill();   // shadow: it stands up off the brass
      const pg = ctx.createRadialGradient(x - r * .35, y - r * .4, 0, x, y, r);
      pg.addColorStop(0, "#fffdf4"); pg.addColorStop(.5, e.kind === "home" ? "#ffd68c" : "#f4e2b4"); pg.addColorStop(1, "#a07a3a");
      ctx.fillStyle = pg; ctx.globalAlpha = Math.min(1, .55 + .45 * c + hot); ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill(); ctx.globalAlpha = 1;
    });
    // end caps
    for (const ex of [x0, x0 + L]) {
      g = ctx.createLinearGradient(0, cy - R, 0, cy + R); g.addColorStop(0, "#5a4018"); g.addColorStop(.3, "#d9b46a"); g.addColorStop(.6, "#8a6428"); g.addColorStop(1, "#24160a");
      ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(ex, cy, R * .14, R * 1.01, 0, 0, TAU); ctx.fill();
      ctx.strokeStyle = "rgba(255,236,190,.35)"; ctx.lineWidth = 1; ctx.beginPath(); ctx.ellipse(ex, cy, R * .14, R, 0, -Math.PI / 2, Math.PI / 2); ctx.stroke();
    }
    // the crank, turning with the drum
    const hx = x0 + L + R * .6, crank = phase * TAU / REV * 2, arm = R * .95;
    ctx.strokeStyle = brass(cy - 4, cy + 4); ctx.lineWidth = 7; ctx.lineCap = "round"; ctx.beginPath(); ctx.moveTo(x0 + L, cy); ctx.lineTo(hx, cy); ctx.stroke();
    const kx = hx + Math.sin(crank) * 10, ky = cy - Math.cos(crank) * arm;
    ctx.strokeStyle = "#c9a35a"; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(hx, cy); ctx.lineTo(kx, ky); ctx.stroke();
    ctx.fillStyle = "#e6c37e"; ctx.beginPath(); ctx.arc(hx, cy, 7, 0, TAU); ctx.fill();
    g = ctx.createRadialGradient(kx - 4, ky - 4, 1, kx, ky, 15); g.addColorStop(0, "#7a3b46"); g.addColorStop(1, "#2a0d14");
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(kx, ky, 14, 0, TAU); ctx.fill(); ctx.strokeStyle = "#d9b46a"; ctx.lineWidth = 2; ctx.stroke();

    // the comb: fine silver tines reaching down to the drum, long and weighted for low notes, short for high
    const top = py0 + ph - 2;
    for (let i = 0; i < 15; i++) {
      const tt = teeth[i], cx = x0 + (i + .5) * span, w = Math.max(3, Math.min(span * .16, 9)) * (1.25 - i * .03);
      const wob = still ? 0 : tt.amp * Math.sin(t * 70 + i);
      tt.amp *= .9; tt.glow *= .93;
      const lit = tt.glow, y0 = top, y1 = sy + 2;
      g = ctx.createLinearGradient(cx - w / 2, 0, cx + w / 2, 0);
      g.addColorStop(0, `rgba(${120 + lit * 100},${116 + lit * 100},${110 + lit * 90},1)`);
      g.addColorStop(.35, `rgba(255,${250 - lit * 10},${240 - lit * 40},1)`);
      g.addColorStop(1, `rgba(${110 + lit * 110},${104 + lit * 100},${96 + lit * 80},1)`);
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.moveTo(cx - w / 2, y0);
      ctx.lineTo(cx + w / 2, y0);
      ctx.quadraticCurveTo(cx + w * .45 + wob * .5, (y0 + y1) / 2, cx + w * .3 + wob, y1 - 2);
      ctx.quadraticCurveTo(cx + wob, y1 + 1.5, cx - w * .3 + wob, y1 - 2);
      ctx.quadraticCurveTo(cx - w * .45 + wob * .5, (y0 + y1) / 2, cx - w / 2, y0);
      ctx.fill();
      if (i < 3) { ctx.fillStyle = "rgba(200,190,175,.9)"; ctx.beginPath(); ctx.ellipse(cx + wob * .4, y0 + (y1 - y0) * .42, w * .8, w * .55, 0, 0, TAU); ctx.fill(); }
      // a bead of light where tine meets pin
      const gl = ctx.createRadialGradient(cx + wob, y1, 0, cx + wob, y1, 10 + lit * 26);
      gl.addColorStop(0, `rgba(255,232,170,${.12 + .75 * lit})`); gl.addColorStop(1, "rgba(255,232,170,0)");
      ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(cx + wob, y1, 10 + lit * 26, 0, TAU); ctx.fill();
    }
    // sparks and rising notes
    sparks = sparks.filter(s => (s.life -= .022) > 0);
    for (const s of sparks) { s.x += s.vx; s.y += s.vy; s.vy += .03; ctx.fillStyle = `rgba(255,228,160,${s.life})`; ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, TAU); ctx.fill(); }
    glyphs = glyphs.filter(q => (q.life -= .009) > 0);
    ctx.font = `${Math.round(R * .3)}px "Instrument Serif", Georgia, serif`; ctx.textAlign = "center";
    for (const q of glyphs) { q.y -= .7; q.x += q.d + Math.sin(q.life * 9) * .3; ctx.fillStyle = `rgba(255,222,150,${q.life * .85})`; ctx.fillText(q.g, q.x, q.y); }
  }

  // ── the loop ──
  const IDLE = 2.2, PLAY = 1 / MB.STEP;
  function frame(now) {
    const dt = Math.min(.05, (now - last) / 1000); last = now;
    if (mel) {
      if (mode === "idle" && !still) advance(dt * IDLE, false);
      else if (mode === "play") advance(dt * PLAY, true);
      else if (mode === "seek") { phase = Math.min(seekTo, phase + dt * 46); if (phase >= seekTo - 1e-6) { phase -= seekShift; mode = "play"; } }
      else if (mode === "coast") { advance(vel * dt, true); vel *= Math.pow(.955, dt * 60); if (Math.abs(vel) < .25) { mode = "rest"; restAt = now; } }
      const end = mel.steps + 2.5;
      if (phase > end) {
        if (mode === "play") { mode = "rest"; restAt = now; listeners.forEach(f => f(name, mel, "done")); }
        else if (!user) nextDemo(); else phase -= REV;
      }
      if (mode === "rest" && !user && now - restAt > 2500) mode = "idle";
    }
    draw(now);
    raf = visible ? requestAnimationFrame(frame) : 0;
  }

  // ── grab and spin ──
  grip.addEventListener("pointerdown", e => {
    MB.ensure();
    drag = { y: e.clientY, t: performance.now(), moved: 0, v: 0 };
    mode = "drag"; grip.setPointerCapture(e.pointerId); grip.classList.add("grabbing");
  });
  grip.addEventListener("pointermove", e => {
    if (!drag) return;
    const now = performance.now(), d = (drag.y - e.clientY) / (R * TAU / REV) * 1.4;
    advance(d, true);
    drag.v = d / Math.max(.008, (now - drag.t) / 1000); drag.t = now; drag.y = e.clientY; drag.moved += Math.abs(d);
  });
  const release = () => {
    if (!drag) return;
    grip.classList.remove("grabbing");
    if (drag.moved < .15) { drag = null; return play(); }      // a tap plays it
    vel = Math.max(-12, Math.min(14, drag.v)); mode = "coast"; drag = null;
  };
  grip.addEventListener("pointerup", release); grip.addEventListener("pointercancel", release);

  // play: spin the drum forward (silently, fast) until the first pin is just below the comb, then play
  let seekTo = 0, seekShift = 0;
  function play() {
    MB.ensure();
    if (!mel) return;
    const k = Math.ceil((phase + 1.4) / REV - 1e-6);
    seekTo = -1.4 + k * REV; seekShift = k * REV; mode = "seek";
  }
  function set(n) {
    user = !!n;
    if (n) { load(n); mode = "rest"; restAt = performance.now(); }
    else { nextDemo(); mode = "idle"; }
  }

  addEventListener("resize", size);
  new IntersectionObserver(([en]) => { visible = en.isIntersecting; if (visible && !raf) { last = performance.now(); raf = requestAnimationFrame(frame); } }).observe(cv);
  size(); nextDemo();
  document.fonts && document.fonts.ready.then(() => draw(performance.now()));
  raf = requestAnimationFrame(frame);
  return { set, play, get playing() { return mode === "play" || mode === "seek"; }, onName: f => listeners.push(f), get name() { return name; }, get user() { return user; } };
})();
