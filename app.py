import requests
import random
from flask import Flask, request, jsonify, make_response, Response
from flask_cors import CORS
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
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

def try_instance(instance, params, headers):
    try:
        response = requests.get(
            f"{instance}/search",
            params=params,
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        if 'results' in data and data['results']:
            image_results = []
            for result in data['results']:
                if 'img_src' in result and result['img_src']:
                    image_results.append({
                        "img_src": result['img_src'],
                        "url": result.get('url', '#'),
                        "title": result.get('title', 'Untitled')
                    })
            if image_results:
                return image_results
    except Exception:
        pass
    return None

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

    instances_to_try = random.sample(SEARX_INSTANCES, min(5, len(SEARX_INSTANCES)))

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(try_instance, inst, params, headers): inst for inst in instances_to_try}
        for future in as_completed(futures, timeout=8):
            try:
                result = future.result()
                if result:
                    return result
            except Exception:
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
        time.sleep(0.05)

    yield f"data: {json.dumps({'type': 'complete', 'total_sent': len(image_results)})}\n\n"

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'name': 'Image Search API',
        'version': '2.0',
        'description': 'Privacy-focused image search API powered by SearX instances with flexible pagination support',
        'documentation': 'https://github.com/endoverdosing/Cyron',
        'endpoints': {
            '/': {'method': 'GET', 'description': 'API information and documentation'},
            '/search': {
                'method': 'POST',
                'description': 'Search for images using JSON body',
                'content_type': 'application/json',
                'body_example': {'query': 'mountains', 'safe_search': True, 'size': 'large', 'time_range': 'week', 'page': 1, 'per_page': 20, 'proxy_mode': False}
            },
            '/search/stream': {
                'method': 'POST',
                'description': 'Search for images with streaming',
                'content_type': 'application/json',
                'response_type': 'text/event-stream',
                'body_example': {'query': 'mountains', 'safe_search': True, 'size': 'large', 'time_range': 'week', 'page': 1, 'proxy_mode': False}
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
                    'proxy_mode': 'true/false (default: false)'
                }
            },
            '/examples': {'method': 'GET', 'description': 'Get example search queries'},
            '/health': {'method': 'GET', 'description': 'API health check'},
            '/stats': {'method': 'GET', 'description': 'View cache statistics'}
        },
        'quick_start': {
            'browser': '/search/cats?page=1&per_page=10',
            'curl': 'curl -X POST /search -H "Content-Type: application/json" -d \'{"query": "cats", "per_page": 20}\'',
            'python': 'requests.post(API_URL + "/search", json={"query": "cats", "per_page": 15})',
            'javascript': 'fetch(API_URL + "/search", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({query: "cats", per_page: 25})})'
        },
        'features': [
            'Privacy-focused (no tracking)',
            'Multiple SearX instances for reliability',
            'Parallel instance querying for speed',
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
        'examples': [
            {
                'category': 'Basic Searches',
                'queries': [
                    {'name': 'Simple search', 'url': '/search/sunset?per_page=10', 'post_body': {'query': 'sunset', 'per_page': 10}},
                    {'name': 'Multi-word search', 'url': '/search/cute puppies?per_page=25', 'post_body': {'query': 'cute puppies', 'safe_search': True, 'per_page': 25}}
                ]
            },
            {
                'category': 'Pagination',
                'queries': [
                    {'name': 'Page 1', 'url': '/search/nature?page=1&per_page=15', 'post_body': {'query': 'nature', 'page': 1, 'per_page': 15}},
                    {'name': 'Page 2', 'url': '/search/nature?page=2&per_page=15', 'post_body': {'query': 'nature', 'page': 2, 'per_page': 15}}
                ]
            }
        ],
        'tips': [
            'Use per_page to control images per page (1-100)',
            'Combine page and per_page for pagination',
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
        'providers': {'total': len(SEARX_INSTANCES), 'status': 'operational'},
        'features': {
            'cache_enabled': True,
            'cors_enabled': True,
            'safe_search': True,
            'proxy_mode': True,
            'streaming': True,
            'flexible_pagination': True,
            'parallel_search': True
        }
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify({
        'success': True,
        'cache': {'current_size': len(_cache), 'efficiency': 'manual dict cache (no eviction)'},
        'providers': {'total_instances': len(SEARX_INSTANCES), 'instances': SEARX_INSTANCES, 'rotation': 'random', 'failover': 'parallel'},
        'api_info': {'version': '2.0', 'cors': 'enabled', 'streaming': 'enabled', 'pagination': 'flexible (1-100 per page)'}
    })

@app.route('/search/stream', methods=['POST'])
def search_stream_post():
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON body.', 'example': {'query': 'mountains'}}), 400

    query = data.get('query')
    is_safe = data.get('safe_search', True)
    size = data.get('size', 'any')
    time_range = data.get('time_range', 'any')
    page = int(data.get('page', 1))
    proxy_mode = data.get('proxy_mode', False)

    if not query:
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400

    if size not in ['any', 'large', 'medium', 'small']:
        return jsonify({'success': False, 'error': f'Invalid size: "{size}".', 'valid_options': ['any', 'large', 'medium', 'small']}), 400

    if time_range not in ['any', 'day', 'week', 'month', 'year']:
        return jsonify({'success': False, 'error': f'Invalid time_range: "{time_range}".', 'valid_options': ['any', 'day', 'week', 'month', 'year']}), 400

    return Response(
        generate_streaming_results(query, is_safe, size, time_range, page, proxy_mode),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive'}
    )

@app.route('/search', methods=['POST'])
def search_for_images():
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON body.', 'example': {'query': 'mountains', 'per_page': 20}}), 400

    query = data.get('query')
    is_safe = data.get('safe_search', True)
    size = data.get('size', 'any')
    time_range = data.get('time_range', 'any')
    page = int(data.get('page', 1))
    per_page = data.get('per_page')
    proxy_mode = data.get('proxy_mode', False)

    if not query:
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400

    if size not in ['any', 'large', 'medium', 'small']:
        return jsonify({'success': False, 'error': f'Invalid size: "{size}".', 'valid_options': ['any', 'large', 'medium', 'small']}), 400

    if time_range not in ['any', 'day', 'week', 'month', 'year']:
        return jsonify({'success': False, 'error': f'Invalid time_range: "{time_range}".', 'valid_options': ['any', 'day', 'week', 'month', 'year']}), 400

    if per_page is not None:
        try:
            per_page = int(per_page)
            if per_page < 1 or per_page > 100:
                return jsonify({'success': False, 'error': 'per_page must be between 1 and 100'}), 400
        except ValueError:
            return jsonify({'success': False, 'error': 'per_page must be a valid integer'}), 400

    image_results = search_images_cached(query, is_safe, size, time_range, page)

    if image_results is None:
        response = make_response(jsonify({
            'success': False,
            'error': 'Could not fetch results. All search providers are currently unavailable.',
            'suggestion': 'Please try again in a few moments.',
            'query': query,
            'providers_attempted': len(SEARX_INSTANCES)
        }), 503)
    elif not image_results:
        response = make_response(jsonify({
            'success': False,
            'error': 'No images found for this query.',
            'suggestion': 'Try different keywords, remove filters, or check a different page.',
            'query': query
        }), 404)
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

        response = make_response(jsonify({
            'success': True,
            'query': query,
            'filters': {'size': size, 'time_range': time_range, 'safe_search': is_safe, 'page': page, 'per_page': per_page, 'proxy_mode': proxy_mode},
            'results': {'count': len(image_results), 'images': image_results},
            'pagination': pagination_info
        }), 200)

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
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400

    if per_page is not None:
        try:
            per_page = int(per_page)
            if per_page < 1 or per_page > 100:
                return jsonify({'success': False, 'error': 'per_page must be between 1 and 100'}), 400
        except ValueError:
            return jsonify({'success': False, 'error': 'per_page must be a valid integer'}), 400

    image_results = search_images_cached(query, safe_search, size, time_range, page)

    if image_results is None:
        return jsonify({'success': False, 'error': 'Could not fetch results.'}), 503

    if not image_results:
        return jsonify({'success': False, 'error': 'No images found.'}), 404

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
        'filters': {'size': size, 'time_range': time_range, 'safe_search': safe_search, 'page': page, 'per_page': per_page, 'proxy_mode': proxy_mode},
        'results': {'count': len(image_results), 'images': image_results},
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
        'available_endpoints': ['/', '/search (POST)', '/search/stream (POST)', '/search/<query> (GET)', '/examples', '/health', '/stats'],
        'suggestion': 'Visit / for full documentation'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'suggestion': 'Check /health for API status'
    }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)