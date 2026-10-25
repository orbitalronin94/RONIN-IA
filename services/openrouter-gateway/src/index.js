const JSON_HEADERS = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
const MAX_BODY_BYTES = 48_000;
const ALLOWED_MODELS = new Set(["openrouter/free", "google/gemma-3-4b-it:free", "meta-llama/llama-3.3-70b-instruct:free"]);

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), { status, headers: { ...JSON_HEADERS, ...extra } });
}

function corsHeaders(request, env) {
  const origin = request.headers.get("Origin") || "";
  const allowed = (env.ALLOWED_ORIGINS || "").split(",").map(s => s.trim()).filter(Boolean);
  const headers = { "vary": "Origin" };
  if (origin && allowed.includes(origin)) {
    headers["access-control-allow-origin"] = origin;
    headers["access-control-allow-methods"] = "POST, OPTIONS";
    headers["access-control-allow-headers"] = "content-type, authorization";
    headers["access-control-max-age"] = "86400";
  }
  return headers;
}

function keysFromSecret(raw) {
  try {
    const value = JSON.parse(raw || "[]");
    if (Array.isArray(value)) return value.filter(k => typeof k === "string" && k.startsWith("sk-or-") && k.length > 20);
  } catch {}
  return [];
}

function validMessages(messages) {
  return Array.isArray(messages) && messages.length > 0 && messages.length <= 12 &&
    messages.every(m => m && ["system", "user", "assistant"].includes(m.role) &&
      typeof m.content === "string" && m.content.length <= 8000);
}

export default {
  async fetch(request, env) {
    const cors = corsHeaders(request, env);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (request.method !== "POST") return json({ error: { message: "Method not allowed" } }, 405, cors);

    const origin = request.headers.get("Origin") || "";
    const allowed = (env.ALLOWED_ORIGINS || "").split(",").map(s => s.trim()).filter(Boolean);
    if (origin && !allowed.includes(origin)) return json({ error: { message: "Origin not allowed" } }, 403, cors);

    const clientToken = env.CLIENT_TOKEN;
    if (!clientToken || request.headers.get("Authorization") !== `Bearer ${clientToken}`) {
      return json({ error: { message: "Unauthorized" } }, 401, cors);
    }

    const length = Number(request.headers.get("content-length") || 0);
    if (length > MAX_BODY_BYTES) return json({ error: { message: "Request too large" } }, 413, cors);

    let body;
    try { body = await request.json(); } catch { return json({ error: { message: "Invalid JSON" } }, 400, cors); }
    if (!validMessages(body.messages)) {
      return json({ error: { message: "messages must contain 1–12 valid chat messages" } }, 400, cors);
    }

    const configuredModels = (env.MODELS || "openrouter/free")
      .split(",").map(s => s.trim()).filter(m => ALLOWED_MODELS.has(m));
    const models = configuredModels.length ? configuredModels : ["openrouter/free"];
    const keys = keysFromSecret(env.OPENROUTER_API_KEYS);
    if (!keys.length) return json({ error: { message: "Gateway not configured: add OPENROUTER_API_KEYS as a Cloudflare secret." } }, 503, cors);

    let lastStatus = 502;
    for (const model of models) {
      for (const key of keys) {
        try {
          const upstream = await fetch("https://openrouter.ai/api/v1/chat/completions", {
            method: "POST",
            headers: {
              "authorization": `Bearer ${key}`,
              "content-type": "application/json",
              "http-referer": env.APP_URL || "https://github.com/orbitalronin94/RONIN-IA",
              "x-title": "Ronin IA"
            },
            body: JSON.stringify({
              model,
              messages: body.messages.map(m => ({ role: m.role, content: m.content.slice(0, 6000) })),
              max_tokens: Math.min(Math.max(Number(body.max_tokens) || 600, 1), 1000),
              temperature: 0.6,
              stream: false
            })
          });
          if (upstream.ok) {
            const data = await upstream.json();
            const content = data?.choices?.[0]?.message?.content;
            if (!content) { lastStatus = 502; continue; }
            return json({ choices: [{ message: { role: "assistant", content } }] }, 200, cors);
          }
          lastStatus = upstream.status;
          if (![401, 402, 403, 429, 500, 502, 503, 504].includes(upstream.status)) {
            return json({ error: { message: "Provider rejected the request", status: upstream.status } }, upstream.status, cors);
          }
        } catch {
          lastStatus = 502;
        }
      }
    }
    const status = lastStatus === 429 ? 429 : lastStatus === 402 ? 402 : 502;
    return json({ error: { message: status === 429 ? "All configured provider keys are rate-limited." : status === 402 ? "Provider credits are unavailable." : "No configured model/key could complete the request." } }, status, cors);
  }
};
