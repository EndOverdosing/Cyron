import requests
import os
import time
from urllib.parse import urlparse
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

def search_images(query, num_images, is_safe):
    searx_url = "https://metasearx.com"
    search_url = f"{searx_url}/search"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    images = []
    page = 1
    
    while len(images) < num_images and page <= 5:
        params = {
            'q': query,
            'categories': 'images',
            'format': 'json',
            'safesearch': '1' if is_safe else '0',
            'pageno': page
        }
        
        try:
            response = requests.get(search_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'results' not in data or not data['results']:
                break
            
            for result in data['results']:
                if len(images) >= num_images:
                    break
                if 'img_src' in result and result['img_src']:
                    images.append(result['img_src'])
                elif 'content' in result and result['content'].startswith('http'):
                    images.append(result['content'])
            
            page += 1
            time.sleep(1)
            
        except Exception:
            break
    
    return images[:num_images]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_for_images():
    data = request.get_json()
    query = data.get('query')
    num_images = int(data.get('num_images', 10))
    is_safe = data.get('safe_search', True)

    if not query:
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400

    image_urls = search_images(query, num_images, is_safe)
    
    if not image_urls:
        return jsonify({'success': False, 'error': 'No images found. Try a different query.'}), 404

    return jsonify({'success': True, 'images': image_urls})