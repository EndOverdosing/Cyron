import requests
import random
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from functools import lru_cache
from datetime import datetime

app = Flask(__name__)
CORS(app)

SEARX_INSTANCES = [
    "https://searx.be",
    "https://search.disroot.org",
    "https://searx.work",
    "https://search.projectsegfau.lt",
    "https://searx.prvcy.eu",
    "https://searx.thegpm.org",
    "https://searx.tiekoetter.com",
    "https://search.ononoki.org",
    "https://searx.si",
    "https://searx.garudalinux.org",
    "https://metasearx.com"
]

@lru_cache(maxsize=256)
def search_images_cached(query, is_safe, size, time_range, page):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    final_query = query
    if ' ' in query and not (query.startswith('"') and query.endswith('"')):
        final_query = f'"{query}"'

    params = {
        'q': final_query,
        'categories': 'images',
        'format': 'json',
        'safesearch': '0' if not is_safe else '1',
        'pageno': page
    }
    if size != 'any':
        params['img_size'] = size
    if time_range != 'any':
        params['time_range'] = time_range

    shuffled_instances = random.sample(SEARX_INSTANCES, len(SEARX_INSTANCES))
    
    for instance in shuffled_instances:
        try:
            search_url = f"{instance}/search"
            if "metasearx.com" in instance or "searx.be" in instance:
                search_url = instance
            
            response = requests.get(search_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'results' in data and data['results']:
                image_results = []
                for result in data['results']:
                    if 'img_src' in result and result['img_src']:
                        image_info = {
                            "img_src": result['img_src'],
                            "url": result.get('url', '#'),
                            "title": result.get('title', 'Untitled')
                        }
                        image_results.append(image_info)
                if image_results:
                    return image_results
        except requests.exceptions.RequestException:
            continue
            
    return None

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'name': 'Image Search API',
        'version': '1.0',
        'description': 'Privacy-focused image search API powered by SearX instances. No tracking, no ads, just results.',
        'documentation': 'https://github.com/yourusername/yourrepo',
        'endpoints': {
            '/': {
                'method': 'GET',
                'description': 'API information and documentation'
            },
            '/search': {
                'method': 'POST',
                'description': 'Search for images using JSON body',
                'content_type': 'application/json',
                'body_example': {
                    'query': 'mountains',
                    'safe_search': True,
                    'size': 'large',
                    'time_range': 'week',
                    'page': 1,
                    'proxy_mode': False
                }
            },
            '/search/<query>': {
                'method': 'GET',
                'description': 'Search for images using URL path (user-friendly)',
                'example': '/search/mountains?size=large&safe_search=true',
                'parameters': {
                    'query': 'Search term (in URL path)',
                    'safe_search': 'true/false (default: true)',
                    'size': 'any/large/medium/small (default: any)',
                    'time_range': 'any/day/week/month/year (default: any)',
                    'page': 'number (default: 1)',
                    'proxy_mode': 'true/false (default: false)'
                }
            },
            '/examples': {
                'method': 'GET',
                'description': 'Get example search queries with different filters'
            },
            '/health': {
                'method': 'GET',
                'description': 'API health check and status'
            },
            '/stats': {
                'method': 'GET',
                'description': 'View cache statistics and provider info'
            }
        },
        'quick_start': {
            'browser': 'Visit: /search/your-query',
            'curl': 'curl -X POST /search -H "Content-Type: application/json" -d \'{"query": "cats"}\'',
            'python': 'requests.post(API_URL + "/search", json={"query": "cats"})',
            'javascript': 'fetch(API_URL + "/search", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({query: "cats"})})'
        },
        'features': [
            'Privacy-focused (no tracking)',
            'Multiple SearX instances for reliability',
            'Built-in caching for performance',
            'CORS enabled for web apps',
            'Safe search filtering',
            'Image size filtering',
            'Time range filtering',
            'Pagination support',
            'Optional image proxy'
        ]
    })

@app.route('/examples', methods=['GET'])
def get_examples():
    return jsonify({
        'success': True,
        'message': 'Here are some example searches you can try. Use these as templates for your own queries.',
        'examples': [
            {
                'category': 'Basic Searches',
                'description': 'Simple queries to get started',
                'queries': [
                    {
                        'name': 'Simple search',
                        'url': '/search/sunset',
                        'post_body': {'query': 'sunset'}
                    },
                    {
                        'name': 'Multi-word search',
                        'url': '/search/cute puppies',
                        'post_body': {'query': 'cute puppies', 'safe_search': True}
                    },
                    {
                        'name': 'Specific topic',
                        'url': '/search/mountain landscape',
                        'post_body': {'query': 'mountain landscape'}
                    }
                ]
            },
            {
                'category': 'Size Filtered',
                'description': 'Find images by specific sizes',
                'queries': [
                    {
                        'name': 'Large wallpapers',
                        'url': '/search/nature wallpaper?size=large',
                        'post_body': {'query': 'nature wallpaper', 'size': 'large'}
                    },
                    {
                        'name': 'Medium photos',
                        'url': '/search/food photography?size=medium',
                        'post_body': {'query': 'food photography', 'size': 'medium'}
                    },
                    {
                        'name': 'Small icons',
                        'url': '/search/app icons?size=small',
                        'post_body': {'query': 'app icons', 'size': 'small'}
                    }
                ]
            },
            {
                'category': 'Time Filtered',
                'description': 'Find recent images',
                'queries': [
                    {
                        'name': 'Today only',
                        'url': '/search/tech news?time_range=day',
                        'post_body': {'query': 'tech news', 'time_range': 'day'}
                    },
                    {
                        'name': 'This week',
                        'url': '/search/fashion trends?time_range=week',
                        'post_body': {'query': 'fashion trends', 'time_range': 'week'}
                    },
                    {
                        'name': 'This month',
                        'url': '/search/new cars?time_range=month',
                        'post_body': {'query': 'new cars', 'time_range': 'month'}
                    }
                ]
            },
            {
                'category': 'Advanced Combinations',
                'description': 'Combine multiple filters for precise results',
                'queries': [
                    {
                        'name': 'Large recent landscapes',
                        'url': '/search/landscape photography?size=large&time_range=week&safe_search=true',
                        'post_body': {'query': 'landscape photography', 'size': 'large', 'time_range': 'week', 'safe_search': True}
                    },
                    {
                        'name': 'Medium vintage images',
                        'url': '/search/vintage cars?size=medium&page=1',
                        'post_body': {'query': 'vintage cars', 'size': 'medium', 'page': 1}
                    },
                    {
                        'name': 'Large wallpapers from this month',
                        'url': '/search/4k wallpaper?size=large&time_range=month&proxy_mode=false',
                        'post_body': {'query': '4k wallpaper', 'size': 'large', 'time_range': 'month', 'proxy_mode': False}
                    }
                ]
            },
            {
                'category': 'Pagination',
                'description': 'Get more results with page numbers',
                'queries': [
                    {
                        'name': 'First page',
                        'url': '/search/ocean?page=1',
                        'post_body': {'query': 'ocean', 'page': 1}
                    },
                    {
                        'name': 'Second page',
                        'url': '/search/ocean?page=2',
                        'post_body': {'query': 'ocean', 'page': 2}
                    },
                    {
                        'name': 'Third page',
                        'url': '/search/ocean?page=3',
                        'post_body': {'query': 'ocean', 'page': 3}
                    }
                ]
            }
        ],
        'tips': [
            'Use specific keywords for better results',
            'Combine size and time filters for precise searches',
            'Enable safe_search for family-friendly content',
            'Use pagination to browse through more results',
            'Try different query variations if results are limited'
        ]
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Image Search API',
        'version': '1.0',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'providers': {
            'total': len(SEARX_INSTANCES),
            'status': 'operational'
        },
        'features': {
            'cache_enabled': True,
            'cors_enabled': True,
            'safe_search': True,
            'proxy_mode': True
        }
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    cache_info = search_images_cached.cache_info()
    hit_rate = (cache_info.hits / (cache_info.hits + cache_info.misses) * 100) if (cache_info.hits + cache_info.misses) > 0 else 0
    
    return jsonify({
        'success': True,
        'cache': {
            'hits': cache_info.hits,
            'misses': cache_info.misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'current_size': cache_info.currsize,
            'max_size': cache_info.maxsize,
            'efficiency': 'high' if hit_rate > 50 else 'medium' if hit_rate > 25 else 'low'
        },
        'providers': {
            'total_instances': len(SEARX_INSTANCES),
            'instances': SEARX_INSTANCES,
            'rotation': 'random',
            'failover': 'automatic'
        },
        'api_info': {
            'version': '1.0',
            'uptime': 'check /health for status',
            'cors': 'enabled',
            'rate_limiting': 'none (consider adding for production)'
        }
    })

@app.route('/search', methods=['POST'])
def search_for_images():
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False, 
            'error': 'Invalid JSON body. Please send a valid JSON object with a "query" field.',
            'example': {'query': 'mountains', 'safe_search': True, 'size': 'large'}
        }), 400
    
    query = data.get('query')
    is_safe = data.get('safe_search', True)
    size = data.get('size', 'any')
    time_range = data.get('time_range', 'any')
    page = int(data.get('page', 1))
    proxy_mode = data.get('proxy_mode', False)

    if not query:
        return jsonify({
            'success': False, 
            'error': 'Search query cannot be empty. Please provide a "query" field in your request.',
            'example': {'query': 'your search term here'}
        }), 400

    if size not in ['any', 'large', 'medium', 'small']:
        return jsonify({
            'success': False,
            'error': f'Invalid size parameter: "{size}". Valid options: any, large, medium, small',
            'provided': size,
            'valid_options': ['any', 'large', 'medium', 'small']
        }), 400

    if time_range not in ['any', 'day', 'week', 'month', 'year']:
        return jsonify({
            'success': False,
            'error': f'Invalid time_range parameter: "{time_range}". Valid options: any, day, week, month, year',
            'provided': time_range,
            'valid_options': ['any', 'day', 'week', 'month', 'year']
        }), 400

    image_results = search_images_cached(query, is_safe, size, time_range, page)
    
    if image_results is None:
        json_response = jsonify({
            'success': False, 
            'error': 'Could not fetch results. All search providers are currently unavailable.',
            'suggestion': 'Please try again in a few moments. Our system rotates through multiple providers automatically.',
            'query': query,
            'providers_attempted': len(SEARX_INSTANCES)
        })
        response = make_response(json_response, 503)
    elif not image_results:
        json_response = jsonify({
            'success': False, 
            'error': 'No images found for this query.',
            'suggestion': 'Try different keywords, remove filters, or check a different page.',
            'query': query,
            'filters': {
                'size': size,
                'time_range': time_range,
                'safe_search': is_safe,
                'page': page
            }
        })
        response = make_response(json_response, 404)
    else:
        for item in image_results:
            if proxy_mode:
                img_src = item['img_src']
                if img_src.startswith('//'):
                    img_src = f"https:{img_src}"
                item['display_src'] = f"https://ovala.vercel.app/proxy/{img_src}"
            else:
                item['display_src'] = item['img_src']

        json_response = jsonify({
            'success': True,
            'query': query,
            'filters': {
                'size': size,
                'time_range': time_range,
                'safe_search': is_safe,
                'page': page,
                'proxy_mode': proxy_mode
            },
            'results': {
                'count': len(image_results),
                'images': image_results
            },
            'pagination': {
                'current_page': page,
                'next_page': page + 1,
                'next_page_url': f'/search?page={page + 1}' if request.method == 'GET' else None
            }
        })
        response = make_response(json_response, 200)

    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/search/<path:query>', methods=['GET'])
def search_get(query):
    safe_search = request.args.get('safe_search', 'true').lower() == 'true'
    size = request.args.get('size', 'any')
    time_range = request.args.get('time_range', 'any')
    page = int(request.args.get('page', 1))
    proxy_mode = request.args.get('proxy_mode', 'false').lower() == 'true'

    if not query or query.strip() == '':
        return jsonify({
            'success': False, 
            'error': 'Search query cannot be empty.',
            'example': '/search/mountains?size=large&safe_search=true',
            'tip': 'Visit /examples to see more query examples'
        }), 400

    if size not in ['any', 'large', 'medium', 'small']:
        return jsonify({
            'success': False,
            'error': f'Invalid size parameter: "{size}". Valid options: any, large, medium, small',
            'provided': size,
            'valid_options': ['any', 'large', 'medium', 'small']
        }), 400

    if time_range not in ['any', 'day', 'week', 'month', 'year']:
        return jsonify({
            'success': False,
            'error': f'Invalid time_range parameter: "{time_range}". Valid options: any, day, week, month, year',
            'provided': time_range,
            'valid_options': ['any', 'day', 'week', 'month', 'year']
        }), 400

    image_results = search_images_cached(query, safe_search, size, time_range, page)
    
    if image_results is None:
        json_response = jsonify({
            'success': False, 
            'error': 'Could not fetch results. All search providers are currently unavailable.',
            'suggestion': 'Please try again in a few moments. Our system rotates through multiple providers automatically.',
            'query': query,
            'providers_attempted': len(SEARX_INSTANCES)
        })
        response = make_response(json_response, 503)
    elif not image_results:
        json_response = jsonify({
            'success': False, 
            'error': 'No images found for this query.',
            'suggestion': 'Try different keywords, remove filters, or check a different page.',
            'query': query,
            'filters': {
                'size': size,
                'time_range': time_range,
                'safe_search': safe_search,
                'page': page
            }
        })
        response = make_response(json_response, 404)
    else:
        for item in image_results:
            if proxy_mode:
                img_src = item['img_src']
                if img_src.startswith('//'):
                    img_src = f"https:{img_src}"
                item['display_src'] = f"https://ovala.vercel.app/proxy/{img_src}"
            else:
                item['display_src'] = item['img_src']

        json_response = jsonify({
            'success': True,
            'query': query,
            'filters': {
                'size': size,
                'time_range': time_range,
                'safe_search': safe_search,
                'page': page,
                'proxy_mode': proxy_mode
            },
            'results': {
                'count': len(image_results),
                'images': image_results
            },
            'pagination': {
                'current_page': page,
                'next_page': page + 1,
                'next_page_url': f'/search/{query}?size={size}&time_range={time_range}&safe_search={str(safe_search).lower()}&page={page + 1}&proxy_mode={str(proxy_mode).lower()}'
            }
        })
        response = make_response(json_response, 200)

    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist.',
        'available_endpoints': [
            '/ - API documentation',
            '/search (POST) - Search with JSON body',
            '/search/<query> (GET) - Search with URL',
            '/examples - View example queries',
            '/health - API health check',
            '/stats - Cache and provider statistics'
        ],
        'suggestion': 'Visit the root endpoint (/) for complete API documentation'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred. Please try again later.',
        'suggestion': 'If the problem persists, check /health for API status'
    }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)