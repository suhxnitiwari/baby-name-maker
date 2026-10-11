// ───────────────────────────────────────────────────────────
// THE PICKER: the sentence menus (the duet's "any faith", the charts' "the United States") open as a small paper card in
// the site's own type instead of the browser's grey list. The real <select> stays underneath, so its value, its change
// events and the phone's own wheel (on touch) all work as before. Long lists get a search line at the top.
// ───────────────────────────────────────────────────────────
(() => {
  let menu = null, owner = null, items = [], at = -1;
  const close = () => { if (!menu) return; menu.remove(); menu = null; owner && owner.classList.remove("picking"); owner = null; };
  function choose(v) {
    const sel = owner; close();
    if (sel.value !== v) { sel.value = v; sel.dispatchEvent(new Event("input", { bubbles: true })); sel.dispatchEvent(new Event("change", { bubbles: true })); }
    sel.focus({ preventScroll: true });
  }
  function mark(i) {
    const shown = items.filter(b => !b.hidden);
    if (!shown.length) return;
    at = (i + shown.length) % shown.length;
    shown.forEach((b, k) => b.classList.toggle("on", k === at));
    shown[at].scrollIntoView({ block: "nearest" });
  }
  function place() {
    const r = owner.getBoundingClientRect(), h = Math.min(menu.scrollHeight, 340), below = innerHeight - r.bottom - 12;
    menu.style.left = Math.max(12, Math.min(r.left, innerWidth - menu.offsetWidth - 12)) + "px";
    menu.style.top = (below >= Math.min(h, 220) ? r.bottom + 8 : Math.max(12, r.top - h - 8)) + "px";
  }
  function open(sel) {
    close(); owner = sel; sel.classList.add("picking");
    menu = document.createElement("div"); menu.className = "picker"; menu.setAttribute("role", "listbox");
    const opts = [...sel.options];
    const search = opts.length > 12 ? `<input class="picker-find" placeholder="type to find…" aria-label="Find in the list">` : "";
    menu.innerHTML = search + `<div class="picker-list">${opts.map(o => `<button type="button" role="option" data-v="${o.value.replace(/"/g, "&quot;")}" aria-selected="${o.value === sel.value}"${o.value === sel.value ? ' class="cur"' : ""}>${o.text.replace(/</g, "&lt;")}</button>`).join("")}</div>`;
    document.body.appendChild(menu);
    items = [...menu.querySelectorAll("button")];
    place();
    const cur = items.findIndex(b => b.classList.contains("cur"));
    at = -1; if (cur >= 0) items[cur].scrollIntoView({ block: "center" });
    const find = menu.querySelector(".picker-find");
    if (find) {
      find.focus({ preventScroll: true });
      find.addEventListener("input", () => { const q = find.value.trim().toLowerCase(); items.forEach(b => b.hidden = q && !b.textContent.toLowerCase().includes(q)); mark(0); });
    }
    menu.addEventListener("click", e => { const b = e.target.closest("button[data-v]"); if (b) choose(b.dataset.v); });
    menu.addEventListener("keydown", key);
  }
  function key(e) {
    if (!menu) return;
    if (e.key === "Escape") { const s = owner; close(); s && s.focus(); e.preventDefault(); }
    else if (e.key === "ArrowDown") { mark(at + 1); e.preventDefault(); }
    else if (e.key === "ArrowUp") { mark(at - 1); e.preventDefault(); }
    else if (e.key === "Enter") { const shown = items.filter(b => !b.hidden); if (shown[at < 0 ? 0 : at]) choose(shown[at < 0 ? 0 : at].dataset.v); e.preventDefault(); }
  }
  // a mouse or trackpad opens the paper menu; a finger keeps the phone's own picker, which already fits the hand
  document.addEventListener("pointerdown", e => {
    const sel = e.target.closest && e.target.closest("select.slot");
    if (sel && e.pointerType !== "touch") { e.preventDefault(); sel === owner ? close() : open(sel); return; }
    if (menu && !menu.contains(e.target)) close();
  }, true);
  document.addEventListener("keydown", e => {
    const sel = document.activeElement;
    if (!menu && sel && sel.matches && sel.matches("select.slot") && [" ", "Enter", "ArrowDown"].includes(e.key)) { e.preventDefault(); open(sel); }
    else key(e);
  }, true);
  addEventListener("resize", close);
  addEventListener("scroll", () => menu && owner && place(), { passive: true });
})();
