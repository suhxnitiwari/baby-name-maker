// ─────────────────────────────────────────────────────────────
// LULLA: the little robot assistant. Eyes follow the cursor, it narrates
// what the algorithm is doing, and the form questions type themselves out.
// Wraps the view functions from index.html / compiler.js / taste.js.
// ─────────────────────────────────────────────────────────────
const bot = (() => {
  const el = $("#bot"), bubble = $("#botSay");
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let typing = 0, idleTimer = 0, moodTimer = 0, chatty = true;

  function say(text, mood) {
    if (mood) setMood(mood);
    clearTimeout(typing);
    if (still) { bubble.textContent = text; return; }
    let i = 0;
    const tick = () => { bubble.textContent = text.slice(0, ++i); if (i < text.length) typing = setTimeout(tick, 18); };
    tick();
  }
  function setMood(m) {
    el.classList.remove("happy", "think");
    if (m && m !== "idle") el.classList.add(m);
    clearTimeout(moodTimer);
    if (m === "happy") moodTimer = setTimeout(() => el.classList.remove("happy"), 2600);
  }
  // eyes follow the cursor
  addEventListener("pointermove", e => {
    const r = el.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height * .4;
    const dx = Math.max(-1, Math.min(1, (e.clientX - cx) / 500)), dy = Math.max(-1, Math.min(1, (e.clientY - cy) / 400));
    el.style.setProperty("--ex", (dx * 11).toFixed(1) + "px");
    el.style.setProperty("--ey", (dy * 6).toFixed(1) + "px");
  }, { passive: true });

  // intro lines, until the user starts doing things
  function intro(total) {
    const lines = ["hi. i'm lulla, your naming assistant.", `i've read ${total} names.`,
      "i check sound, meaning, flow & official records.", "tell me who we're naming ↓"];
    let k = 0;
    const next = () => { if (!chatty) return; say(lines[k % lines.length]); k++; if (k < lines.length) idleTimer = setTimeout(next, 3200); };
    next();
  }
  const quiet = () => { chatty = false; clearTimeout(idleTimer); };
  return { say, setMood, intro, quiet };
})();

// ── narrate the views ──
const countOf = () => { const b = $("#count b"); return b ? b.textContent : ""; };
// the automatic search on page load shouldn't interrupt Lulla's hello
let booted = false;
addEventListener("DOMContentLoaded", () => setTimeout(() => { booted = true; }, 0));
function narrate(fnName, before, after) {
  const orig = window[fnName];
  if (typeof orig !== "function") return;
  window[fnName] = function (...args) {
    if (!booted) { const out = orig.apply(this, args); if (fnName === "find") setTimeout(addSearchLog, 0); return out; }
    bot.quiet();
    before && before();
    const out = orig.apply(this, args);
    after && setTimeout(after, 380);
    return out;
  };
}
narrate("find", () => bot.say("analyzing candidates…", "think"), () => { addSearchLog(); bot.say(countOf() ? `scanned ${countOf()} matches. here's what i found.` : "nothing matched. try loosening a filter?", countOf() ? "happy" : "idle"); });
narrate("blend", () => { const a = $("#mom").value.trim(), b = $("#dad").value.trim(); if (a && b) bot.say(`splicing ${a.toLowerCase()} × ${b.toLowerCase()}…`, "think"); },
  () => { const f = $("#results .featured .name"); if (f) setTimeout(() => bot.say(`compiled. meet ${f.textContent}.`, "happy"), 2000); });
narrate("showTaste", () => taste.love.length && bot.say("learning your taste…", "think"),
  () => { const c = document.querySelector(".genome-head span:last-child"); if (c) bot.say(`profile ready · ${c.textContent}.`, "happy"); });
narrate("showPopular", () => bot.say("pulling official records…", "think"), () => bot.say("official numbers, straight from the source.", "idle"));
narrate("spell", () => $("#spellIn").value.trim() && bot.say("tracing spellings…", "think"), () => $("#spellIn").value.trim() && bot.say("here's how people really spell it.", "happy"));

// react to choices in the form
$$(".gbtn").forEach(b => b.addEventListener("click", () => { bot.quiet(); bot.say(`noted: ${b.textContent.trim().toLowerCase()}.`); }));
["#theme", "#vibeSel", "#religion", "#culture", "#lang", "#len", "#first"].forEach(sel => $(sel).addEventListener("change", e => {
  const o = e.target.selectedOptions[0]; bot.quiet(); bot.say(o && o.value ? `${o.text.toLowerCase()}. got it.` : "okay, no preference.");
}));
$("#lastName").addEventListener("change", () => { const l = lastName(); if (l) bot.say(`i'll test every name with ${l}.`); });

// ── the form questions type themselves out ──
const _wizShow = wizShow;
wizShow = function () {
  _wizShow();
  const q = $("#panel .step.active .step-q");
  if (!q) return;
  q.dataset.full ??= q.textContent;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const full = q.dataset.full; let i = 0;
  clearTimeout(q._t);
  const tick = () => { q.textContent = full.slice(0, ++i); if (i < full.length) q._t = setTimeout(tick, 22); };
  tick();
};
wizShow();

// ── search log for Find names: real counts at each stage ──
function addSearchLog() {
  if (tab !== "find") return;
  const f = filters(), log = [];
  let pool = [...REAL, ...ROOT_NAMES].filter(genderOk).concat(invented(gender));
  log.push([`indexing ${gender === "either" ? "gender-neutral" : gender === "girl" ? "feminine" : "masculine"} names`, pool.length.toLocaleString()]);
  if (f.theme || f.vibe) {
    pool = pool.filter(x => (!f.theme || themesOf(x).includes(f.theme)) && (!f.vibe || vibeMatch(x, f.vibe)));
    log.push(["matching meaning & vibe", `→ ${pool.length.toLocaleString()}`]);
  }
  if (f.religion || f.culture || f.lang) {
    pool = pool.filter(x => (!f.religion || x.r.includes(f.religion)) && (!f.culture || x.o === f.culture) && (!f.lang || x.l === f.lang));
    log.push(["checking religion, culture & language", `→ ${pool.length.toLocaleString()}`]);
  }
  if (f.first || f.first2 || f.ends || f.len) {
    pool = pool.filter(x => { const n = fold(x.n); return (!f.first || n.startsWith(f.first)) && (!f.first2 || n.startsWith(f.first2)) && (!f.ends || n.endsWith(f.ends)) && lenOk(x.n, f.len); });
    log.push(["fitting letters & length", `→ ${pool.length.toLocaleString()}`]);
  }
  if (lastName()) log.push([`testing flow with ${lastName()}`, "on every card"]);
  log.push(["mixing real · root-built · invented", `showing ${$$("#results .card").length}`]);
  $("#results").insertAdjacentHTML("afterbegin", pipelineHTML(log, "lulla · search"));
}

bot.intro((REAL.length + ROOT_NAMES.length + ["girl", "boy", "either"].reduce((t, g) => t + invented(g).length, 0)).toLocaleString());

