import requests
import random
from flask import Flask, render_template, request, jsonify, make_response
from functools import lru_cache

app = Flask(__name__)

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
    "https://searx.garudalinux.org"
]

@lru_cache(maxsize=256)
def search_images_cached(query, is_safe, size, time_range, page):
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
        params['size'] = size
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
                image_urls = []
                for result in data['results']:
                    if 'img_src' in result and result['img_src']:
                        image_urls.append(result['img_src'])
                if image_urls:
                    return image_urls
        except requests.exceptions.RequestException:
            continue
            
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_for_images():
    data = request.get_json()
    query = data.get('query')
    is_safe = data.get('safe_search', True)
    size = data.get('size', 'any')
    time_range = data.get('time_range', 'any')
    page = int(data.get('page', 1))

    if not query:
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400

    image_urls = search_images_cached(query, is_safe, size, time_range, page)
    
    if image_urls is None:
        json_response = jsonify({'success': False, 'error': 'Could not fetch results. All search providers are currently unavailable. Please try again later.'})
        response = make_response(json_response, 503)
    elif not image_urls:
        json_response = jsonify({'success': False, 'error': 'No more images found for this query.'})
        response = make_response(json_response, 404)
    else:
        json_response = jsonify({'success': True, 'images': image_urls})
        response = make_response(json_response, 200)

    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response