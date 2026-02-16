![Cyron Logo](/static/assets/banner.png)

# Cyron Image Search API

A privacy-focused image search API powered by SearX instances. Search for images without tracking or ads.

## Features

- Privacy-focused - No tracking or data collection
- Fast image search across multiple SearX instances
- Advanced filtering (size, time range, safe search)
- **Flexible pagination - Control images per page (1-100)**
- Built-in caching for improved performance
- Automatic failover across multiple search providers
- Optional image proxy support
- CORS enabled for web applications
- User-friendly GET and POST endpoints
- Comprehensive error handling with helpful messages

## Quick Start

### Browser-Friendly GET Requests

Simply visit these URLs in your browser:
```
https://your-api.vercel.app/search/mountains
https://your-api.vercel.app/search/mountains?per_page=20
https://your-api.vercel.app/search/sunset?size=large&per_page=15
https://your-api.vercel.app/search/ocean waves?time_range=week&page=2&per_page=30
```

### POST Requests with JSON

For more control, use POST requests with JSON:
```bash
curl -X POST https://your-api.vercel.app/search \
  -H "Content-Type: application/json" \
  -d '{"query": "mountains", "size": "large", "per_page": 25}'
```

## API Endpoints

### GET `/`
Returns complete API documentation, available endpoints, and quick start examples.

**Example:**
```
https://your-api.vercel.app/
```

**Response:**
```json
{
  "name": "Image Search API",
  "version": "2.0",
  "description": "Privacy-focused image search API with flexible pagination",
  "endpoints": { ... },
  "quick_start": { ... },
  "features": [ ... ]
}
```

### GET `/examples`
Returns comprehensive example queries organized by category with both GET and POST formats.

**Example:**
```
https://your-api.vercel.app/examples
```

**Response:**
```json
{
  "success": true,
  "examples": [
    {
      "category": "Pagination Examples",
      "queries": [
        {
          "name": "Page 1 - 15 images",
          "url": "/search/nature?page=1&per_page=15",
          "post_body": {"query": "nature", "page": 1, "per_page": 15}
        }
      ]
    }
  ],
  "tips": [ ... ]
}
```

### GET `/health`
Check API health status and configuration.

**Example:**
```
https://your-api.vercel.app/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Image Search API",
  "version": "2.0",
  "timestamp": "2024-02-16T10:30:00Z",
  "providers": {
    "total": 11,
    "status": "operational"
  },
  "features": {
    "cache_enabled": true,
    "cors_enabled": true,
    "safe_search": true,
    "proxy_mode": true,
    "flexible_pagination": true
  }
}
```

### GET `/stats`
View cache performance statistics and provider information.

**Example:**
```
https://your-api.vercel.app/stats
```

**Response:**
```json
{
  "success": true,
  "cache": {
    "hits": 145,
    "misses": 23,
    "hit_rate": "86.31%",
    "current_size": 23,
    "max_size": 256,
    "efficiency": "high"
  },
  "providers": {
    "total_instances": 11,
    "instances": [ ... ],
    "rotation": "random",
    "failover": "automatic"
  }
}
```

### POST `/search`
Search for images using JSON request body.

**Request Body:**
```json
{
  "query": "mountains",
  "safe_search": true,
  "size": "large",
  "time_range": "week",
  "page": 1,
  "per_page": 20,
  "proxy_mode": false
}
```

**Parameters:**
- `query` (required, string): Search query
- `safe_search` (optional, boolean): Enable safe search filtering (default: true)
- `size` (optional, string): Filter by image size - `any`, `large`, `medium`, `small` (default: any)
- `time_range` (optional, string): Filter by time - `any`, `day`, `week`, `month`, `year` (default: any)
- `page` (optional, integer): Page number for pagination (default: 1)
- `per_page` (optional, integer): Images per page, 1-100 (default: all available images)
- `proxy_mode` (optional, boolean): Use proxy URLs for images (default: false)

**Success Response (200):**
```json
{
  "success": true,
  "query": "mountains",
  "filters": {
    "size": "large",
    "time_range": "week",
    "safe_search": true,
    "page": 1,
    "per_page": 20,
    "proxy_mode": false
  },
  "results": {
    "count": 20,
    "images": [
      {
        "img_src": "https://example.com/image.jpg",
        "display_src": "https://example.com/image.jpg",
        "url": "https://example.com/page",
        "title": "Mountain Landscape"
      }
    ]
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
Search for images using URL path (user-friendly, browser-accessible).

**Examples:**
```
https://your-api.vercel.app/search/cats
https://your-api.vercel.app/search/cats?per_page=10
https://your-api.vercel.app/search/mountain landscape?page=2&per_page=25
https://your-api.vercel.app/search/sunset?size=large&per_page=15
https://your-api.vercel.app/search/ocean?size=large&time_range=week&page=3&per_page=30
```

**Query Parameters:**
- `safe_search` (optional): `true` or `false` (default: true)
- `size` (optional): `any`, `large`, `medium`, `small` (default: any)
- `time_range` (optional): `any`, `day`, `week`, `month`, `year` (default: any)
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Images per page, 1-100 (default: all available)
- `proxy_mode` (optional): `true` or `false` (default: false)
- `stream` (optional): `true` or `false` (default: false)

**Success Response (200):**
Same format as POST `/search` endpoint.

**Error Responses:**
- `400` - Invalid parameters or missing query
- `404` - No images found for query
- `503` - All search providers unavailable

## Pagination Guide

### Understanding Pagination

The API supports flexible pagination allowing you to control how many images you get per page:

- **Default behavior**: Returns all available images from the current page
- **With `per_page`**: Returns only the specified number of images (1-100)
- **Multiple pages**: Use `page` parameter to navigate through pages

### Pagination Examples

#### Get All Images (Default)
```bash
curl "https://your-api.vercel.app/search/nature"
```

Returns all available images from page 1.

#### Get Specific Number Per Page
```bash
curl "https://your-api.vercel.app/search/nature?per_page=20"
```

Returns exactly 20 images from page 1.

#### Navigate Pages with Fixed Size
```bash
curl "https://your-api.vercel.app/search/nature?page=1&per_page=15"
curl "https://your-api.vercel.app/search/nature?page=2&per_page=15"
curl "https://your-api.vercel.app/search/nature?page=3&per_page=15"
```

Gets 15 images from each page sequentially.

### Frontend Pagination Implementation

#### JavaScript Example - Dynamic Page Size
```javascript
class ImageGallery {
  constructor(apiUrl, query) {
    this.apiUrl = apiUrl;
    this.query = query;
    this.currentPage = 1;
    this.perPage = 20;
  }

  async loadPage(page = this.currentPage) {
    const response = await fetch(
      `${this.apiUrl}/search/${this.query}?page=${page}&per_page=${this.perPage}`
    );
    const data = await response.json();
    
    if (data.success) {
      this.displayImages(data.results.images);
      this.updatePagination(data.pagination);
    }
  }

  changePageSize(newSize) {
    this.perPage = newSize;
    this.currentPage = 1;
    this.loadPage();
  }

  nextPage() {
    this.currentPage++;
    this.loadPage();
  }

  prevPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadPage();
    }
  }

  displayImages(images) {
    const gallery = document.getElementById('gallery');
    gallery.innerHTML = '';
    
    images.forEach(img => {
      const imgElement = document.createElement('img');
      imgElement.src = img.display_src;
      imgElement.alt = img.title;
      gallery.appendChild(imgElement);
    });
  }

  updatePagination(pagination) {
    document.getElementById('page-info').textContent = 
      `Page ${pagination.current_page} - Showing ${pagination.returned} images`;
  }
}

const gallery = new ImageGallery('https://your-api.vercel.app', 'nature');
gallery.loadPage();

document.getElementById('page-size-10').addEventListener('click', () => {
  gallery.changePageSize(10);
});

document.getElementById('page-size-25').addEventListener('click', () => {
  gallery.changePageSize(25);
});

document.getElementById('page-size-50').addEventListener('click', () => {
  gallery.changePageSize(50);
});

document.getElementById('next-btn').addEventListener('click', () => {
  gallery.nextPage();
});

document.getElementById('prev-btn').addEventListener('click', () => {
  gallery.prevPage();
});
```

#### React Example - Paginated Gallery
```jsx
import React, { useState, useEffect } from 'react';

function ImageGallery() {
  const [images, setImages] = useState([]);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState(null);

  useEffect(() => {
    loadImages();
  }, [page, perPage]);

  const loadImages = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `https://your-api.vercel.app/search/nature?page=${page}&per_page=${perPage}`
      );
      const data = await response.json();
      
      if (data.success) {
        setImages(data.results.images);
        setPagination(data.pagination);
      }
    } catch (error) {
      console.error('Error loading images:', error);
    }
    setLoading(false);
  };

  return (
    <div>
      <div className="controls">
        <select 
          value={perPage} 
          onChange={(e) => {
            setPerPage(Number(e.target.value));
            setPage(1);
          }}
        >
          <option value={10}>10 per page</option>
          <option value={20}>20 per page</option>
          <option value={30}>30 per page</option>
          <option value={50}>50 per page</option>
        </select>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="gallery">
          {images.map((img, index) => (
            <img key={index} src={img.display_src} alt={img.title} />
          ))}
        </div>
      )}

      <div className="pagination">
        <button 
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
        >
          Previous
        </button>
        
        <span>
          Page {pagination?.current_page} - 
          Showing {pagination?.returned} of {pagination?.total_on_page} images
        </span>
        
        <button 
          onClick={() => setPage(p => p + 1)}
          disabled={!pagination?.has_next}
        >
          Next
        </button>
      </div>
    </div>
  );
}

export default ImageGallery;
```

#### Python Example - Batch Processing
```python
import requests

def fetch_all_pages(query, per_page=25, max_pages=10):
    all_images = []
    api_url = 'https://your-api.vercel.app'
    
    for page in range(1, max_pages + 1):
        response = requests.get(
            f'{api_url}/search/{query}',
            params={'page': page, 'per_page': per_page}
        )
        
        data = response.json()
        
        if data['success']:
            images = data['results']['images']
            all_images.extend(images)
            print(f"Page {page}: Got {len(images)} images")
            
            if not data['pagination']['has_next']:
                break
        else:
            print(f"No more images at page {page}")
            break
    
    return all_images

images = fetch_all_pages('landscape', per_page=20, max_pages=5)
print(f"Total images collected: {len(images)}")
```

### POST Request Pagination

```bash
curl -X POST https://your-api.vercel.app/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sunset over mountains",
    "size": "large",
    "page": 1,
    "per_page": 30
  }'
```

```python
import requests

response = requests.post('https://your-api.vercel.app/search', json={
    'query': 'forest landscape',
    'size': 'large',
    'page': 1,
    'per_page': 25
})

data = response.json()
if data['success']:
    print(f"Got {data['results']['count']} images")
    print(f"Page {data['pagination']['current_page']}")
```

## Usage Examples

### Browser (GET)

Simply paste these URLs in your browser:
```
https://your-api.vercel.app/search/puppies?per_page=15
https://your-api.vercel.app/search/nature wallpaper?size=large&per_page=20
https://your-api.vercel.app/search/tech news?time_range=day&per_page=10
```

### cURL (POST)
```bash
curl -X POST https://your-api.vercel.app/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sunset over mountains",
    "size": "large",
    "time_range": "month",
    "safe_search": true,
    "page": 1,
    "per_page": 25
  }'
```

### cURL (GET)
```bash
curl "https://your-api.vercel.app/search/ocean?size=large&per_page=20"
```

### Python (requests)
```python
import requests

response = requests.post('https://your-api.vercel.app/search', json={
    'query': 'forest landscape',
    'size': 'large',
    'time_range': 'week',
    'safe_search': True,
    'page': 1,
    'per_page': 30
})

data = response.json()
if data['success']:
    for image in data['results']['images']:
        print(f"{image['title']}: {image['img_src']}")

response = requests.get('https://your-api.vercel.app/search/cats?size=medium&per_page=15')
data = response.json()
```

### JavaScript (Fetch API)
```javascript
fetch('https://your-api.vercel.app/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'northern lights',
    size: 'large',
    time_range: 'month',
    safe_search: true,
    per_page: 20
  })
})
.then(res => res.json())
.then(data => {
  if (data.success) {
    data.results.images.forEach(img => {
      console.log(img.title, img.img_src);
    });
  }
});

fetch('https://your-api.vercel.app/search/mountains?size=large&per_page=25')
  .then(res => res.json())
  .then(data => console.log(data));
```

### JavaScript (Axios)
```javascript
const axios = require('axios');

axios.post('https://your-api.vercel.app/search', {
  query: 'beach sunset',
  size: 'large',
  time_range: 'week',
  safe_search: true,
  per_page: 30
})
.then(response => {
  if (response.data.success) {
    console.log(response.data.results.images);
  }
});

axios.get('https://your-api.vercel.app/search/ocean?size=large&per_page=15')
  .then(response => console.log(response.data));
```

### PHP
```php
<?php
$data = array(
    'query' => 'mountain peaks',
    'size' => 'large',
    'safe_search' => true,
    'page' => 1,
    'per_page' => 20
);

$options = array(
    'http' => array(
        'header'  => "Content-type: application/json\r\n",
        'method'  => 'POST',
        'content' => json_encode($data)
    )
);

$context  = stream_context_create($options);
$result = file_get_contents('https://your-api.vercel.app/search', false, $context);
$response = json_decode($result);

if ($response->success) {
    foreach ($response->results->images as $image) {
        echo $image->title . ": " . $image->img_src . "\n";
    }
}

$result = file_get_contents('https://your-api.vercel.app/search/cats?size=medium&per_page=15');
$response = json_decode($result);
?>
```

## Advanced Usage

### Multi-Page Collection

Collect images across multiple pages:
```python
import requests

query = "landscape photography"
all_images = []
per_page = 20

for page in range(1, 6):
    response = requests.post('https://your-api.vercel.app/search', json={
        'query': query,
        'size': 'large',
        'page': page,
        'per_page': per_page
    })
    
    data = response.json()
    if data['success']:
        all_images.extend(data['results']['images'])
        print(f"Page {page}: {data['results']['count']} images")
    else:
        break

print(f"Total images collected: {len(all_images)}")
```

### Dynamic Page Size Selection

Allow users to choose their preferred page size:
```javascript
const pageSizes = [10, 20, 30, 50, 100];

async function loadImagesWithSize(query, pageSize) {
  const response = await fetch(
    `https://your-api.vercel.app/search/${query}?per_page=${pageSize}`
  );
  const data = await response.json();
  
  if (data.success) {
    console.log(`Loaded ${data.results.count} images with page size ${pageSize}`);
    return data.results.images;
  }
}

loadImagesWithSize('nature', 25);
```

### Using Proxy Mode

Enable proxy mode to route images through a proxy server:
```bash
curl -X POST https://your-api.vercel.app/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artwork",
    "proxy_mode": true,
    "per_page": 20
  }'
```

### Filtering by Time Range

Get only recent images:
```javascript
fetch('https://your-api.vercel.app/search/tech news?time_range=day&per_page=15')
  .then(res => res.json())
  .then(data => {
    console.log(`Got ${data.results.count} images from last 24 hours`);
  });
```

### Combining All Features
```bash
curl "https://your-api.vercel.app/search/wallpaper?size=large&time_range=week&safe_search=true&page=2&per_page=25"
```

## Deployment

### Deploy to Vercel

1. Clone this repository
2. Install Vercel CLI: `npm i -g vercel`
3. Run `vercel` in the project directory
4. Follow the prompts

Or click the button below:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/yourrepo)

### Deploy to Heroku

1. Create a new Heroku app
2. Connect your GitHub repository
3. Deploy from the main branch

### Deploy to Railway

1. Create a new project on Railway
2. Connect your GitHub repository
3. Railway will automatically detect and deploy your Flask app

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the Flask app:
```bash
python app.py
```

4. The API will be available at `http://localhost:5000`

5. Test the API:
```bash
curl http://localhost:5000/
curl http://localhost:5000/search/cats?size=large&per_page=10
```

## Configuration

### SearX Instances

The API uses multiple SearX instances for redundancy and reliability. You can modify the `SEARX_INSTANCES` list in `app.py` to add or remove instances:
```python
SEARX_INSTANCES = [
    "https://searx.be",
    "https://search.disroot.org",
    "https://searx.work",
]
```

### Cache Settings

Results are cached using `lru_cache` with a maximum size of 256 entries. To adjust the cache size, modify the decorator in `app.py`:
```python
@lru_cache(maxsize=256)
def search_images_cached(query, is_safe, size, time_range, page):
```

### CORS Configuration

CORS is enabled by default for all origins. To restrict access, modify the CORS initialization in `app.py`:
```python
from flask_cors import CORS

CORS(app)

CORS(app, origins=["https://yourdomain.com", "https://anotherdomain.com"])
```

### Pagination Limits

The default pagination limit is 100 images per page. To change this, modify the validation in `app.py`:
```python
if per_page < 1 or per_page > 100:
```

Change `100` to your desired maximum.

## Error Handling

The API provides detailed error messages to help troubleshoot issues:

### 400 Bad Request
```json
{
  "success": false,
  "error": "per_page must be between 1 and 100",
  "provided": 150
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "No images found for this query.",
  "suggestion": "Try different keywords, remove filters, or check a different page.",
  "query": "your-query",
  "filters": { ... }
}
```

### 503 Service Unavailable
```json
{
  "success": false,
  "error": "Could not fetch results. All search providers are currently unavailable.",
  "suggestion": "Please try again in a few moments.",
  "providers_attempted": 11
}
```

## Performance

### Caching

The API implements intelligent caching to improve performance:

- Results are cached based on query parameters (including page number)
- Cache hit rate typically exceeds 80% for popular queries
- View cache statistics at `/stats` endpoint
- Cache automatically expires after service restart

### Provider Rotation

- Requests are distributed randomly across all SearX instances
- Automatic failover to next provider if one fails
- Timeout set to 15 seconds per provider
- Continues trying until all providers are exhausted

## Requirements

- Python 3.7+
- Flask
- flask-cors
- requests

See `requirements.txt` for specific versions.

## File Structure
```
your-repo/
├── app.py                 
├── requirements.txt       
├── vercel.json           
└── README.md             
```

## Privacy and Security

### Privacy Features

- No user data is stored or logged
- No cookies or tracking mechanisms
- Searches are distributed across multiple SearX instances
- No analytics or user profiling
- Cache headers prevent browser caching of results

### Security Recommendations

For production use, consider implementing:

**Rate Limiting**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)
```

**API Key Authentication**
```python
@app.before_request
def check_api_key():
    api_key = request.headers.get('X-API-Key')
    if api_key != os.environ.get('API_KEY'):
        return jsonify({'error': 'Invalid API key'}), 401
```

**HTTPS Only**
Always use HTTPS in production to encrypt data in transit.

## Rate Limiting

Currently, no rate limiting is implemented. For production deployment, we recommend adding rate limiting to prevent abuse:
```bash
pip install flask-limiter
```

Then add to your `app.py`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/search', methods=['POST'])
@limiter.limit("10 per minute")
def search_for_images():
```

## Troubleshooting

### No Results Returned

- Check if your query is too specific
- Try removing filters (size, time_range)
- Verify SearX instances are accessible
- Check `/health` endpoint for API status

### Slow Response Times

- Results may be cached on subsequent requests
- Some SearX instances may be slower than others
- Check `/stats` for cache hit rate
- Consider increasing cache size

### 503 Errors

- All SearX providers may be temporarily down
- Check individual instance status
- Try again after a few minutes
- Consider adding more instances to the list

### Pagination Not Working

- Ensure `per_page` is between 1-100
- Verify `page` is a positive integer
- Check if the page number exceeds available pages

## Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Add tests for new features
- Update documentation for API changes
- Ensure backwards compatibility

## Acknowledgments

- Powered by SearX - Privacy-respecting metasearch engine
- Built with Flask - Lightweight WSGI web application framework
- Deployed on Vercel - Cloud platform for static sites and serverless functions

## Support

- Visit `/` endpoint for API documentation
- Visit `/examples` for query examples
- Check `/health` for API status
- View `/stats` for performance metrics

For issues and feature requests, please open an issue on GitHub.