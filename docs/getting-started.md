# Getting Started

## Requirements

- A Cloudflare account (free tier works)
- Node.js 18+ and npm (for local development only)

## Local Development

```bash
git clone https://github.com/yourname/cyron.git
cd cyron
npm install
npm run dev
```

The API will be available at `http://localhost:8788`.

## Making Your First Request

```bash
curl "http://localhost:8788/search/artificial intelligence?per_page=5"
```

```bash
curl -X POST http://localhost:8788/search \
  -H "Content-Type: application/json" \
  -d '{"query": "neural networks", "categories": "science", "per_page": 10}'
```

## Response Shape

Every successful response includes:

- `success` — boolean
- `query` — the original query string
- `params` — the resolved parameters used
- `meta` — source instance and result counts
- `results.all` — flat array of all results
- `results.by_type` — results grouped by category type
- `answers` — direct answers if available
- `infobox` — knowledge panel if available
- `suggestions` — related search suggestions
- `pagination` — current page info and next page number

## Result Types

Each result object always contains `type`, `url`, and `title`. Additional fields depend on type:

| Type | Extra Fields |
|------|-------------|
| general | content, thumbnail, publishedDate, engines, score |
| images | img_src, thumbnail |
| videos | iframe_src, thumbnail, duration, views, publishedDate |
| news | content, publishedDate, thumbnail |
| science | authors, journal, doi, publishedDate |
| files | filesize, seed, leech, magnet |
| music | artist, album, duration |
| social_media | username, publishedDate |
| it | content, engines |