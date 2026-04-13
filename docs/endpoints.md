# Endpoints

## GET /

Returns full API documentation as JSON including all endpoints, parameters, and quick start examples.

---

## POST /search

Full search with a JSON request body.

**Request**
```json
{
  "query": "artificial intelligence",
  "categories": "general",
  "engines": "google,bing",
  "language": "en",
  "time_range": "week",
  "safesearch": 1,
  "pageno": 1,
  "per_page": 20
}
```

**Response**
```json
{
  "success": true,
  "query": "artificial intelligence",
  "params": { "categories": "general", "language": "en", "pageno": 1, "per_page": 20 },
  "meta": { "source_instance": "https://searx.be", "displayed": 20 },
  "answers": [],
  "infobox": { "title": "Artificial Intelligence", "content": "..." },
  "suggestions": ["machine learning", "deep learning"],
  "corrections": [],
  "results": {
    "all": [ { "type": "general", "url": "...", "title": "...", "content": "..." } ],
    "by_type": { "general": [ ... ] }
  },
  "pagination": { "current_page": 1, "next_page": 2, "has_next": true }
}
```

---

## GET /search/\<query\>

Search via URL path. All POST parameters are supported as query string arguments. Supports `stream=true`.

```
GET /search/mountains?categories=images&per_page=20
GET /search/news today?categories=news&time_range=day&language=en
GET /search/react?categories=it&engines=github,stackoverflow
GET /search/space?stream=true
```

---

## POST /search/stream

Same request body as `POST /search`. Returns `text/event-stream`.

```bash
curl -N -X POST /search/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "climate change", "categories": "news"}'
```

```
data: {"type":"meta","total_count":25,"suggestions":["global warming"]}
data: {"type":"result","index":0,"data":{"title":"...","url":"..."}}
data: {"type":"result","index":1,"data":{"title":"...","url":"..."}}
data: {"type":"complete","total_sent":25}
```

---

## GET /categories

Returns all supported categories with descriptions.

---

## GET /engines

Returns all engines grouped by category. Filter by category with `?category=images`.

---

## GET /languages

Returns all 30 supported language codes and their names.

---

## GET /health

Returns service status, supported features, and provider list.

---

## GET /stats

Returns cache hit/miss ratio, current cache size, and provider configuration.