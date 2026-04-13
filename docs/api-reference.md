# API Reference

## Base URL

```
https://your-project.pages.dev
```

## Authentication

None. The API is public and requires no API keys.

## Request Format

All POST endpoints accept `application/json` bodies. GET endpoints use query string parameters.

## Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | The search term |
| `categories` | string or array | general | Comma-separated or JSON array of categories |
| `engines` | string or array | auto | Specific engines to target |
| `language` | string | all | Language code: en, de, fr, es, it, pt, nl, pl, ru, zh, ja, ko, ar, hi, tr, vi, th, uk, cs, sv, da, fi, no, hu, ro, bg, hr, sk, sl |
| `time_range` | string | any | `day`, `week`, `month`, or `year` |
| `safesearch` | integer | 1 | `0` = off, `1` = moderate, `2` = strict |
| `pageno` | integer | 1 | Page number for pagination |
| `per_page` | integer | all | Results to return, 1–100 |

## Categories

| Category | Description |
|----------|-------------|
| general | Standard web results |
| images | Images with `img_src` |
| videos | Videos with `iframe_src` and `duration` |
| news | News articles with `publishedDate` |
| music | Tracks with `artist` and `album` |
| files | Torrents/files with `filesize`, `seed`, `leech` |
| social_media | Posts and profiles |
| science | Academic papers with `authors`, `journal`, `doi` |
| it | Code, repos, Stack Overflow answers |

## Engines by Category

| Category | Engines |
|----------|---------|
| general | google, bing, duckduckgo, brave, yahoo, startpage, qwant, wikipedia, wikidata |
| images | bing_images, google_images, flickr, unsplash |
| videos | bing_videos, google_videos, youtube, dailymotion, vimeo |
| news | bing_news, google_news, reuters, bbc, techcrunch |
| music | soundcloud, bandcamp, mixcloud |
| files | piratebay, nyaa |
| social_media | reddit, twitter, mastodon |
| science | arxiv, pubmed, semantic_scholar |
| it | github, gitlab, stackoverflow |

## Error Responses

### 400 Bad Request
Returned when parameters fail validation.
```json
{ "success": false, "errors": ["Invalid category \"xyz\""] }
```

### 404 Not Found
Returned when a search returns zero results, or an unknown endpoint is hit.
```json
{ "success": false, "error": "No results found.", "suggestions": [] }
```

### 503 Service Unavailable
Returned when all SearX instances fail or time out.
```json
{ "success": false, "error": "All search providers are currently unavailable.", "providers_attempted": 10 }
```

## Streaming

Streaming endpoints return `Content-Type: text/event-stream`. Each event is a JSON object on a `data:` line.

| Event type | When | Key fields |
|------------|------|------------|
| `meta` | First event | `total_count`, `answers`, `infobox`, `suggestions` |
| `result` | One per result | `index`, `data` (full result object) |
| `complete` | Last event | `total_sent` |