![Cyron Logo](/static/assets/banner.png)

# Cyron Search API

A privacy-focused meta search engine API powered by SearX. Returns structured results across web, images, videos, news, music, files, social media, science, and IT — with full filtering support.

## Features

- Full meta search engine — not just images
- Nine result categories: general, images, videos, news, music, files, social_media, science, it
- Engine selection — target specific sources like YouTube, GitHub, ArXiv, PubMed, and more
- Language filtering across 30 languages
- Time range filtering: day, week, month, year
- Safe search levels: 0 (off), 1 (moderate), 2 (strict)
- Infobox extraction — Wikipedia-style knowledge panels
- Answer extraction — direct answers from search engines
- Suggestions and spelling corrections
- Flexible pagination (1–100 results per page)
- Streaming mode via Server-Sent Events
- LRU caching with 512 entry capacity
- Automatic failover across 11 SearX instances
- CORS enabled for web applications
- Zero tracking, zero ads

## Quick Start

```
GET /search/artificial intelligence?per_page=10
GET /search/mountains?categories=images&per_page=20
GET /search/tutorials?categories=videos
GET /search/technology?categories=news&time_range=day
GET /search/python?categories=general,science,it
```

## Endpoints

### GET `/`
Returns full API documentation.

### GET `/categories`
Lists all supported categories with descriptions.

**Response:**
```json
{
  "success": true,
  "categories": [
    { "name": "general", "description": "Web search results" },
    { "name": "images", "description": "Image search results with img_src and thumbnails" },
    { "name": "videos", "description": "Video results with iframe_src and duration" },
    { "name": "news", "description": "News articles with publishedDate" },
    { "name": "music", "description": "Music tracks with artist and album" },
    { "name": "files", "description": "File and torrent results with filesize, seed, leech" },
    { "name": "social_media", "description": "Social media posts and profiles" },
    { "name": "science", "description": "Academic papers with authors, journal, doi" },
    { "name": "it", "description": "IT resources, code, repositories" }
  ]
}
```

### GET `/engines`
Lists all engines, optionally filtered by category.

```
GET /engines
GET /engines?category=images
GET /engines?category=science
```

**Response:**
```json
{
  "success": true,
  "engines_by_category": {
    "general": ["google", "bing", "duckduckgo", "brave", "startpage", "qwant", "wikipedia"],
    "images": ["bing_images", "google_images", "flickr", "unsplash"],
    "videos": ["bing_videos", "google_videos", "youtube", "dailymotion", "vimeo"],
    "news": ["bing_news", "google_news", "reuters", "bbc", "techcrunch"],
    "science": ["arxiv", "pubmed", "semantic_scholar"],
    "it": ["github", "gitlab", "stackoverflow"]
  }
}
```

### GET `/languages`
Lists all 30 supported language codes.

### GET `/health`
API health status and configuration.

### GET `/stats`
Cache performance and provider statistics.

### POST `/search`
Main search endpoint with full parameter support.

**Request Body:**
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

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search term |
| `categories` | string or array | general | Comma-separated categories or JSON array |
| `engines` | string or array | auto | Specific engines to use |
| `language` | string | all | Language code (en, de, fr, etc.) |
| `time_range` | string | any | day, week, month, year |
| `safesearch` | integer | 1 | 0=off, 1=moderate, 2=strict |
| `pageno` | integer | 1 | Page number |
| `per_page` | integer | all | Results per page (1–100) |

**Success Response (200):**
```json
{
  "success": true,
  "query": "artificial intelligence",
  "params": {
    "categories": "general",
    "engines": "auto",
    "language": "en",
    "time_range": "week",
    "safesearch": 1,
    "pageno": 1,
    "per_page": 20
  },
  "meta": {
    "source_instance": "https://searx.be",
    "number_of_results": 45,
    "total_returned": 45,
    "displayed": 20
  },
  "answers": ["Direct answer text if available"],
  "infobox": {
    "title": "Artificial Intelligence",
    "content": "AI is the simulation of human intelligence...",
    "img_src": "https://example.com/ai.jpg",
    "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "attributes": {
      "Founded": "1956",
      "Key figures": "Alan Turing, John McCarthy"
    }
  },
  "suggestions": ["machine learning", "deep learning", "neural networks"],
  "corrections": [],
  "results": {
    "all": [
      {
        "url": "https://example.com/article",
        "title": "What is Artificial Intelligence?",
        "content": "A comprehensive overview of AI technologies...",
        "engines": ["google", "bing"],
        "score": 1.0,
        "category": "general",
        "type": "general",
        "publishedDate": "2024-01-15",
        "thumbnail": "https://example.com/thumb.jpg"
      }
    ],
    "by_type": {
      "general": [...],
      "news": [...]
    }
  },
  "pagination": {
    "current_page": 1,
    "per_page": 20,
    "total_on_page": 45,
    "returned": 20,
    "has_next": true,
    "next_page": 2
  }
}
```

### GET `/search/<query>`
Search via URL path with query parameters.

```
GET /search/mountains?categories=images&per_page=20
GET /search/news today?categories=news&time_range=day&language=en
GET /search/deep learning?categories=science&engines=arxiv
GET /search/javascript?categories=it&engines=github,stackoverflow
GET /search/sunset?categories=images,videos&safesearch=1
GET /search/anything?stream=true
```

All parameters from POST `/search` are supported as query string parameters.

| Parameter | Type | Default |
|-----------|------|---------|
| `categories` | string | general |
| `engines` | string | auto |
| `language` | string | all |
| `time_range` | string | any |
| `safesearch` | integer | 1 |
| `pageno` | integer | 1 |
| `per_page` | integer | all |
| `stream` | boolean | false |

### POST `/search/stream`
Streaming search that emits results progressively via Server-Sent Events.

Same request body as POST `/search`. Response is `text/event-stream` with events:

**Meta event** (first):
```json
{
  "type": "meta",
  "success": true,
  "query": "mountains",
  "answers": [],
  "infobox": null,
  "suggestions": ["hiking", "photography"],
  "corrections": [],
  "total_count": 30,
  "source": "https://searx.be"
}
```

**Result event** (per result):
```json
{
  "type": "result",
  "index": 0,
  "data": {
    "url": "...",
    "title": "...",
    "content": "...",
    "type": "general"
  }
}
```

**Complete event** (last):
```json
{
  "type": "complete",
  "total_sent": 30
}
```

## Result Fields by Category

### general / news
```json
{
  "url": "https://example.com",
  "title": "Page Title",
  "content": "Description or excerpt",
  "engines": ["google", "bing"],
  "score": 0.95,
  "category": "general",
  "type": "general",
  "publishedDate": "2024-01-15",
  "thumbnail": "https://example.com/thumb.jpg",
  "language": "en"
}
```

### images
```json
{
  "url": "https://example.com/page",
  "title": "Image Title",
  "img_src": "https://example.com/image.jpg",
  "thumbnail": "https://example.com/thumb.jpg",
  "type": "images"
}
```

### videos
```json
{
  "url": "https://youtube.com/watch?v=xxx",
  "title": "Video Title",
  "content": "Description",
  "iframe_src": "https://youtube.com/embed/xxx",
  "thumbnail": "https://example.com/thumb.jpg",
  "duration": "12:34",
  "publishedDate": "2024-01-15",
  "views": "1.2M",
  "type": "videos"
}
```

### science
```json
{
  "url": "https://arxiv.org/abs/2401.00000",
  "title": "Paper Title",
  "content": "Abstract text",
  "authors": "John Doe, Jane Smith",
  "journal": "Nature",
  "doi": "10.1038/xxxxx",
  "publishedDate": "2024-01-10",
  "type": "science"
}
```

### files
```json
{
  "url": "https://example.com/file",
  "title": "File Name",
  "content": "Description",
  "filesize": "1.2 GB",
  "seed": "142",
  "leech": "34",
  "type": "files"
}
```

### music
```json
{
  "url": "https://soundcloud.com/track",
  "title": "Track Title",
  "artist": "Artist Name",
  "album": "Album Name",
  "duration": "3:45",
  "type": "music"
}
```

## Usage Examples

### Browser
```
/search/space exploration?per_page=15
/search/machine learning?categories=general,science&language=en&per_page=25
/search/javascript?categories=it&engines=github,stackoverflow
/search/nature?categories=images&time_range=month&per_page=30
/search/AI news?categories=news&time_range=day&safesearch=1
```

### cURL
```bash
curl -X POST https://your-api.vercel.app/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quantum computing",
    "categories": "science",
    "engines": "arxiv,pubmed",
    "language": "en",
    "time_range": "year",
    "safesearch": 1,
    "per_page": 20
  }'

curl "https://your-api.vercel.app/search/sunset?categories=images&per_page=10"

curl -N "https://your-api.vercel.app/search/news?categories=news&time_range=day&stream=true"
```

### Python
```python
import requests

response = requests.post('https://your-api.vercel.app/search', json={
    'query': 'deep learning',
    'categories': ['science', 'it'],
    'language': 'en',
    'time_range': 'year',
    'per_page': 30
})

data = response.json()
if data['success']:
    for result in data['results']['all']:
        print(f"[{result['type']}] {result['title']}: {result['url']}")
    
    if data['infobox']:
        print(f"\nInfobox: {data['infobox']['title']}")
    
    if data['suggestions']:
        print(f"Suggestions: {', '.join(data['suggestions'])}")

response = requests.get(
    'https://your-api.vercel.app/search/neural networks',
    params={'categories': 'science', 'engines': 'arxiv', 'per_page': 10}
)
data = response.json()
```

```python
import requests
import json

def stream_search(query, categories='general'):
    url = 'https://your-api.vercel.app/search/stream'
    with requests.post(url, json={'query': query, 'categories': categories}, stream=True) as resp:
        for line in resp.iter_lines():
            if line and line.startswith(b'data: '):
                event = json.loads(line[6:])
                if event['type'] == 'result':
                    print(f"  {event['data']['title']}")
                elif event['type'] == 'meta':
                    print(f"Found ~{event['total_count']} results")
                elif event['type'] == 'complete':
                    print(f"Done: {event['total_sent']} results received")

stream_search('climate change', 'news')
```

### JavaScript
```javascript
const search = async (query, options = {}) => {
  const resp = await fetch('https://your-api.vercel.app/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, per_page: 20, ...options })
  });
  return resp.json();
};

const results = await search('artificial intelligence', {
  categories: 'general',
  language: 'en',
  time_range: 'week'
});

const imageResults = await search('mountains', { categories: 'images' });
imageResults.results.all.forEach(img => {
  const el = document.createElement('img');
  el.src = img.img_src || img.thumbnail;
  document.body.appendChild(el);
});

const streamSearch = (query, onResult, onMeta) => {
  const evtSource = new EventSource(
    `https://your-api.vercel.app/search/${encodeURIComponent(query)}?stream=true`
  );
  evtSource.onmessage = (e) => {
    const event = JSON.parse(e.data);
    if (event.type === 'meta') onMeta(event);
    if (event.type === 'result') onResult(event.data);
    if (event.type === 'complete') evtSource.close();
  };
};

streamSearch(
  'space exploration',
  (result) => console.log(result.title),
  (meta) => console.log(`About ${meta.total_count} results`)
);
```

### React
```jsx
import { useState, useEffect } from 'react';

function SearchEngine() {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('general');
  const [results, setResults] = useState([]);
  const [infobox, setInfobox] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);

  const search = async (p = 1) => {
    setLoading(true);
    const resp = await fetch('https://your-api.vercel.app/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, categories: category, pageno: p, per_page: 20 })
    });
    const data = await resp.json();
    if (data.success) {
      setResults(data.results.all);
      setInfobox(data.infobox);
      setSuggestions(data.suggestions);
      setPage(p);
    }
    setLoading(false);
  };

  return (
    <div>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <select value={category} onChange={e => setCategory(e.target.value)}>
        {['general','images','videos','news','science','it','music','files','social_media'].map(c => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
      <button onClick={() => search(1)}>Search</button>

      {infobox && (
        <div className="infobox">
          <h2>{infobox.title}</h2>
          <p>{infobox.content}</p>
        </div>
      )}

      {suggestions.length > 0 && (
        <div>Also try: {suggestions.map(s => (
          <button key={s} onClick={() => { setQuery(s); search(1); }}>{s}</button>
        ))}</div>
      )}

      {loading ? <div>Searching...</div> : results.map((r, i) => (
        <div key={i}>
          {r.type === 'images' && <img src={r.img_src} alt={r.title} />}
          {r.type === 'videos' && <iframe src={r.iframe_src} title={r.title} />}
          <a href={r.url}>{r.title}</a>
          <p>{r.content}</p>
          {r.publishedDate && <small>{r.publishedDate}</small>}
          {r.authors && <small>by {r.authors}</small>}
        </div>
      ))}

      <button onClick={() => search(page - 1)} disabled={page === 1}>Previous</button>
      <button onClick={() => search(page + 1)}>Next</button>
    </div>
  );
}
```

## Batch Multi-Category Collection

```python
import requests

def collect_all_categories(query, per_page=10):
    categories = ['general', 'news', 'images', 'videos', 'science']
    all_results = {}
    
    for cat in categories:
        resp = requests.post('https://your-api.vercel.app/search', json={
            'query': query,
            'categories': cat,
            'per_page': per_page
        })
        data = resp.json()
        if data['success']:
            all_results[cat] = data['results']['all']
    
    return all_results

results = collect_all_categories('quantum computing')
for cat, items in results.items():
    print(f"\n{cat}: {len(items)} results")
    for item in items[:3]:
        print(f"  - {item['title']}")
```

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "errors": [
    "Invalid category \"xyz\". Valid: general, images, videos, news, music, files, social_media, science, it",
    "Invalid time_range \"yesterday\". Valid: day, week, month, year"
  ]
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "No results found for this query.",
  "query": "xyzabc123",
  "suggestions": [],
  "corrections": []
}
```

### 503 Service Unavailable
```json
{
  "success": false,
  "error": "All search providers are currently unavailable.",
  "providers_attempted": 11
}
```

## Deployment

### Vercel

1. Clone the repository
2. `npm i -g vercel`
3. `vercel`

`vercel.json`:
```json
{
  "builds": [{ "src": "app.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "app.py" }]
}
```

### Local Development

```bash
git clone https://github.com/yourusername/cyron.git
cd cyron
pip install -r requirements.txt
python app.py
```

API available at `http://localhost:5000`.

## Configuration

### SearX Instances

Modify `SEARX_INSTANCES` in `app.py`:
```python
SEARX_INSTANCES = [
    "https://searx.be",
    "https://your-instance.example.com",
]
```

### Cache Size

Modify the decorator:
```python
@lru_cache(maxsize=512)
def execute_search(...):
```

### CORS Restriction

```python
CORS(app, origins=["https://yourdomain.com"])
```

### Rate Limiting (Production)

```bash
pip install flask-limiter
```

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

@app.route('/search', methods=['POST'])
@limiter.limit("10 per minute")
def search_post():
    ...
```

## Requirements

- Python 3.7+
- Flask
- flask-cors
- requests
- beautifulsoup4

## File Structure

```
cyron/
├── app.py
├── requirements.txt
├── vercel.json
└── README.md
```

## Privacy

No user data is stored. No cookies. No tracking. Requests are distributed across SearX instances that themselves do not log queries.

## Support

- `GET /` — Full API documentation
- `GET /examples` — Query examples for every category
- `GET /health` — Status check
- `GET /stats` — Cache and performance metrics
- `GET /categories` — Category reference
- `GET /engines` — Engine reference
- `GET /languages` — Language codes