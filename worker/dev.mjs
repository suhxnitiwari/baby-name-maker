// A local stand-in for the Cloudflare Worker, for building without a Cloudflare login: the real worker code runs in Node,
// and env.AI is a stand-in model. It reads requests with the page's own plain reader and writes reasons from the facts.
//   node dev.mjs                 → http://localhost:8787
//   STANDIN=liar node dev.mjs    → a model that invents names and meanings, to watch the checks throw its lines out
import http from "node:http";
import worker from "./lullabyte-ai.js";

const liar = process.env.STANDIN === "liar";
const between = (s, a, b) => { const i = s.indexOf(a), j = s.indexOf(b, i + a.length); return i < 0 || j < 0 ? "" : s.slice(i + a.length, j); };
const AI = {
  async run(model, { messages }) {
    const sys = messages[0].content, user = messages[messages.length - 1].content;
    await new Promise(r => setTimeout(r, 250));
    if (sys.startsWith("TASK: interpret")) return { choices: [{ message: { content: JSON.stringify(globalThis.Reader.read(between(user, "<request>", "</request>"))) } }] };
    const picks = JSON.parse(user.slice(user.indexOf("[")));
    const reasons = picks.map(p => {
      if (liar) return `${p.name} means "star of the sea", just like Isabella.`;
      if (p.near && p.near.length === 2) return `Close to ${p.near[0].name} in ${p.near[0].shares[0] || "sound"}, and to ${p.near[1].name} in ${p.near[1].shares[0] || "sound"}.`;
      const m = p.matched.slice(0, 2).join(" and ");
      return p.meaning ? `${m ? m.charAt(0).toUpperCase() + m.slice(1) : "Fits the wish"}, and it means ${p.meaning.split(/[,;]/)[0]}.` : `${m ? m.charAt(0).toUpperCase() + m.slice(1) : "Fits the wish"}.`;
    });
    return { choices: [{ message: { content: JSON.stringify({ reasons }) } }] };
  },
};

http.createServer(async (req, res) => {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  const headers = new Headers(Object.entries(req.headers).filter(([, v]) => typeof v === "string"));
  headers.set("CF-Connecting-IP", req.socket.remoteAddress || "local");
  const body = ["GET", "HEAD", "OPTIONS"].includes(req.method) ? undefined : Buffer.concat(chunks);
  const out = await worker.fetch(new Request(`http://localhost:8787${req.url}`, { method: req.method, headers, body }), { AI });
  res.writeHead(out.status, Object.fromEntries(out.headers));
  res.end(Buffer.from(await out.arrayBuffer()));
}).listen(8787, () => console.log(`Lullabyte's assistant (local stand-in${liar ? ", lying on purpose" : ""}) on http://localhost:8787`));
