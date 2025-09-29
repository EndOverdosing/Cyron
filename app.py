import requests
import os
import io
import zipfile
from urllib.parse import urlparse
import time
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)

def download_image_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()
        
        parsed_url = urlparse(url)
        ext = os.path.splitext(parsed_url.path)[1]
        if not ext or ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            ext = '.jpg'
        
        return response.content, ext
    except Exception:
        return None, None

def search_images(query, num_images):
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
            'safesearch': '1',
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

@app.route('/download', methods=['POST'])
def download_images_zip():
    data = request.get_json()
    query = data.get('query')
    num_images = int(data.get('num_images', 10))

    if not query:
        return jsonify({'success': False, 'error': 'Search query cannot be empty.'}), 400

    image_urls = search_images(query, num_images)
    
    if not image_urls:
        return jsonify({'success': False, 'error': 'No images found. Try a different query.'}), 404

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, url in enumerate(image_urls):
            content, ext = download_image_content(url)
            if content:
                filename = f"image_{i+1:03d}{ext}"
                zf.writestr(filename, content)
            time.sleep(0.1)

    memory_file.seek(0)
    
    safe_query_name = "".join(c for c in query if c.isalnum() or c in (' ', '_')).rstrip()
    zip_filename = f"{safe_query_name.replace(' ', '_')}_images.zip"

    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )