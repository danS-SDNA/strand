// Local check of the worker with a stand-in model; no network, no key.
import w from "./index.js";
const kv = new Map();
const env = { AI_BASE: "https://example.invalid/v1", AI_MODEL: "m", AI_KEY: "k", DEVICE_DAILY: "2", GLOBAL_DAILY: "3", ALLOWED_ORIGIN: "https://dans-sdna.github.io",
  CAPS: { get: async (k) => kv.get(k) ?? null, put: async (k, v) => { kv.set(k, v); } } };
let seen;
globalThis.fetch = async (url, init) => { seen = JSON.parse(init.body);
  return new Response(JSON.stringify({ choices: [{ message: { content: 'Sure: {"len":"two","pace":"gentle","fame":"famous","themes":["writers","dragons"],"cats":["pubs"],"breaks":["pub","nap"],"intro":"Two gentle days of writers and old pubs."}' } }] })); };
const call = (device, text = "two days, Dickens and old pubs, not much walking") => w.fetch(new Request("https://x/", { method: "POST", body: JSON.stringify({ text, device, themes: ["writers", "science"], cats: ["pubs", "museums"] }) }), env);
let fails = 0; const ok = (c, m) => { if (!c) { fails++; console.log("FAIL", m); } else console.log("ok  ", m); };
let r = await call("a"); let j = await r.json();
ok(r.status === 200, "200 for a normal request");
ok(j.answers.len === "two" && j.answers.pace === "gentle" && j.answers.fame === "famous", "length, pace and fame read");
ok(JSON.stringify(j.answers.themes) === '["writers"]', "invented theme 'dragons' dropped");
ok(JSON.stringify(j.answers.breaks) === '["pub"]', "invented break 'nap' dropped");
ok(j.intro.startsWith("Two gentle days"), "intro passed through");
ok(seen.messages[0].content.includes('"writers","science"'), "allowed themes sent to the model");
ok(r.headers.get("Access-Control-Allow-Origin") === "https://dans-sdna.github.io", "CORS limited to the site");
r = await call("a"); ok(r.status === 200, "second plan for device a allowed");
r = await call("a"); ok(r.status === 429, "third plan for device a refused (device cap 2)");
r = await call("b"); ok(r.status === 200, "device b still served: a's refused calls did not use the shared budget");
r = await call("c"); ok(r.status === 429, "device c refused once the global cap (3) is reached");
r = await call("d", "hi"); ok(r.status === 400, "too-short text refused before spending anything");
console.log(fails ? `${fails} FAILED` : "all passed");
process.exit(fails ? 1 : 0);
