// ─────────────────────────────────────────────────────────────
// HANGING NAMES: a small wooden mobile of names on strings (the charts and the cradle).
// New names descend on their strings and settle; leaving names are pulled back up.
// Brushing past a name sways it; everything swings on a damped spring, never a bounce.
// ─────────────────────────────────────────────────────────────
const Hang = (() => {
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const live = new Set();
  let raf = 0;
  function tick() {
    raf = 0;
    for (const s of live) {
      s.w += (-s.a * 30 - s.w * 3.2) * .016; s.a += s.w * .016;
      s.el.style.transform = `rotate(${s.a.toFixed(3)}rad)`;
      if (Math.abs(s.a) < .0005 && Math.abs(s.w) < .0005) { s.a = 0; s.w = 0; s.el.style.transform = ""; live.delete(s); }
    }
    if (live.size) raf = requestAnimationFrame(tick);
  }
  function nudge(el, v) {
    if (still) return;
    const s = el._sw || (el._sw = { el, a: 0, w: 0 });
    s.w += v; live.add(s);
    if (!raf) raf = requestAnimationFrame(tick);
  }
  // items: [{ key, html, len (px of string) }]
  function render(root, items, o = {}) {
    if (!root.querySelector(".hang-row")) root.innerHTML = `<div class="dowel"><i></i></div><div class="hang-row"></div>`;
    const row = root.querySelector(".hang-row"), keep = new Set(items.map(i => i.key));
    row.querySelectorAll(".hc").forEach(el => {
      if (keep.has(el.dataset.key) && !el.classList.contains("rise")) return;
      el.classList.add("rise"); el.style.pointerEvents = "none";
      setTimeout(() => el.remove(), 650);
    });
    items.forEach((it, k) => {
      let el = [...row.querySelectorAll(".hc:not(.rise)")].find(e => e.dataset.key === it.key);
      if (!el) {
        el = document.createElement("div");
        el.className = "hc"; el.dataset.key = it.key;
        el.innerHTML = `<div class="sw"><i class="thread"></i><div class="tag">${it.html}</div></div>`;
        el.style.setProperty("--len", "0px");
        row.appendChild(el);
        setTimeout(() => { el.style.setProperty("--len", it.len + "px"); nudge(el.firstChild, (Math.random() - .5) * .6); }, 30 + k * (o.stagger ?? 90));
      } else { el.style.setProperty("--len", it.len + "px"); el.querySelector(".tag").innerHTML = it.html; }
      el.style.order = k;
    });
  }
  document.addEventListener("pointerover", e => {
    const t = e.target.closest(".hc .sw");
    if (t && !t.contains(e.relatedTarget)) nudge(t, (e.movementX || (Math.random() - .5) * 4) * .02 + .08 * Math.sign(e.movementX || 1));
  });
  return { render, nudge };
})();
