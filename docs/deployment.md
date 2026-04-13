# Deployment

## Cloudflare Pages (Recommended)

1. Push the repository to GitHub or GitLab
2. Go to [Cloudflare Dashboard](https://dash.cloudflare.com) → Workers & Pages → Create
3. Connect your repository
4. Set build configuration:
   - Framework preset: `None`
   - Build command: *(leave empty)*
   - Build output directory: `static`
5. Click Deploy

Cloudflare automatically detects `functions/[[path]].js` and deploys it as a Worker alongside your static assets.

## Wrangler CLI

```bash
npm install -g wrangler
wrangler login
wrangler pages deploy static
```

## Custom Domain

In Cloudflare Pages → your project → Custom Domains → Add domain.

## Environment Variables

No environment variables are required. Optional overrides can be set in the Cloudflare Pages dashboard under Settings → Environment Variables, then accessed in the Worker via `context.env`.

## Compatibility

The Worker uses `compatibility_date: 2024-04-01` with `nodejs_compat` flag enabled via `wrangler.toml`. Do not remove these — they are required for the `URL`, `fetch`, and `ReadableStream` APIs used in the Worker.