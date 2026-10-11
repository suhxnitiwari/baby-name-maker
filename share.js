// ───────────────────────────────────────────────────────────
// SHARING THE CRADLE: a story-size card (1080 × 1920) of an open wooden music box with the names written inside its lid,
// and a link that opens the same names on anyone's phone, where a partner can say Love, Maybe or Pass and send their
// votes back. No account and no server: the names and the votes travel in the link itself.
//   ?list=Aria,Leo,Mila#cradle            a shortlist to hear and vote on
//   ?list=Aria,Leo,Mila&v=lmp#cradle      the same, with the other person's votes (l love, m maybe, p pass)
// ───────────────────────────────────────────────────────────
const Share = (() => {
  const W = 1080, H = 1920, C = { page: "#f6efe2", paper: "#fbf5e8", ink: "#241417", muted: "#574437", rose: "#a23d55", brass: "#c99a4c" };
  const SERIF = '"Instrument Serif", Georgia, serif', MONO = '"JetBrains Mono", ui-monospace, Menlo, monospace';
  const base = () => location.origin + location.pathname;
  const linkFor = (names, votes = "") => `${base()}?list=${names.map(encodeURIComponent).join(",")}${votes ? `&v=${votes}` : ""}#cradle`;
  const meaningOf = n => ((typeof BY_NAME !== "undefined" && BY_NAME.get(fold(n))) || []).find(x => x.m)?.m || "";
  const notesLine = n => MB.explain(n).map(p => `${p.text.toUpperCase()} ${p.notes[0] || ""}`.trim()).join("  ·  ");

  // ── the card ──
  function spaced(ctx, text, x, y, gap) {          // letter-spaced mono, centred on x
    const widths = [...text].map(ch => ctx.measureText(ch).width), total = widths.reduce((a, b) => a + b, 0) + gap * (text.length - 1);
    let cx = x - total / 2;
    [...text].forEach((ch, i) => { ctx.fillText(ch, cx + widths[i] / 2, y); cx += widths[i] + gap; });
  }
  function fit(ctx, text, font, size, max) {        // the largest size up to `size` that fits `max` pixels
    for (let s = size; s > 20; s -= 4) { ctx.font = font.replace("%", s); if (ctx.measureText(text).width <= max) return s; }
    return 20;
  }
  function rr(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
  function wood(ctx, y0, y1, light = false) {
    const g = ctx.createLinearGradient(0, y0, 0, y1);
    g.addColorStop(0, light ? "#f1dfbf" : "#e8cc9e"); g.addColorStop(.55, light ? "#e3c697" : "#d8b483"); g.addColorStop(1, light ? "#cda672" : "#c29966");
    return g;
  }
  function box(ctx) {
    // the lid, open and upright behind the box: a wooden frame round a paper panel
    ctx.save(); ctx.shadowColor = "rgba(90,60,40,.22)"; ctx.shadowBlur = 50; ctx.shadowOffsetY = 24;
    rr(ctx, 170, 560, 740, 640, 26); ctx.fillStyle = wood(ctx, 560, 1200, true); ctx.fill(); ctx.restore();
    rr(ctx, 204, 594, 672, 572, 14); ctx.fillStyle = C.paper; ctx.fill();
    rr(ctx, 222, 612, 636, 536, 8); ctx.strokeStyle = "rgba(201,154,76,.55)"; ctx.lineWidth = 2; ctx.stroke();
    // the velvet tray seen over the front edge
    rr(ctx, 186, 1196, 708, 34, 6); ctx.fillStyle = "#7d3445"; ctx.fill();
    // the body, with a darker rim, feet, a brass plaque and the winding key
    ctx.save(); ctx.shadowColor = "rgba(90,60,40,.25)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 20;
    rr(ctx, 150, 1222, 780, 330, 20); ctx.fillStyle = wood(ctx, 1222, 1552); ctx.fill(); ctx.restore();
    rr(ctx, 150, 1222, 780, 22, 10); ctx.fillStyle = "rgba(120,80,45,.25)"; ctx.fill();
    ctx.strokeStyle = "rgba(255,245,225,.35)"; ctx.lineWidth = 2;
    for (const y of [1300, 1470]) { ctx.beginPath(); ctx.moveTo(176, y); ctx.lineTo(904, y); ctx.stroke(); }
    ctx.fillStyle = wood(ctx, 1552, 1590); rr(ctx, 186, 1548, 70, 30, 8); ctx.fill(); rr(ctx, 824, 1548, 70, 30, 8); ctx.fill();
    const b = ctx.createLinearGradient(0, 1352, 0, 1418); b.addColorStop(0, "#ecd29b"); b.addColorStop(1, "#c08d40");
    rr(ctx, 380, 1352, 320, 66, 12); ctx.fillStyle = b; ctx.fill();
    ctx.font = `500 26px ${MONO}`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillStyle = "rgba(255,240,205,.7)"; spaced(ctx, "LULLABYTE", 540, 1387, 9);
    ctx.fillStyle = "#6b4a1e"; spaced(ctx, "LULLABYTE", 540, 1385, 9);
    ctx.fillStyle = wood(ctx, 1360, 1420); rr(ctx, 930, 1372, 34, 18, 6); ctx.fill();
    ctx.beginPath(); ctx.ellipse(978, 1381, 14, 30, 0, 0, Math.PI * 2); ctx.fill();
  }
  function notesFloating(ctx) {                   // a few notes drifting up out of the box
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    [[120, 700, 64, .5, C.brass], [960, 640, 54, .45, C.rose], [100, 980, 46, .35, C.rose], [985, 900, 70, .4, C.brass]].forEach(([x, y, s, a, c]) => {
      ctx.globalAlpha = a; ctx.fillStyle = c; ctx.font = `${s}px ${SERIF}`; ctx.fillText("♪", x, y);
    });
    ctx.globalAlpha = 1;
  }
  async function draw(names, one) {
    if (document.fonts) await document.fonts.ready;
    const cv = document.createElement("canvas"); cv.width = W; cv.height = H;
    const ctx = cv.getContext("2d");
    const bg = ctx.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, "#f8f2e6"); bg.addColorStop(1, "#ece0cb");
    ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
    ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
    ctx.font = `500 28px ${MONO}`; ctx.fillStyle = C.muted; spaced(ctx, one ? "OUR BABY'S NAME" : "OUR SHORTLIST", 540, 210, 8);
    // the headline: ink, with its last word in rose italic, as on the site
    const [a, b] = one ? ["We chose a ", "lullaby."] : ["Names we ", "love."];
    ctx.font = `400 118px ${SERIF}`; const wa = ctx.measureText(a).width;
    ctx.font = `italic 400 118px ${SERIF}`; const wb = ctx.measureText(b).width;
    let x = 540 - (wa + wb) / 2; ctx.textAlign = "left";
    ctx.font = `400 118px ${SERIF}`; ctx.fillStyle = C.ink; ctx.fillText(a, x, 380);
    ctx.font = `italic 400 118px ${SERIF}`; ctx.fillStyle = C.rose; ctx.fillText(b, x + wa, 380);
    ctx.textAlign = "center";
    notesFloating(ctx); box(ctx);
    // inside the lid
    if (one) {
      const n = names[0], s = fit(ctx, n, `400 %px ${SERIF}`, 190, 580);
      ctx.font = `400 ${s}px ${SERIF}`; ctx.fillStyle = C.ink; ctx.fillText(n, 540, 860);
      ctx.font = `500 26px ${MONO}`; ctx.fillStyle = C.muted; spaced(ctx, notesLine(n), 540, 940, 3);
      const m = meaningOf(n);
      if (m) { const ms = fit(ctx, `“${m}”`, `italic 400 %px ${SERIF}`, 54, 560); ctx.font = `italic 400 ${ms}px ${SERIF}`; ctx.fillStyle = C.rose; ctx.fillText(`“${m}”`, 540, 1040); }
    } else {
      const list = names.slice(0, 7), step = Math.min(78, 470 / list.length), top = 650 + (470 - step * list.length) / 2 + step * .7;
      list.forEach((n, k) => {
        const y = top + k * step, s = Math.min(fit(ctx, n, `400 %px ${SERIF}`, 64, 360), step * .82);
        ctx.textAlign = "left"; ctx.font = `400 ${s}px ${SERIF}`; ctx.fillStyle = C.ink; ctx.fillText(n, 262, y);
        ctx.textAlign = "right"; ctx.font = `500 22px ${MONO}`; ctx.fillStyle = C.muted;
        ctx.fillText(MB.explain(n).map(p => p.notes[0]).filter(Boolean).join(" "), 818, y - 6);
        if (k < list.length - 1) { ctx.strokeStyle = "rgba(201,154,76,.3)"; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(262, y + step * .32); ctx.lineTo(818, y + step * .32); ctx.stroke(); }
      });
      if (names.length > 7) { ctx.textAlign = "center"; ctx.font = `italic 400 34px ${SERIF}`; ctx.fillStyle = C.muted; ctx.fillText(`and ${names.length - 7} more`, 540, 1138); }
      ctx.textAlign = "center";
    }
    // how to hear them: a code to scan and the address
    const qr = await qrCode(linkFor(names));
    if (qr) {
      const size = 150, n = qr.getModuleCount(), cell = size / n, qx = 540 - size / 2, qy = 1666;
      rr(ctx, qx - 16, qy - 16, size + 32, size + 32, 18); ctx.fillStyle = C.paper; ctx.fill();
      ctx.fillStyle = C.ink;
      for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (qr.isDark(r, c)) ctx.fillRect(qx + c * cell, qy + r * cell, Math.ceil(cell), Math.ceil(cell));
    }
    ctx.font = `italic 400 40px ${SERIF}`; ctx.fillStyle = C.ink; ctx.fillText(one ? "Scan to hear it sing" : "Scan to hear them sing", 540, qr ? 1612 : 1700);
    ctx.font = `500 22px ${MONO}`; ctx.fillStyle = C.muted; spaced(ctx, "SUHXNITIWARI.GITHUB.IO/BABY-NAME-MAKER", 540, 1880, 2);
    return cv;
  }
  // the QR code library loads only when someone shares (cdnjs, MIT)
  let qrLib = null;
  function qrCode(text) {
    qrLib ||= new Promise(res => {
      const s = document.createElement("script");
      s.src = "https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js";
      s.onload = () => res(window.qrcode); s.onerror = () => res(null); document.head.appendChild(s);
    });
    return qrLib.then(q => { if (!q) return null; const c = q(0, "M"); c.addData(text); c.make(); return c; });
  }

  // ── the sheet ──
  let mode = "list", chosen = "";
  function open() {
    const names = Cradle.list;
    if (!names.length) return;
    chosen = names.includes(chosen) ? chosen : names[0];
    mode = names.length === 1 ? "one" : mode;
    const sh = $("#shareSheet");
    sh.innerHTML = `<button class="sheet-x" data-share-close aria-label="Close">×</button>
      <p class="kick">share the cradle</p><h3>A card for your <i>story.</i></h3>
      <div class="share-seg seg">${names.length > 1 ? `<button data-share-mode="list" aria-pressed="${mode === "list"}">our shortlist</button>` : ""}<button data-share-mode="one" aria-pressed="${mode === "one"}">one name</button></div>
      <div class="share-pick" ${mode === "one" && names.length > 1 ? "" : "hidden"}>${names.map(n => `<button data-share-pick="${esc(n)}" aria-pressed="${n === chosen}">${esc(n)}</button>`).join("")}</div>
      <div class="share-card"><canvas id="shareCanvas" width="${W}" height="${H}" aria-label="The card"></canvas></div>
      <div class="share-acts">
        <button class="go" data-share-card>Share the card</button>
        <button class="go quiet" data-share-vote>Send to vote on</button>
        <button class="link" data-share-link>copy the link</button>
      </div>
      <p class="share-note" id="shareNote">On a phone, “Share the card” opens Instagram Stories, Messages or WhatsApp. On a computer it saves the picture.</p>`;
    sh.hidden = false; requestAnimationFrame(() => sh.classList.add("on"));
    paint();
  }
  const current = () => mode === "one" ? [chosen] : Cradle.list;
  async function paint() {
    const cv = await draw(current(), mode === "one"), out = $("#shareCanvas");
    if (out) out.getContext("2d").drawImage(cv, 0, 0);
  }
  function close() { const sh = $("#shareSheet"); sh.classList.remove("on"); setTimeout(() => { sh.hidden = true; }, 300); }
  async function shareCard() {
    const names = current(), cv = await draw(names, mode === "one"), link = linkFor(names);
    const blob = await new Promise(r => cv.toBlob(r, "image/png"));
    const file = new File([blob], mode === "one" ? `${names[0]}-lullabyte.png` : "our-shortlist-lullabyte.png", { type: "image/png" });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      try { await navigator.share({ files: [file], text: link }); return; } catch (e) { if (e.name === "AbortError") return; }
    }
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = file.name; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    note("Saved the picture. Add it to your story, and the link is copied for the link sticker.");
    navigator.clipboard?.writeText(link);
  }
  async function sendLink(vote) {
    const names = mode === "one" ? [chosen] : Cradle.list, link = linkFor(names);
    const text = vote ? "Love, maybe or pass? Vote on our names here:" : "Hear our names:";
    if (navigator.share) { try { await navigator.share({ text, url: link }); return; } catch (e) { if (e.name === "AbortError") return; } }
    navigator.clipboard?.writeText(link);
    note(vote ? "Link copied. When they vote, they send you a link back with their answers." : "Link copied.");
  }
  const note = t => { const el = $("#shareNote"); if (el) el.textContent = t; };
  document.addEventListener("click", e => {
    const t = e.target;
    if (t.closest("[data-share-close]")) return close();
    const m = t.closest("[data-share-mode]");
    if (m) { mode = m.dataset.shareMode; $$("[data-share-mode]").forEach(b => b.setAttribute("aria-pressed", b === m)); $(".share-pick").hidden = !(mode === "one" && Cradle.list.length > 1); return paint(); }
    const p = t.closest("[data-share-pick]");
    if (p) { chosen = p.dataset.sharePick; $$("[data-share-pick]").forEach(b => b.setAttribute("aria-pressed", b === p)); return paint(); }
    if (t.closest("[data-share-card]")) return shareCard();
    if (t.closest("[data-share-vote]")) return sendLink(true);
    if (t.closest("[data-share-link]")) return sendLink(false);
  });
  addEventListener("keydown", e => { if (e.key === "Escape" && !$("#shareSheet").hidden) close(); });

  // ── a shortlist someone sent: hear it, vote, send the votes back ──
  const VOTE = { l: "Love", m: "Maybe", p: "Pass" };
  function received() {
    const q = new URLSearchParams(location.search), raw = q.get("list");
    if (!raw) return;
    const names = raw.split(",").map(s => capName(decodeURIComponent(s).trim())).filter(Boolean).slice(0, 30);
    if (!names.length) return;
    const theirs = (q.get("v") || "").split(""), key = "lullabyte-votes:" + names.map(fold).join(",");
    let mine = store.get(key, {});
    const panel = $("#sharedList");
    function render() {
      const both = names.filter((n, k) => theirs[k] === "l" && (mine[fold(n)] || (Cradle.has(n) ? "l" : "")) === "l");
      panel.innerHTML = `<p class="kick">${theirs.length ? "their votes are in" : "a shortlist, sent to you"}</p>
        <h3>${theirs.length ? "Love, maybe or <i>pass?</i>" : "Hear them, then <i>vote.</i>"}</h3>
        ${both.length ? `<p class="shared-match">You both love ${both.map(esc).join(both.length > 2 ? ", " : " and ")}.</p>` : ""}
        <div class="shared-rows">${names.map((n, k) => {
          const v = mine[fold(n)] || "", t = theirs[k];
          return `<div class="shared-row${both.includes(n) ? " match" : ""}"><button class="shared-name" data-play-name="${esc(n)}">${esc(n)} <span>♪</span></button>
            ${t && VOTE[t] ? `<small class="shared-theirs">they said ${VOTE[t].toLowerCase()}</small>` : ""}
            <span class="shared-votes">${Object.entries(VOTE).map(([c, w]) => `<button data-vote="${k}" data-v="${c}" aria-pressed="${v === c}">${w}</button>`).join("")}</span></div>`;
        }).join("")}</div>
        <div class="share-acts"><button class="go" data-votes-back>Send my votes back</button><button class="link" data-keep-all>keep them all in my cradle</button></div>
        <p class="share-note" id="votesNote"></p>`;
    }
    panel.hidden = false; render();
    panel.addEventListener("click", async e => {
      const b = e.target.closest("[data-vote]");
      if (b) { const n = names[+b.dataset.vote]; mine[fold(n)] = mine[fold(n)] === b.dataset.v ? "" : b.dataset.v; store.set(key, mine); MB.tick(.5); return render(); }
      if (e.target.closest("[data-keep-all]")) { names.forEach(n => Cradle.has(n) || Cradle.toggle(n)); $("#votesNote").textContent = "In your cradle now."; return; }
      if (e.target.closest("[data-votes-back]")) {
        const v = names.map(n => mine[fold(n)] || "-").join(""), link = linkFor(names, v);
        if (navigator.share) { try { await navigator.share({ text: "My votes on our names:", url: link }); return; } catch (err) { if (err.name === "AbortError") return; } }
        navigator.clipboard?.writeText(link); $("#votesNote").textContent = "Link copied. Send it back, and the names you both love light up.";
      }
    });
    // once the page has opened (after the sound gate for a first visit), go straight to the shortlist
    const go = () => setTimeout(() => $("#sharedList").scrollIntoView({ behavior: "smooth", block: "start" }), 900);
    document.body.classList.contains("awake") ? go() : new MutationObserver((_, o) => { if (document.body.classList.contains("awake")) { o.disconnect(); go(); } }).observe(document.body, { attributes: true, attributeFilter: ["class"] });
  }
  return { open, received, draw, linkFor };
})();
$("#cradleShare").onclick = () => Share.open();
Share.received();
