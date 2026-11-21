// Strand ratings. POST /rate stores one rating per phone per place (overall stars, optional, and what the place was
// good for, from a fixed list). GET /summary returns, for every rated place, the count, star total and tag counts;
// the app turns those into a confidence-weighted average and copper / silver / gold tiers.
// Not stored: names, accounts, locations. The device id is a random string the phone made for itself.
const TAGS = ["history", "culture", "wow", "quirky", "kids", "peaceful"];
const PLACE = /^(Q\d{1,10}|z:[a-z0-9-]{1,60})$/;
const DEVICE = /^[a-z0-9]{8,40}$/;

function cors(env, req) {
  const o = req.headers.get("Origin") || "";
  const allowed = env.ALLOWED_ORIGINS.split(",");
  return { "Access-Control-Allow-Origin": allowed.includes(o) ? o : allowed[0], "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
           "Access-Control-Allow-Headers": "Content-Type", "Vary": "Origin" };
}
function reply(env, req, status, body, extra = {}) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...cors(env, req), ...extra } });
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, { headers: cors(env, req) });

    if (req.method === "GET" && url.pathname === "/summary") {
      const cache = caches.default, key = new Request(url.origin + "/summary");
      const hit = await cache.match(key);
      if (hit) { const r = new Response(hit.body, hit); Object.entries(cors(env, req)).forEach(([k, v]) => r.headers.set(k, v)); return r; }
      const rows = (await env.DB.prepare("SELECT place, COUNT(*) n, COUNT(stars) ns, COALESCE(SUM(stars),0) s, GROUP_CONCAT(tags, ',') t FROM ratings GROUP BY place").all()).results;
      const out = {};
      for (const r of rows) {
        const tc = {};
        for (const t of (r.t || "").split(",")) if (t) tc[t] = (tc[t] || 0) + 1;
        out[r.place] = { n: r.n, ns: r.ns, s: r.s, t: tc };
      }
      const res = reply(env, req, 200, { places: out, at: Date.now() }, { "Cache-Control": "public, max-age=60" });
      ctx.waitUntil(cache.put(key, res.clone()));
      return res;
    }

    if (req.method === "POST" && url.pathname === "/rate") {
      let b;
      try { b = await req.json(); } catch { return reply(env, req, 400, { error: "Bad request" }); }
      const device = String(b.device || ""), place = String(b.place || "");
      if (!DEVICE.test(device) || !PLACE.test(place)) return reply(env, req, 400, { error: "Bad place or device" });
      const stars = b.stars == null ? null : Number(b.stars);
      if (stars != null && !(Number.isInteger(stars) && stars >= 1 && stars <= 5)) return reply(env, req, 400, { error: "Stars must be 1 to 5" });
      const tags = [...new Set((Array.isArray(b.tags) ? b.tags : []).map(String).filter((t) => TAGS.includes(t)))];
      if (stars == null && !tags.length) {  // an empty rating withdraws the phone's rating for that place
        await env.DB.prepare("DELETE FROM ratings WHERE device=?1 AND place=?2").bind(device, place).run();
        await caches.default.delete(new Request(url.origin + "/summary"));
        return reply(env, req, 200, { ok: true, withdrawn: true });
      }
      const day = new Date().toISOString().slice(0, 10);
      const d = await env.DB.prepare("INSERT INTO daily (device, day, n) VALUES (?1, ?2, 1) ON CONFLICT(device, day) DO UPDATE SET n = n + 1 RETURNING n").bind(device, day).first();
      if (d && d.n > parseInt(env.DEVICE_DAILY, 10)) return reply(env, req, 429, { error: "That's a lot of ratings for one day. Thank you! Try again tomorrow." });
      await env.DB.prepare("INSERT INTO ratings (device, place, stars, tags, ts) VALUES (?1, ?2, ?3, ?4, ?5) ON CONFLICT(device, place) DO UPDATE SET stars=?3, tags=?4, ts=?5")
        .bind(device, place, stars, tags.join(","), Date.now()).run();
      await caches.default.delete(new Request(url.origin + "/summary"));
      return reply(env, req, 200, { ok: true });
    }
    return reply(env, req, 404, { error: "Not found" });
  },
};
