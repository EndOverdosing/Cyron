
![Cyron Search API](https://raw.githubusercontent.com/EndOverdosing/Cyron/refs/heads/main/static/assets/banner.png)


# Cyron Search API v4.0

Cyron is a privacy-focused meta search engine API built on SearX and deployed on Cloudflare Pages + Workers. It aggregates results from multiple search engines simultaneously without storing queries, setting cookies, or serving ads. All requests are distributed across a pool of SearX instances with automatic failover, so no single provider is a point of failure. The entire API runs at the edge, keeping latency low for users worldwide.

## Deploy

### Cloudflare Pages (recommended)

1. Push to GitHub/GitLab
2. In Cloudflare Dashboard → Pages → Create project → Connect repo
3. Build settings:
   - Framework preset: None
   - Build command: (leave empty)
   - Build output directory: `static`
4. Deploy

### Local dev

```bash
npm install
npm run dev
```

### Manual deploy via CLI

```bash
npm install -g wrangler
wrangler pages deploy static
```

## Project structure

```
cyron/
├── functions/
│   └── [[path]].js     # Catch-all Worker (all API routes)
├── static/
│   ├── index.html
│   ├── assets/
│   ├── _headers
│   └── _redirects
├── package.json
├── wrangler.toml
└── README.md
```

## API Reference

### GET /
Documentation

### POST /search
```json
{ "query": "...", "categories": "general", "language": "en", "per_page": 20 }
```

### GET /search/<query>
```
/search/mountains?categories=images&per_page=20
/search/news?categories=news&time_range=day
/search/anything?stream=true
```

### POST /search/stream
Same body as POST /search. Returns text/event-stream.

### GET /categories, /engines, /languages, /health, /stats

## Categories
general, images, videos, news, music, files, social_media, science, it

## Changes from v3 (Vercel/Flask)
- Rewritten in JavaScript for Cloudflare Workers runtime
- `Promise.race`-style parallel fetching — first valid response wins
- In-memory LRU cache with TTL (5 min, 512 entries)
- Regex-based HTML parser — no BeautifulSoup dependency
- Streaming via ReadableStream (native Workers API)
- Security headers via static/_headers