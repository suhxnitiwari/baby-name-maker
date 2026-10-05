// ─────────────────────────────────────────────────────────────
// THE TOY PIANO: what a name sounds like.
// Fifteen ivory keys in a walnut case, C5 to C7: exactly the music box's comb.
// A small dot sits over every key the name uses; the syllables float over their notes,
// and as the name plays, each key presses down under its syllable. Every key can be played by hand.
// ─────────────────────────────────────────────────────────────
const Piano = (() => {
  const WHITE = ["C", "D", "E", "F", "G", "A", "B"];
  const N = 15;                                                     // white keys: C5 … C7 (comb teeth 0–14)
  const BLACK_AFTER = new Set([0, 1, 3, 4, 5]);                     // a black key after C, D, F, G, A
  const midiOf = i => MB.COMB[i];
  const x = i => (i + .5) / N * 100;                                 // centre of white key i, in %

  // voices: [{ m: melody, words: syllable strings, own: "a" | "b" | "" }]
  function html(voices, o = {}) {
    const used = new Map();
    voices.forEach(v => v.m.ev.forEach(e => { if (e.kind === "main") used.set(e.i, (used.get(e.i) || "") + (v.own || "x")); }));
    let keys = "";
    for (let i = 0; i < N; i++) {
      const nm = MB.NOTE_NAMES[i], u = used.get(i) || "";
      const dot = u ? `<i class="dot${u.includes("a") && u.includes("b") ? " both" : u.includes("a") ? " a" : u.includes("b") ? " b" : ""}"></i>` : "";
      keys += `<button class="key w" data-midi="${midiOf(i)}" data-i="${i}" aria-label="${nm}" tabindex="-1">${dot}<span class="kl">${nm}</span></button>`;
    }
    for (let i = 0; i < N - 1; i++) if (BLACK_AFTER.has(i % 7)) keys += `<button class="key b" data-midi="${midiOf(i) + 1}" style="left:${((i + 1) / N * 100).toFixed(3)}%" aria-label="${WHITE[i % 7]}♯" tabindex="-1"></button>`;
    // the syllables float over their first note; neighbours too close share a second row
    let maxRow = 0;
    const placed = voices.map((v, vi) => {
      const pos = [], rows = [];
      v.words.forEach((w, k) => { const e = v.m.ev.find(e => e.kind === "main" && e.syl === k); if (e) pos.push({ w, k, at: x(e.i), stress: e.stress === 1 }); });
      return pos.map(p => {
        let row = 0; while ((rows[row] || []).some(q => Math.abs(q - p.at) < Math.max(7, p.w.length * 2.2))) row++;
        (rows[row] = rows[row] || []).push(p.at);
        const r = row + (voices.length > 1 ? vi * 2 : 0); maxRow = Math.max(maxRow, r);
        return { ...p, vi, r, own: v.own };
      });
    }).flat();
    // earlier syllables sit higher, so stacked ones read top to bottom
    const lyr = placed.map(p => `<span class="syl${p.own ? " o-" + p.own : ""}${p.stress ? " stress" : ""}" data-v="${p.vi}" data-syl="${p.k}" style="left:${p.at.toFixed(2)}%;--row:${maxRow - p.r}">${esc(p.w)}</span>`).join("");
    return `<div class="piano${o.small ? " small" : ""}" ${o.id ? `id="${o.id}"` : ""}>
      <div class="lyrics" style="height:${26 + (maxRow + 1) * 20}px">${lyr}</div>
      <div class="case"><div class="felt"></div><div class="keys">${keys}</div></div>
    </div>`;
  }
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function press(el, ms = 260, cls = "") {
    if (!el) return;
    el.classList.remove("down", "a", "b"); void el.offsetWidth;
    el.classList.add("down"); if (cls) el.classList.add(cls);
    clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove("down", "a", "b"), ms);
  }
  // play one or more voices on a piano element at once; keys press under their syllables
  const timers = new WeakMap();
  function play(root, voices, o = {}) {
    if (!root) return 0;
    (timers.get(root) || []).forEach(clearTimeout);
    const T = [], keyAt = i => root.querySelector(`.key.w[data-i="${i}"]`);
    let dur = 0;
    voices.forEach((v, vi) => {
      dur = Math.max(dur, MB.play(v.m, o.speed || 1));
      for (const e of v.m.ev) {
        if (e.kind !== "main" && e.kind !== "home") continue;
        T.push(setTimeout(() => {
          press(keyAt(e.i), e.kind === "home" ? 600 : 300, v.own || "");
          root.querySelectorAll(`.syl[data-v="${vi}"]`).forEach(s => s.classList.toggle("on", e.kind === "main" && +s.dataset.syl === e.syl));
          o.onNote && o.onNote(e, vi);
        }, 60 + e.t * MB.STEP * 1000 / (o.speed || 1)));
      }
    });
    root.classList.add("playing");
    T.push(setTimeout(() => { root.classList.remove("playing"); root.querySelectorAll(".syl.on").forEach(s => s.classList.remove("on")); o.onDone && o.onDone(); }, dur * 1000 + 200));
    timers.set(root, T);
    return dur;
  }
  // play by hand
  document.addEventListener("pointerdown", e => {
    const k = e.target.closest(".piano .key");
    if (!k) return;
    e.preventDefault();
    MB.ensure(); MB.tone(+k.dataset.midi, .9); press(k, 220);
  });
  return { html, play, voice: (n, own = "", owners = null) => ({ m: MB.melody(n, "", owners), words: MB.explain(n).map(s => s.text), own }) };
})();
