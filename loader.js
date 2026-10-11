// ───────────────────────────────────────────────────────────
// THE LOADER: a background worker that downloads and reads the big data files, so the page never stops to parse
// 13 MB of JSON while someone is typing. It hands the result back in small pieces (a few hundred rows at a time); each
// piece is quick for the page to take in, and the mobile keeps turning between them.
//   { id, url, kind: "json" | "lines" } →  { id, at: [key] | [], items } … then { id, done } (or { id, error })
// ───────────────────────────────────────────────────────────
const PIECE = 400;            // rows of a big list per message
// pieces are spaced out, so the page takes them in between frames instead of all in one go
const queues = new Map();     // each file keeps its own queue, so two files loading at once never mix their pieces
const post = m => (queues.get(m.id) || queues.set(m.id, []).get(m.id)).push(m);
async function flush(id) {
  const q = queues.get(id) || [];
  for (const m of q) { postMessage(m); if (m.items || m.pairs) await new Promise(r => setTimeout(r, 6)); }
  queues.delete(id);
}
const send = (id, at, items) => post({ id, at, items });
function stream(id, at, value) {
  if (Array.isArray(value)) {
    if (value.length <= PIECE) return send(id, at, value);
    for (let i = 0; i < value.length; i += PIECE) send(id, at, value.slice(i, i + PIECE));
    return;
  }
  if (value && typeof value === "object") {
    const keys = Object.keys(value);
    if (!at.length && keys.length > 200) { post({ id, shape: null }); for (let i = 0; i < keys.length; i += PIECE) post({ id, at, pairs: keys.slice(i, i + PIECE).map(k => [k, value[k]]) }); return; }
    if (!at.length) { post({ id, shape: Object.fromEntries(keys.map(k => [k, Array.isArray(value[k]) ? "a" : value[k] && typeof value[k] === "object" ? "o" : "v"])) }); keys.forEach(k => stream(id, [k], value[k])); return; }
    // a big object (a lookup of 50,000 names): sent as [key, value] pairs
    for (let i = 0; i < keys.length; i += PIECE) post({ id, at, pairs: keys.slice(i, i + PIECE).map(k => [k, value[k]]) });
    return;
  }
  post({ id, at, value });
}
onmessage = async e => {
  const { id, url, kind } = e.data;
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${r.status} ${url}`);
    if (kind === "lines") {
      const lines = (await r.text()).split("\n");
      for (let i = 0; i < lines.length; i += PIECE * 25) send(id, [], lines.slice(i, i + PIECE * 25));
    } else stream(id, [], await r.json());
    await flush(id);
    postMessage({ id, done: true });
  } catch (err) { postMessage({ id, error: String(err) }); }
};
