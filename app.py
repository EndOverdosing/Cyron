import requests
import random
import time
import logging
from flask import Flask, request, jsonify, make_response, Response
from flask_cors import CORS
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

FALLBACK_INSTANCES = [
    "https://baresearch.org",
    "https://copp.gg",
    "https://etsi.me",
    "https://paulgo.io",
    "https://search.inetol.net",
    "https://searxng.site",
    "https://search.hbubli.cc",
    "https://searx.tiekoetter.com",
    "https://search.ononoki.org",
    "https://searx.oxafree.com",
    "https://searx.fmac.xyz",
    "https://searx.be",
]

_instances_cache = {"instances": list(FALLBACK_INSTANCES), "last_updated": 0}
_cache = {}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
}

def get_instances():
    now = time.time()
    if now - _instances_cache["last_updated"] < 3600:
        return _instances_cache["instances"]
    try:
        logger.info("Refreshing instance list from searx.space...")
        r = requests.get("https://searx.space/data/instances.json", timeout=8, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        good = []
        for url, info in data.get("instances", {}).items():
            if info.get("network_type") != "normal":
                continue
            if info.get("http", {}).get("status_code") != 200:
                continue
            uptime = info.get("uptime", {})
            if uptime.get("uptimeWeek", 0) < 95:
                continue
            search = info.get("timing", {}).get("search", {})
            if search.get("success_percentage", 0) < 95:
                continue
            good.append(url.rstrip("/"))
        if good:
            _instances_cache["instances"] = good
            _instances_cache["last_updated"] = now
            logger.info(f"Loaded {len(good)} instances from searx.space")
        else:
            logger.warning("searx.space returned no usable instances, keeping fallback list")
    except Exception as e:
        logger.warning(f"Failed to refresh instances from searx.space: {e}")
    return _instances_cache["instances"]

def search_images_cached(query, is_safe, size, time_range, page):
    cache_key = (query, is_safe, size, time_range, page)
    if cache_key in _cache:
        logger.info(f"Cache hit for query='{query}'")
        return _cache[cache_key]
    result, debug_log = _do_search(query, is_safe, size, time_range, page)
    if result is not None:
        _cache[cache_key] = result
    return result, debug_log

def _do_search(query, is_safe, size, time_range, page):
    params = {
        'q': query,
        'categories': 'images',
        'format': 'json',
        'safesearch': '1' if is_safe else '0',
        'pageno': page,
    }
    if size != 'any':
        params['img_size'] = size
    if time_range != 'any':
        params['time_range'] = time_range

    instances = get_instances()
    shuffled = random.sample(instances, min(len(instances), 11))
    debug_log = []

    logger.info(f"Starting search: query='{query}', trying {len(shuffled)} instances")

    for instance in shuffled:
        entry = {"instance": instance, "status": None, "error": None, "result_count": 0}
        try:
            response = requests.get(
                f"{instance}/search",
                params=params,
                headers=HEADERS,
                timeout=10
            )
            entry["status"] = response.status_code

            if response.status_code != 200:
                entry["error"] = f"HTTP {response.status_code}"
                debug_log.append(entry)
                logger.warning(f"  {instance} -> HTTP {response.status_code}")
                continue

            content_type = response.headers.get('Content-Type', '')
            entry["content_type"] = content_type

            if 'json' not in content_type:
                preview = response.text[:120].replace('\n', ' ')
                entry["error"] = f"Non-JSON response (Content-Type: {content_type}). Body preview: {preview!r}"
                debug_log.append(entry)
                logger.warning(f"  {instance} -> non-JSON content-type: {content_type}. Likely HTML/CAPTCHA. Preview: {preview!r}")
                continue

            try:
                data = response.json()
            except ValueError as e:
                preview = response.text[:120].replace('\n', ' ')
                entry["error"] = f"JSON parse error: {e}. Body preview: {preview!r}"
                debug_log.append(entry)
                logger.warning(f"  {instance} -> JSON parse failed: {e}. Preview: {preview!r}")
                continue

            if 'results' not in data:
                entry["error"] = f"No 'results' key in response. Keys present: {list(data.keys())}"
                debug_log.append(entry)
                logger.warning(f"  {instance} -> missing 'results' key, got keys: {list(data.keys())}")
                continue

            image_results = []
            for result in data['results']:
                if 'img_src' in result and result['img_src']:
                    image_results.append({
                        "img_src": result['img_src'],
                        "url": result.get('url', '#'),
                        "title": result.get('title', 'Untitled'),
                    })

            entry["result_count"] = len(image_results)

            if not image_results:
                entry["error"] = f"0 image results (total results in response: {len(data['results'])})"
                debug_log.append(entry)
                logger.warning(f"  {instance} -> 0 images (total results: {len(data['results'])})")
                continue

            entry["status"] = "success"
            debug_log.append(entry)
            logger.info(f"  {instance} -> SUCCESS: {len(image_results)} images")
            return image_results, debug_log

        except requests.exceptions.Timeout:
            entry["error"] = "Timeout (10s)"
            debug_log.append(entry)
            logger.warning(f"  {instance} -> Timeout")
        except requests.exceptions.ConnectionError as e:
            entry["error"] = f"Connection error: {e}"
            debug_log.append(entry)
            logger.warning(f"  {instance} -> Connection error: {e}")
        except requests.exceptions.RequestException as e:
            entry["error"] = f"Request error: {e}"
            debug_log.append(entry)
            logger.warning(f"  {instance} -> Request error: {e}")

    logger.error(f"All instances failed for query='{query}'")
    return None, debug_log

def generate_streaming_results(query, is_safe, size, time_range, page, proxy_mode):
    image_results, debug_log = search_images_cached(query, is_safe, size, time_range, page)

    if image_results is None:
        yield f"data: {json.dumps({'success': False, 'error': 'Could not fetch results. All search providers are currently unavailable.', 'debug': debug_log})}\n\n"
        return

    if not image_results:
        yield f"data: {json.dumps({'success': False, 'error': 'No images found for this query.', 'query': query, 'debug': debug_log})}\n\n"
        return

    yield f"data: {json.dumps({'type': 'metadata', 'success': True, 'query': query, 'filters': {'size': size, 'time_range': time_range, 'safe_search': is_safe, 'page': page, 'proxy_mode': proxy_mode}, 'total_count': len(image_results)})}\n\n"

    for index, item in enumerate(image_results):
        if proxy_mode:
            img_src = item['img_src']
            if img_src.startswith('//'):
                img_src = f"https:{img_src}"
            item['display_src'] = f"https://ovala.vercel.app/proxy/{img_src}"
        else:
            item['display_src'] = item['img_src']

        yield f"data: {json.dumps({'type': 'image', 'index': index, 'data': item})}\n\n"
        time.sleep(0.05)

    yield f"data: {json.dumps({'type': 'complete', 'total_sent': len(image_results)})}\n\n"

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'name': 'Image Search API',
        'version': '2.1',
        'description': 'Privacy-focused image search API powered by SearXNG instances with flexible pagination support',
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
                'description': 'Search for images with Server-Sent Events streaming',
                'content_type': 'application/json',
                'response_type': 'text/event-stream',
                'body_example': {'query': 'mountains', 'safe_search': True, 'size': 'large', 'page': 1, 'proxy_mode': False}
            },
            '/search/<query>': {
                'method': 'GET',
                'description': 'Search for images using URL path',
                'example': '/search/mountains?size=large&page=1&per_page=20',
                'parameters': {
                    'safe_search': 'true/false (default: true)',
                    'size': 'any/large/medium/small (default: any)',
                    'time_range': 'any/day/week/month/year (default: any)',
                    'page': 'number (default: 1)',
                    'per_page': '1-100 (default: all available)',
                    'proxy_mode': 'true/false (default: false)',
                }
            },
            '/examples': {'method': 'GET', 'description': 'Get example search queries'},
            '/health': {'method': 'GET', 'description': 'API health check'},
            '/stats': {'method': 'GET', 'description': 'View cache and instance statistics'},
        },
        'quick_start': {
            'browser': '/search/cats?page=1&per_page=10',
            'curl': 'curl -X POST /search -H "Content-Type: application/json" -d \'{"query": "cats", "per_page": 20}\'',
            'python': 'requests.post(API_URL + "/search", json={"query": "cats", "per_page": 15})',
            'javascript': 'fetch(API_URL + "/search", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({query:"cats", per_page:25})})',
        },
        'features': [
            'Privacy-focused (no tracking)',
            'Auto-refreshing instance list from searx.space',
            'Per-instance debug logging on failure',
            'Multiple SearXNG instances for reliability',
            'Built-in caching for performance',
            'CORS enabled for web apps',
            'Safe search, size, and time range filtering',
            'Flexible pagination (1-100 images per page)',
            'Optional image proxy',
            'Streaming mode (SSE) for dynamic loading',
        ]
    })

@app.route('/examples', methods=['GET'])
def get_examples():
    return jsonify({
        'success': True,
        'examples': [
            {'name': 'Basic search', 'url': '/search/sunset?per_page=10', 'post_body': {'query': 'sunset', 'per_page': 10}},
            {'name': 'Large images only', 'url': '/search/nature?size=large&per_page=20', 'post_body': {'query': 'nature', 'size': 'large', 'per_page': 20}},
            {'name': 'Recent images', 'url': '/search/space?time_range=week&per_page=15', 'post_body': {'query': 'space', 'time_range': 'week', 'per_page': 15}},
            {'name': 'Page 2', 'url': '/search/cats?page=2&per_page=20', 'post_body': {'query': 'cats', 'page': 2, 'per_page': 20}},
        ],
        'tips': [
            'per_page controls images returned (1-100)',
            'Omit per_page to get all available results',
            'Use page + per_page together for pagination',
            'Page numbers start at 1',
            'Check the "debug" field on errors to see per-instance failure reasons',
        ]
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Image Search API',
        'version': '2.1',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'providers': {
            'total': len(get_instances()),
            'status': 'operational',
            'source': 'searx.space (auto-refreshed hourly)',
        },
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    instances = get_instances()
    return jsonify({
        'success': True,
        'cache': {'current_size': len(_cache)},
        'providers': {
            'total_instances': len(instances),
            'instances': instances,
            'source': 'searx.space',
            'last_updated': datetime.utcfromtimestamp(_instances_cache['last_updated']).isoformat() + 'Z' if _instances_cache['last_updated'] else 'never',
            'rotation': 'random',
            'failover': 'sequential with per-instance debug logging',
        },
    })

def _validate_params(size, time_range):
    if size not in ['any', 'large', 'medium', 'small']:
        return jsonify({'success': False, 'error': f'Invalid size: "{size}".', 'valid_options': ['any', 'large', 'medium', 'small']}), 400
    if time_range not in ['any', 'day', 'week', 'month', 'year']:
        return jsonify({'success': False, 'error': f'Invalid time_range: "{time_range}".', 'valid_options': ['any', 'day', 'week', 'month', 'year']}), 400
    return None

def _validate_per_page(per_page):
    if per_page is None:
        return None, None
    try:
        per_page = int(per_page)
        if per_page < 1 or per_page > 100:
            return None, (jsonify({'success': False, 'error': 'per_page must be between 1 and 100'}), 400)
    except (ValueError, TypeError):
        return None, (jsonify({'success': False, 'error': 'per_page must be a valid integer'}), 400)
    return per_page, None

def _build_results_response(image_results, query, size, time_range, is_safe, page, per_page, proxy_mode):
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
        'has_next': True,
    }
    if per_page is not None:
        pagination_info['next_page'] = page + 1

    return {
        'success': True,
        'query': query,
        'filters': {'size': size, 'time_range': time_range, 'safe_search': is_safe, 'page': page, 'per_page': per_page, 'proxy_mode': proxy_mode},
        'results': {'count': len(image_results), 'images': image_results},
        'pagination': pagination_info,
    }

@app.route('/search/stream', methods=['POST'])
def search_stream_post():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON body.'}), 400

    query = data.get('query', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400

    is_safe = data.get('safe_search', True)
    size = data.get('size', 'any')
    time_range = data.get('time_range', 'any')
    page = int(data.get('page', 1))
    proxy_mode = data.get('proxy_mode', False)

    err = _validate_params(size, time_range)
    if err:
        return err

    return Response(
        generate_streaming_results(query, is_safe, size, time_range, page, proxy_mode),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive'},
    )

@app.route('/search', methods=['POST'])
def search_for_images():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON body.', 'example': {'query': 'mountains', 'per_page': 20}}), 400

    query = data.get('query', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400

    is_safe = data.get('safe_search', True)
    size = data.get('size', 'any')
    time_range = data.get('time_range', 'any')
    page = int(data.get('page', 1))
    proxy_mode = data.get('proxy_mode', False)

    err = _validate_params(size, time_range)
    if err:
        return err

    per_page, err = _validate_per_page(data.get('per_page'))
    if err:
        return err

    image_results, debug_log = search_images_cached(query, is_safe, size, time_range, page)

    if image_results is None:
        resp = make_response(jsonify({
            'success': False,
            'error': 'Could not fetch results. All search providers are currently unavailable.',
            'query': query,
            'debug': debug_log,
        }), 503)
    elif not image_results:
        resp = make_response(jsonify({
            'success': False,
            'error': 'No images found for this query.',
            'query': query,
            'debug': debug_log,
        }), 404)
    else:
        resp = make_response(jsonify(_build_results_response(image_results, query, size, time_range, is_safe, page, per_page, proxy_mode)), 200)

    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/search/<path:query>', methods=['GET'])
def search_get(query):
    query = query.strip()
    if not query:
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400

    is_safe = request.args.get('safe_search', 'true').lower() == 'true'
    size = request.args.get('size', 'any')
    time_range = request.args.get('time_range', 'any')
    page = int(request.args.get('page', 1))
    proxy_mode = request.args.get('proxy_mode', 'false').lower() == 'true'

    err = _validate_params(size, time_range)
    if err:
        return err

    per_page, err = _validate_per_page(request.args.get('per_page'))
    if err:
        return err

    image_results, debug_log = search_images_cached(query, is_safe, size, time_range, page)

    if image_results is None:
        resp = jsonify({'success': False, 'error': 'Could not fetch results.', 'debug': debug_log})
        resp.status_code = 503
        return resp
    if not image_results:
        resp = jsonify({'success': False, 'error': 'No images found.', 'debug': debug_log})
        resp.status_code = 404
        return resp

    resp = jsonify(_build_results_response(image_results, query, size, time_range, is_safe, page, per_page, proxy_mode))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found.',
        'available_endpoints': ['/', '/search (POST)', '/search/stream (POST)', '/search/<query> (GET)', '/examples', '/health', '/stats'],
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error. Check /health for status.'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)