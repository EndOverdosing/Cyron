import requests
import time
import logging
from flask import Flask, request, jsonify, make_response, Response
from flask_cors import CORS
from datetime import datetime
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ── API keys (set these as Vercel environment variables) ─────────────────────
# BRAVE_API_KEY   - https://api.search.brave.com  (free: 2000 req/month)
# UNSPLASH_KEY    - https://unsplash.com/developers (free: 50 req/hour)
# PIXABAY_KEY     - https://pixabay.com/api/docs/  (free: 100 req/min)
#
# None are required — the app uses whichever keys are present and falls back
# gracefully. Add at least one for reliable results.
# ─────────────────────────────────────────────────────────────────────────────

BRAVE_API_KEY   = os.environ.get("BRAVE_API_KEY")
UNSPLASH_KEY    = os.environ.get("UNSPLASH_KEY")
PIXABAY_KEY     = os.environ.get("PIXABAY_KEY")

_cache = {}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

SIZE_MAP_PIXABAY = {
    'large':  'large',
    'medium': 'medium',
    'small':  'small',
    'any':    'all',
}

# ── Source: Brave Image Search ────────────────────────────────────────────────

def _search_brave(query, is_safe, size, page, debug_log):
    if not BRAVE_API_KEY:
        debug_log.append({"source": "brave", "error": "BRAVE_API_KEY not set"})
        return None

    params = {
        'q': query,
        'count': 20,
        'offset': (page - 1) * 20,
        'safesearch': 'strict' if is_safe else 'off',
    }
    if size != 'any':
        params['size'] = size

    try:
        r = requests.get(
            "https://api.search.brave.com/res/v1/images/search",
            params=params,
            headers={**HEADERS, 'Accept': 'application/json', 'X-Subscription-Token': BRAVE_API_KEY},
            timeout=10,
        )
        debug_log.append({"source": "brave", "status": r.status_code})
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get('results', []):
            src = item.get('properties', {}).get('url') or item.get('thumbnail', {}).get('src')
            if src:
                results.append({
                    'img_src': src,
                    'url': item.get('url', '#'),
                    'title': item.get('title', 'Untitled'),
                })
        debug_log[-1]['result_count'] = len(results)
        if results:
            logger.info(f"Brave: {len(results)} results for '{query}'")
            return results
        debug_log[-1]['error'] = 'No image results returned'
    except requests.exceptions.RequestException as e:
        debug_log.append({"source": "brave", "error": str(e)})
        logger.warning(f"Brave search failed: {e}")
    return None

# ── Source: Unsplash ──────────────────────────────────────────────────────────

def _search_unsplash(query, is_safe, size, page, debug_log):
    if not UNSPLASH_KEY:
        debug_log.append({"source": "unsplash", "error": "UNSPLASH_KEY not set"})
        return None

    params = {
        'query': query,
        'per_page': 20,
        'page': page,
        'content_filter': 'high' if is_safe else 'low',
    }

    try:
        r = requests.get(
            "https://api.unsplash.com/search/photos",
            params=params,
            headers={**HEADERS, 'Authorization': f'Client-ID {UNSPLASH_KEY}'},
            timeout=10,
        )
        debug_log.append({"source": "unsplash", "status": r.status_code})
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get('results', []):
            urls = item.get('urls', {})
            src = urls.get('regular') or urls.get('small') or urls.get('full')
            if src:
                user = item.get('user', {})
                results.append({
                    'img_src': src,
                    'url': item.get('links', {}).get('html', '#'),
                    'title': item.get('alt_description') or item.get('description') or f"Photo by {user.get('name', 'Unknown')}",
                })
        debug_log[-1]['result_count'] = len(results)
        if results:
            logger.info(f"Unsplash: {len(results)} results for '{query}'")
            return results
        debug_log[-1]['error'] = 'No image results returned'
    except requests.exceptions.RequestException as e:
        debug_log.append({"source": "unsplash", "error": str(e)})
        logger.warning(f"Unsplash search failed: {e}")
    return None

# ── Source: Pixabay ───────────────────────────────────────────────────────────

def _search_pixabay(query, is_safe, size, page, debug_log):
    if not PIXABAY_KEY:
        debug_log.append({"source": "pixabay", "error": "PIXABAY_KEY not set"})
        return None

    params = {
        'key': PIXABAY_KEY,
        'q': query,
        'image_type': 'photo',
        'per_page': 20,
        'page': page,
        'safesearch': 'true' if is_safe else 'false',
    }
    if size != 'any':
        params['min_width'] = {'large': 1920, 'medium': 1280, 'small': 640}.get(size, 0)

    try:
        r = requests.get(
            "https://pixabay.com/api/",
            params=params,
            headers=HEADERS,
            timeout=10,
        )
        debug_log.append({"source": "pixabay", "status": r.status_code})
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get('hits', []):
            src = item.get('largeImageURL') or item.get('webformatURL')
            if src:
                results.append({
                    'img_src': src,
                    'url': item.get('pageURL', '#'),
                    'title': ' '.join(item.get('tags', '').split(',')[:3]).strip() or 'Untitled',
                })
        debug_log[-1]['result_count'] = len(results)
        if results:
            logger.info(f"Pixabay: {len(results)} results for '{query}'")
            return results
        debug_log[-1]['error'] = 'No image results returned'
    except requests.exceptions.RequestException as e:
        debug_log.append({"source": "pixabay", "error": str(e)})
        logger.warning(f"Pixabay search failed: {e}")
    return None

# ── Orchestrator ──────────────────────────────────────────────────────────────

def search_images_cached(query, is_safe, size, time_range, page):
    cache_key = (query, is_safe, size, time_range, page)
    if cache_key in _cache:
        logger.info(f"Cache hit for '{query}'")
        cached = _cache[cache_key]
        return cached, [{"source": "cache", "result_count": len(cached)}]
    result, debug_log = _do_search(query, is_safe, size, page)
    if result is not None:
        _cache[cache_key] = result
    return result, debug_log

def _do_search(query, is_safe, size, page):
    debug_log = []
    configured = []
    if BRAVE_API_KEY:
        configured.append(('brave', _search_brave))
    if UNSPLASH_KEY:
        configured.append(('unsplash', _search_unsplash))
    if PIXABAY_KEY:
        configured.append(('pixabay', _search_pixabay))

    if not configured:
        debug_log.append({
            "error": "No API keys configured. Set BRAVE_API_KEY, UNSPLASH_KEY, or PIXABAY_KEY as environment variables.",
            "hint": "See the comments at the top of app.py for how to get free API keys."
        })
        logger.error("No API keys set — all sources unavailable")
        return None, debug_log

    for name, fn in configured:
        result = fn(query, is_safe, size, page, debug_log)
        if result:
            return result, debug_log

    return None, debug_log

# ── Streaming ─────────────────────────────────────────────────────────────────

def generate_streaming_results(query, is_safe, size, time_range, page, proxy_mode):
    image_results, debug_log = search_images_cached(query, is_safe, size, time_range, page)

    if image_results is None:
        yield f"data: {json.dumps({'success': False, 'error': 'Could not fetch results.', 'debug': debug_log})}\n\n"
        return

    yield f"data: {json.dumps({'type': 'metadata', 'success': True, 'query': query, 'total_count': len(image_results)})}\n\n"

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

# ── Helpers ───────────────────────────────────────────────────────────────────

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

def _no_cache_headers(resp):
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def index():
    sources_configured = []
    if BRAVE_API_KEY:   sources_configured.append('brave')
    if UNSPLASH_KEY:    sources_configured.append('unsplash')
    if PIXABAY_KEY:     sources_configured.append('pixabay')
    return jsonify({
        'name': 'Image Search API',
        'version': '3.0',
        'sources_configured': sources_configured if sources_configured else ['none — set API keys as env vars'],
        'description': 'Image search API with Brave, Unsplash, and Pixabay backends.',
        'setup': {
            'BRAVE_API_KEY':  'https://api.search.brave.com  (free: 2000 req/month)',
            'UNSPLASH_KEY':   'https://unsplash.com/developers (free: 50 req/hour)',
            'PIXABAY_KEY':    'https://pixabay.com/api/docs/  (free: 100 req/min)',
        },
        'endpoints': {
            '/search (POST)':         '{"query":"cats","per_page":20}',
            '/search/stream (POST)':  '{"query":"cats"} → SSE stream',
            '/search/<query> (GET)':  '/search/cats?per_page=20&size=large',
            '/health (GET)':          'health check',
            '/stats (GET)':           'cache + source status',
        },
        'parameters': {
            'query':       'search term (required)',
            'safe_search': 'true/false (default: true)',
            'size':        'any/large/medium/small (default: any)',
            'time_range':  'any/day/week/month/year (default: any, Brave only)',
            'page':        'page number (default: 1)',
            'per_page':    '1–100 images (default: all returned)',
            'proxy_mode':  'true/false (default: false)',
        },
    })

@app.route('/health', methods=['GET'])
def health_check():
    sources = {}
    if BRAVE_API_KEY:   sources['brave']    = 'configured'
    if UNSPLASH_KEY:    sources['unsplash'] = 'configured'
    if PIXABAY_KEY:     sources['pixabay']  = 'configured'
    if not sources:
        sources['warning'] = 'No API keys set — all searches will fail'
    return jsonify({
        'status': 'healthy',
        'version': '3.0',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'sources': sources,
        'cache_size': len(_cache),
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    sources = []
    if BRAVE_API_KEY:   sources.append('brave')
    if UNSPLASH_KEY:    sources.append('unsplash')
    if PIXABAY_KEY:     sources.append('pixabay')
    return jsonify({
        'success': True,
        'cache': {'current_size': len(_cache)},
        'sources': sources or ['none configured'],
        'fallback_order': sources,
    })

@app.route('/search/stream', methods=['POST'])
def search_stream_post():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON body.'}), 400
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400
    is_safe    = data.get('safe_search', True)
    size       = data.get('size', 'any')
    time_range = data.get('time_range', 'any')
    page       = int(data.get('page', 1))
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
        return jsonify({'success': False, 'error': 'Invalid JSON body.'}), 400
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400
    is_safe    = data.get('safe_search', True)
    size       = data.get('size', 'any')
    time_range = data.get('time_range', 'any')
    page       = int(data.get('page', 1))
    proxy_mode = data.get('proxy_mode', False)
    err = _validate_params(size, time_range)
    if err:
        return err
    per_page, err = _validate_per_page(data.get('per_page'))
    if err:
        return err

    image_results, debug_log = search_images_cached(query, is_safe, size, time_range, page)

    if image_results is None:
        return _no_cache_headers(make_response(jsonify({'success': False, 'error': 'Could not fetch results.', 'query': query, 'debug': debug_log}), 503))
    if not image_results:
        return _no_cache_headers(make_response(jsonify({'success': False, 'error': 'No images found.', 'query': query, 'debug': debug_log}), 404))
    return _no_cache_headers(make_response(jsonify(_build_results_response(image_results, query, size, time_range, is_safe, page, per_page, proxy_mode)), 200))

@app.route('/search/<path:query>', methods=['GET'])
def search_get(query):
    query = query.strip()
    if not query:
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400
    is_safe    = request.args.get('safe_search', 'true').lower() == 'true'
    size       = request.args.get('size', 'any')
    time_range = request.args.get('time_range', 'any')
    page       = int(request.args.get('page', 1))
    proxy_mode = request.args.get('proxy_mode', 'false').lower() == 'true'
    err = _validate_params(size, time_range)
    if err:
        return err
    per_page, err = _validate_per_page(request.args.get('per_page'))
    if err:
        return err

    image_results, debug_log = search_images_cached(query, is_safe, size, time_range, page)

    if image_results is None:
        return _no_cache_headers(make_response(jsonify({'success': False, 'error': 'Could not fetch results.', 'debug': debug_log}), 503))
    if not image_results:
        return _no_cache_headers(make_response(jsonify({'success': False, 'error': 'No images found.', 'debug': debug_log}), 404))
    return _no_cache_headers(make_response(jsonify(_build_results_response(image_results, query, size, time_range, is_safe, page, per_page, proxy_mode)), 200))

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found.', 'available_endpoints': ['/', '/search (POST)', '/search/stream (POST)', '/search/<query> (GET)', '/health', '/stats']}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error.'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)