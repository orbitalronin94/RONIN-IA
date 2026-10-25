# Ronin IA — OpenRouter gateway

Cloudflare Worker proxy so provider keys are not embedded in the Android APK or frontend source.

## Secrets

Create the secrets in the Cloudflare dashboard or with Wrangler. Never commit secret values:

```sh
npx wrangler secret put OPENROUTER_API_KEYS
# Enter a JSON array, e.g. ["sk-or-v1-...","sk-or-v1-..."]
npx wrangler secret put CLIENT_TOKEN
# Enter a long random token; generate it locally, e.g. openssl rand -hex 32
```

Create OpenRouter keys separately in the OpenRouter account dashboard. GitHub credentials do not create or authorize OpenRouter API keys. Use only keys that belong to you and set spending/rate limits in OpenRouter where available. Separate keys can be rotated/fail over, but they do not create more free quota or bypass provider limits.

## Deploy

Requires your own Cloudflare account and Wrangler authentication:

```sh
npm install --global wrangler
wrangler login
cd services/openrouter-gateway
wrangler deploy
```

Set `ALLOWED_ORIGINS` to the exact hosted web origin(s) after you know where the web app is hosted. Add rate limiting in Cloudflare for this Worker route before sharing it publicly. The Worker requires `Authorization: Bearer <CLIENT_TOKEN>`; however, a token embedded in a distributed APK can be extracted. It is an abuse deterrent, not strong user authentication. For public distribution, add user authentication and/or Cloudflare Turnstile plus per-user quotas before treating the gateway as production-secure.

## Configure the client

After deployment, note the Worker URL (typically `https://ronin-ia-gateway.<your-account-subdomain>.workers.dev`). Configure the frontend to call `/v1/chat/completions` on that URL and supply the client token only for private testing. Do not publish an APK with a shared secret and assume it cannot be extracted.

## Limits

- Requests are JSON only, capped at 48 KB and 12 messages.
- Only a short allowlist of free model IDs is accepted.
- Provider keys are held in Cloudflare Worker secrets, not plain-text vars.
- The Worker does not log prompt content intentionally.
- This is a starter gateway, not yet production-secure for an anonymous public app; rate limiting/authentication and abuse monitoring must be configured before public deployment.
