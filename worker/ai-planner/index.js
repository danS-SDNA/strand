// Strand AI planner. The model never picks places: it only translates a sentence into the same answers
// the tap-only planner takes (length, pace, fame, themes, kinds of place, breaks) plus a one-line intro.
// The phone then builds the tours from real Strand places. Small prompt, small reply, nothing invented.
const LEN = ["hours", "half", "day", "two", "three", "week"], PACE = ["gentle", "normal", "brisk"], FAME = ["famous", "mix", "hidden"], BREAKS = ["coffee", "pub"];

function cors(env) {
  return { "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN, "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type" };
}
function reply(env, status, body) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...cors(env) } });
}
async function bump(env, key, limit) {
  const n = parseInt((await env.CAPS.get(key)) || "0", 10);
  if (n >= limit) return false;
  await env.CAPS.put(key, String(n + 1), { expirationTtl: 60 * 60 * 26 });
  return true;
}

export default {
  async fetch(req, env) {
    if (req.method === "OPTIONS") return new Response(null, { headers: cors(env) });
    if (req.method !== "POST") return reply(env, 405, { error: "POST only" });
    let b;
    try { b = await req.json(); } catch { return reply(env, 400, { error: "Bad request" }); }
    const text = String(b.text || "").slice(0, 300).trim(), device = String(b.device || "").slice(0, 40);
    const themes = (b.themes || []).map(String).slice(0, 20), cats = (b.cats || []).map(String).slice(0, 20);
    if (text.length < 4 || !device) return reply(env, 400, { error: "Say a little more" });
    const day = new Date().toISOString().slice(0, 10);
    // device first: a device over its own cap must not use up everyone else's budget
    if (!(await bump(env, `d:${day}:${device}`, parseInt(env.DEVICE_DAILY, 10)))) return reply(env, 429, { error: "That is today's AI plans used up. The taps above still work." });
    if (!(await bump(env, `g:${day}`, parseInt(env.GLOBAL_DAILY, 10)))) return reply(env, 429, { error: "AI planning is resting for today. The taps above still work." });

    const sys = `You set up a London walking-tour planner from what a visitor says. Reply with JSON only:
{"len": one of ${JSON.stringify(LEN)}, "pace": one of ${JSON.stringify(PACE)}, "fame": one of ${JSON.stringify(FAME)},
 "themes": subset of ${JSON.stringify(themes)}, "cats": subset of ${JSON.stringify(cats)}, "breaks": subset of ${JSON.stringify(BREAKS)},
 "intro": "one friendly sentence, under 25 words, saying what you planned for them"}
Use only the values listed. Leave a field out when the visitor gives no clue. Never name places.`;
    const r = await fetch(`${env.AI_BASE}/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${env.AI_KEY}` },
      body: JSON.stringify({ model: env.AI_MODEL, temperature: 0.2, max_tokens: 300, messages: [{ role: "system", content: sys }, { role: "user", content: text }] }),
    });
    if (!r.ok) return reply(env, 502, { error: "Not available just now" });
    const out = await r.json();
    const m = (out.choices?.[0]?.message?.content || "").match(/\{[\s\S]*\}/);
    let a = {};
    try { a = m ? JSON.parse(m[0]) : {}; } catch { a = {}; }
    const pick = (v, list) => (list.includes(v) ? v : undefined), some = (v, list) => (Array.isArray(v) ? v.filter((x) => list.includes(x)) : []);
    const answers = { len: pick(a.len, LEN), pace: pick(a.pace, PACE), fame: pick(a.fame, FAME), themes: some(a.themes, themes), cats: some(a.cats, cats), breaks: some(a.breaks, BREAKS) };
    return reply(env, 200, { answers, intro: typeof a.intro === "string" ? a.intro.slice(0, 200) : "" });
  },
};
