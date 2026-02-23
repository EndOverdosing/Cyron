import requests
import random
from flask import Flask, request, jsonify, make_response, Response
from flask_cors import CORS
from datetime import datetime
import json
import time

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

_cache = {}

def search_images_cached(query, is_safe, size, time_range, page):
    cache_key = (query, is_safe, size, time_range, page)
    if cache_key in _cache:
        return _cache[cache_key]

    result = _do_search(query, is_safe, size, time_range, page)
    if result is not None:
        _cache[cache_key] = result
    return result

def _do_search(query, is_safe, size, time_range, page):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }

    params = {
        'q': query,
        'categories': 'images',
        'format': 'json',
        'safesearch': '1' if is_safe else '0',
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

def generate_streaming_results(query, is_safe, size, time_range, page, proxy_mode):
    image_results = search_images_cached(query, is_safe, size, time_range, page)

    if image_results is None:
        yield f"data: {json.dumps({'success': False, 'error': 'Could not fetch results. All search providers are currently unavailable.', 'providers_attempted': len(SEARX_INSTANCES)})}\n\n"
        return

    if not image_results:
        yield f"data: {json.dumps({'success': False, 'error': 'No images found for this query.', 'query': query})}\n\n"
        return

    metadata = {
        'type': 'metadata',
        'success': True,
        'query': query,
        'filters': {
            'size': size,
            'time_range': time_range,
            'safe_search': is_safe,
            'page': page,
            'proxy_mode': proxy_mode
        },
        'total_count': len(image_results)
    }
    yield f"data: {json.dumps(metadata)}\n\n"

    for index, item in enumerate(image_results):
        if proxy_mode:
            img_src = item['img_src']
            if img_src.startswith('//'):
                img_src = f"https:{img_src}"
            item['display_src'] = f"https://ovala.vercel.app/proxy/{img_src}"
        else:
            item['display_src'] = item['img_src']

        image_data = {
            'type': 'image',
            'index': index,
            'data': item
        }
        yield f"data: {json.dumps(image_data)}\n\n"
        time.sleep(0.1)

    completion = {
        'type': 'complete',
        'total_sent': len(image_results)
    }
    yield f"data: {json.dumps(completion)}\n\n"

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'name': 'Image Search API',
        'version': '2.0',
        'description': 'Privacy-focused image search API powered by SearX instances with flexible pagination support',
        'documentation': 'https://github.com/endoverdosing/Cyron',
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
                    'per_page': 20,
                    'proxy_mode': False
                }
            },
            '/search/stream': {
                'method': 'POST',
                'description': 'Search for images with streaming',
                'content_type': 'application/json',
                'response_type': 'text/event-stream',
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
                'description': 'Search for images using URL path',
                'example': '/search/mountains?size=large&page=1&per_page=20',
                'parameters': {
                    'query': 'Search term (in URL path)',
                    'safe_search': 'true/false (default: true)',
                    'size': 'any/large/medium/small (default: any)',
                    'time_range': 'any/day/week/month/year (default: any)',
                    'page': 'number (default: 1)',
                    'per_page': 'images per page, 1-100 (default: all available)',
                    'proxy_mode': 'true/false (default: false)',
                    'stream': 'true/false (default: false)'
                }
            },
            '/examples': {
                'method': 'GET',
                'description': 'Get example search queries'
            },
            '/health': {
                'method': 'GET',
                'description': 'API health check'
            },
            '/stats': {
                'method': 'GET',
                'description': 'View cache statistics'
            }
        },
        'quick_start': {
            'browser': '/search/cats?page=1&per_page=10',
            'streaming': '/search/cats?stream=true',
            'curl': 'curl -X POST /search -H "Content-Type: application/json" -d \'{"query": "cats", "per_page": 20}\'',
            'curl_streaming': 'curl -X POST /search/stream -H "Content-Type: application/json" -d \'{"query": "cats"}\'',
            'python': 'requests.post(API_URL + "/search", json={"query": "cats", "per_page": 15})',
            'javascript': 'fetch(API_URL + "/search", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({query: "cats", per_page: 25})})'
        },
        'features': [
            'Privacy-focused (no tracking)',
            'Multiple SearX instances for reliability',
            'Built-in caching for performance',
            'CORS enabled for web apps',
            'Safe search filtering',
            'Image size filtering',
            'Time range filtering',
            'Flexible pagination (1-100 images per page)',
            'Optional image proxy',
            'Streaming mode for dynamic loading'
        ]
    })

@app.route('/examples', methods=['GET'])
def get_examples():
    return jsonify({
        'success': True,
        'message': 'Example searches with pagination support',
        'examples': [
            {
                'category': 'Basic Searches',
                'description': 'Simple queries to get started',
                'queries': [
                    {
                        'name': 'Simple search - 10 per page',
                        'url': '/search/sunset?per_page=10',
                        'post_body': {'query': 'sunset', 'per_page': 10}
                    },
                    {
                        'name': 'Multi-word search - 25 per page',
                        'url': '/search/cute puppies?per_page=25',
                        'post_body': {'query': 'cute puppies', 'safe_search': True, 'per_page': 25}
                    },
                    {
                        'name': 'All available images',
                        'url': '/search/mountain landscape',
                        'post_body': {'query': 'mountain landscape'}
                    }
                ]
            },
            {
                'category': 'Pagination Examples',
                'description': 'Different pagination strategies',
                'queries': [
                    {
                        'name': 'Page 1 - 15 images',
                        'url': '/search/nature?page=1&per_page=15',
                        'post_body': {'query': 'nature', 'page': 1, 'per_page': 15}
                    },
                    {
                        'name': 'Page 2 - 15 images',
                        'url': '/search/nature?page=2&per_page=15',
                        'post_body': {'query': 'nature', 'page': 2, 'per_page': 15}
                    },
                    {
                        'name': 'Page 3 - 20 images',
                        'url': '/search/nature?page=3&per_page=20',
                        'post_body': {'query': 'nature', 'page': 3, 'per_page': 20}
                    }
                ]
            },
            {
                'category': 'Size Filtered with Pagination',
                'description': 'Combine filters with custom page sizes',
                'queries': [
                    {
                        'name': 'Large wallpapers - 12 per page',
                        'url': '/search/nature wallpaper?size=large&per_page=12',
                        'post_body': {'query': 'nature wallpaper', 'size': 'large', 'per_page': 12}
                    },
                    {
                        'name': 'Medium photos - 30 per page',
                        'url': '/search/food photography?size=medium&per_page=30',
                        'post_body': {'query': 'food photography', 'size': 'medium', 'per_page': 30}
                    }
                ]
            },
            {
                'category': 'Streaming Mode',
                'description': 'Dynamic loading examples',
                'queries': [
                    {
                        'name': 'Stream large landscapes',
                        'url': '/search/landscape?size=large&stream=true',
                        'post_endpoint': '/search/stream',
                        'post_body': {'query': 'landscape', 'size': 'large'}
                    }
                ]
            }
        ],
        'tips': [
            'Use per_page parameter to control images per page (1-100)',
            'Omit per_page to get all available images from the page',
            'Combine page and per_page for efficient pagination',
            'Use stream=true for progressive loading',
            'Page numbers start from 1'
        ]
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Image Search API',
        'version': '2.0',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'providers': {
            'total': len(SEARX_INSTANCES),
            'status': 'operational'
        },
        'features': {
            'cache_enabled': True,
            'cors_enabled': True,
            'safe_search': True,
            'proxy_mode': True,
            'streaming': True,
            'flexible_pagination': True
        }
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify({
        'success': True,
        'cache': {
            'current_size': len(_cache),
            'efficiency': 'manual dict cache (no eviction)'
        },
        'providers': {
            'total_instances': len(SEARX_INSTANCES),
            'instances': SEARX_INSTANCES,
            'rotation': 'random',
            'failover': 'automatic'
        },
        'api_info': {
            'version': '2.0',
            'uptime': 'check /health for status',
            'cors': 'enabled',
            'streaming': 'enabled',
            'pagination': 'flexible (1-100 per page)',
            'rate_limiting': 'none (consider adding for production)'
        }
    })

@app.route('/search/stream', methods=['POST'])
def search_stream_post():
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
            'error': 'Search query cannot be empty.',
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

    return Response(
        generate_streaming_results(query, is_safe, size, time_range, page, proxy_mode),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )

@app.route('/search', methods=['POST'])
def search_for_images():
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'error': 'Invalid JSON body. Please send a valid JSON object with a "query" field.',
            'example': {'query': 'mountains', 'safe_search': True, 'size': 'large', 'per_page': 20}
        }), 400

    query = data.get('query')
    is_safe = data.get('safe_search', True)
    size = data.get('size', 'any')
    time_range = data.get('time_range', 'any')
    page = int(data.get('page', 1))
    per_page = data.get('per_page')
    proxy_mode = data.get('proxy_mode', False)

    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query cannot be empty.',
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

    if per_page is not None:
        try:
            per_page = int(per_page)
            if per_page < 1 or per_page > 100:
                return jsonify({
                    'success': False,
                    'error': 'per_page must be between 1 and 100',
                    'provided': per_page
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'per_page must be a valid integer'
            }), 400

    image_results = search_images_cached(query, is_safe, size, time_range, page)

    if image_results is None:
        json_response = jsonify({
            'success': False,
            'error': 'Could not fetch results. All search providers are currently unavailable.',
            'suggestion': 'Please try again in a few moments.',
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
        total_images = len(image_results)

        if per_page is not None:
            image_results = image_results[:per_page]

        for item in image_results:
            if proxy_mode:
                img_src = item['img_src']
                if img_src.startswith('//'):
                    img_src = f"https:{img_src}"
                item['display_src'] = f"https://ovala.vercel.app/proxy/{img_src}"
            else:
                item['display_src'] = item['img_src']

        pagination_info = {
            'current_page': page,
            'per_page': per_page if per_page is not None else total_images,
            'total_on_page': total_images,
            'returned': len(image_results),
            'has_next': True
        }

        if per_page is not None:
            pagination_info['next_page'] = page + 1

        json_response = jsonify({
            'success': True,
            'query': query,
            'filters': {
                'size': size,
                'time_range': time_range,
                'safe_search': is_safe,
                'page': page,
                'per_page': per_page,
                'proxy_mode': proxy_mode
            },
            'results': {
                'count': len(image_results),
                'images': image_results
            },
            'pagination': pagination_info
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
    per_page = request.args.get('per_page')

    if not query or query.strip() == '':
        return jsonify({
            'success': False,
            'error': 'Search query cannot be empty.',
        }), 400

    if per_page is not None:
        try:
            per_page = int(per_page)
            if per_page < 1 or per_page > 100:
                return jsonify({
                    'success': False,
                    'error': 'per_page must be between 1 and 100',
                    'provided': per_page
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'per_page must be a valid integer'
            }), 400

    image_results = search_images_cached(query, safe_search, size, time_range, page)

    if image_results is None:
        return jsonify({
            'success': False,
            'error': 'Could not fetch results.',
        }), 503

    if not image_results:
        return jsonify({
            'success': False,
            'error': 'No images found.',
        }), 404

    total_images = len(image_results)

    if per_page is not None:
        image_results = image_results[:per_page]

    for item in image_results:
        if proxy_mode:
            img_src = item['img_src']
            if img_src.startswith('//'):
                img_src = f"https:{img_src}"
            item['display_src'] = f"https://ovala.vercel.app/proxy/{img_src}"
        else:
            item['display_src'] = item['img_src']

    pagination_info = {
        'current_page': page,
        'per_page': per_page if per_page is not None else total_images,
        'total_on_page': total_images,
        'returned': len(image_results),
        'has_next': True
    }

    if per_page is not None:
        pagination_info['next_page'] = page + 1

    response = jsonify({
        'success': True,
        'query': query,
        'filters': {
            'size': size,
            'time_range': time_range,
            'safe_search': safe_search,
            'page': page,
            'per_page': per_page,
            'proxy_mode': proxy_mode
        },
        'results': {
            'count': len(image_results),
            'images': image_results
        },
        'pagination': pagination_info
    })

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
            '/search/stream (POST) - Streaming search',
            '/search/<query> (GET) - Search with URL',
            '/examples - View examples',
            '/health - Health check',
            '/stats - Statistics'
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