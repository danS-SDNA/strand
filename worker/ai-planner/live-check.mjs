// One real call through the worker code against Kimi, to measure latency and tokens. Key from AI_KEY env.
import w from "./index.js";
const kv = new Map();
const model = process.argv[2] || "kimi-k3";
const env = { AI_BASE: "https://api.moonshot.ai/v1", AI_MODEL: model, AI_THINKING: process.argv[4] || "disabled", AI_KEY: process.env.AI_KEY, DEVICE_DAILY: "5", GLOBAL_DAILY: "500", ALLOWED_ORIGIN: "https://dans-sdna.github.io",
  CAPS: { get: async (k) => kv.get(k) ?? null, put: async (k, v) => { kv.set(k, v); } } };
const realFetch = globalThis.fetch; let usage = null;
globalThis.fetch = async (u, o) => { const r = await realFetch(u, o); const t = await r.text(); try { usage = JSON.parse(t).usage; } catch {} if (!r.ok) console.log("upstream", r.status, t.slice(0, 400)); return new Response(t, { status: r.status }); };
const t0 = Date.now();
const r = await w.fetch(new Request("https://x/", { method: "POST", body: JSON.stringify({ text: process.argv[3] || "Two days in London, I love Dickens and old pubs, not too much walking, and I need my coffee", device: "check",
  themes: ["writers", "science", "art", "stage", "royal", "politics", "war", "faith"], cats: ["museums", "churches", "pubs", "outdoors", "graves", "monuments"] }) }), env);
console.log(model, "status", r.status, "in", Date.now() - t0, "ms; usage", JSON.stringify(usage));
console.log(JSON.stringify(await r.json()));
