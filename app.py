import requests
import random
from flask import Flask, request, jsonify, make_response, Response
from flask_cors import CORS
from functools import lru_cache
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
from bs4 import BeautifulSoup

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

VALID_CATEGORIES = [
    "general", "images", "videos", "news", "music",
    "files", "social_media", "science", "it"
]

VALID_ENGINES = [
    "google", "bing", "duckduckgo", "brave", "yahoo",
    "startpage", "qwant", "wikipedia", "wikidata",
    "bing_images", "google_images", "flickr", "unsplash",
    "bing_videos", "google_videos", "youtube", "dailymotion", "vimeo",
    "bing_news", "google_news", "reuters", "bbc", "techcrunch",
    "soundcloud", "bandcamp", "mixcloud",
    "reddit", "twitter", "mastodon",
    "arxiv", "pubmed", "semantic_scholar",
    "github", "gitlab", "stackoverflow",
    "piratebay", "nyaa",
    "openstreetmap", "photon"
]

VALID_LANGUAGES = [
    "all", "en", "de", "fr", "es", "it", "pt", "nl", "pl", "ru",
    "zh", "ja", "ko", "ar", "hi", "tr", "vi", "th", "uk", "cs",
    "sv", "da", "fi", "no", "hu", "ro", "bg", "hr", "sk", "sl"
]

VALID_TIME_RANGES = ["", "day", "week", "month", "year"]
VALID_SAFESEARCH = [0, 1, 2]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
]


def make_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    })
    return session


def detect_result_type(article, categories):
    classes = ' '.join(article.get('class', []))
    data_template = article.get('data-result-template', '')

    if any(x in classes for x in ['result-images', 'result-image', 'image-result']):
        return 'images'
    if any(x in classes for x in ['result-videos', 'result-video', 'video-result']):
        return 'videos'
    if any(x in classes for x in ['result-news', 'news-result']):
        return 'news'
    if any(x in classes for x in ['result-files', 'files-result', 'torrent']):
        return 'files'
    if any(x in classes for x in ['result-music', 'music-result']):
        return 'music'
    if any(x in classes for x in ['result-social', 'social-result']):
        return 'social_media'
    if any(x in classes for x in ['result-science', 'science-result', 'paper-result']):
        return 'science'
    if any(x in classes for x in ['result-it', 'it-result', 'code-result']):
        return 'it'
    if 'images' in data_template:
        return 'images'
    if 'videos' in data_template:
        return 'videos'

    if categories:
        return categories[0]
    return 'general'


def extract_url(article, instance):
    for selector in ['h3 a', 'h4 a', '.result_header a', '.result-title a', 'a.result_title']:
        el = article.select_one(selector)
        if el and el.get('href'):
            href = el['href']
            if href.startswith('/'):
                href = instance + href
            if href.startswith('http'):
                return href

    for a in article.find_all('a', href=True):
        href = a['href']
        if href.startswith('/'):
            href = instance + href
        if href.startswith('http') and not any(x in href for x in ['searx', 'search.', 'metasearx']):
            return href

    return None


def extract_title(article):
    for selector in ['h3', 'h4', 'h2', '.result_header', '.result-title', '.title']:
        el = article.select_one(selector)
        if el:
            text = el.get_text(strip=True)
            if text:
                return text
    return None


def extract_content(article):
    for selector in [
        'p.result-content', 'p.content', 'div.result-content',
        '.result_content', '.description', 'p.description',
        'div.content', 'span.content', 'p'
    ]:
        el = article.select_one(selector)
        if el:
            text = el.get_text(strip=True)
            if len(text) > 20:
                return text
    return None


def extract_image(article, instance, result_type):
    img_src = None

    for attr in ['data-img-src', 'data-original', 'data-src', 'data-lazy-src', 'data-url']:
        val = article.get(attr, '')
        if val and val.startswith('http'):
            img_src = val
            break

    if not img_src:
        img_wrap = article.select_one('.result-images-source, .image_thumbnail, .thumbnail, .preview')
        if img_wrap:
            img = img_wrap.find('img')
            if img:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''
                if src.startswith('/'):
                    src = instance + src
                if src.startswith('http'):
                    img_src = src

    if not img_src:
        for img in article.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''
            if src.startswith('/'):
                src = instance + src
            if src.startswith('http') and not src.endswith('.svg'):
                img_src = src
                break

    return img_src


def extract_engines(article):
    engines = []
    for selector in ['.engines a', '.engine a', 'span.engine', '.badge', '.label']:
        for el in article.select(selector):
            text = el.get_text(strip=True)
            if text and len(text) < 30:
                engines.append(text)
    if not engines:
        engine_div = article.select_one('.engines, .engine-list, [data-engine]')
        if engine_div:
            raw = engine_div.get('data-engine') or engine_div.get_text(strip=True)
            engines = [e.strip() for e in raw.split(',') if e.strip()]
    return engines or None


def extract_date(article):
    for selector in ['time', '.date', '.publishedDate', '.result-pubdate', 'span.date']:
        el = article.select_one(selector)
        if el:
            dt = el.get('datetime') or el.get('title') or el.get_text(strip=True)
            if dt:
                return dt
    return None


def parse_html_results(html, instance, categories):
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    article_selectors = [
        'article.result',
        'div.result',
        '#results article',
        '#main_results article',
        '#main_results .result',
        '#results .result',
        '.results article',
        '.search-result',
        'li.result',
    ]

    articles = []
    for sel in article_selectors:
        found = soup.select(sel)
        if found:
            articles = found
            break

    for article in articles:
        result = {}

        result_type = detect_result_type(article, categories)
        result['type'] = result_type

        url = extract_url(article, instance)
        if url:
            result['url'] = url

        title = extract_title(article)
        if title:
            result['title'] = title

        content = extract_content(article)
        if content:
            result['content'] = content

        img = extract_image(article, instance, result_type)
        if img:
            if result_type == 'images':
                result['img_src'] = img
            else:
                result['thumbnail'] = img

        engines = extract_engines(article)
        if engines:
            result['engines'] = engines

        pub_date = extract_date(article)
        if pub_date:
            result['publishedDate'] = pub_date

        score_el = article.select_one('[data-score]')
        if score_el:
            try:
                result['score'] = float(score_el['data-score'])
            except (ValueError, TypeError):
                pass

        iframe = article.select_one('iframe')
        if iframe and iframe.get('src'):
            result['iframe_src'] = iframe['src']

        if result_type == 'videos':
            dur = article.select_one('.duration, [data-duration]')
            if dur:
                result['duration'] = dur.get('data-duration') or dur.get_text(strip=True)
            views = article.select_one('.views, [data-views]')
            if views:
                result['views'] = views.get_text(strip=True)

        if result_type == 'files':
            for attr_name, field in [('data-filesize', 'filesize'), ('data-file-size', 'filesize')]:
                val = article.get(attr_name)
                if val:
                    result[field] = val
            for sel, field in [('.seeds,.seeders', 'seed'), ('.leechs,.leechers', 'leech'), ('.magnet', 'magnet')]:
                el = article.select_one(sel)
                if el:
                    result[field] = el.get('href') or el.get_text(strip=True)

        if result_type == 'science':
            for sel, field in [('.authors,.author', 'authors'), ('.journal', 'journal'), ('.doi', 'doi'), ('.isbn', 'isbn')]:
                el = article.select_one(sel)
                if el:
                    result[field] = el.get('href') or el.get_text(strip=True)

        if result_type == 'music':
            for sel, field in [('.artist', 'artist'), ('.album', 'album'), ('.duration', 'duration')]:
                el = article.select_one(sel)
                if el:
                    result[field] = el.get_text(strip=True)

        if result_type == 'social_media':
            username = article.select_one('.username, .handle, .author')
            if username:
                result['username'] = username.get_text(strip=True)

        if 'url' in result or 'title' in result or 'img_src' in result:
            results.append(result)

    infobox_data = {}
    for ib_sel in ['div.infobox', '#infobox', '.knowledge-panel', '.answer-box']:
        infobox = soup.select_one(ib_sel)
        if infobox:
            h = infobox.select_one('h2, h3, h4')
            if h:
                infobox_data['title'] = h.get_text(strip=True)
            p = infobox.select_one('p')
            if p:
                infobox_data['content'] = p.get_text(strip=True)
            ib_img = infobox.select_one('img')
            if ib_img:
                src = ib_img.get('src', '')
                if src.startswith('/'):
                    src = instance + src
                infobox_data['img_src'] = src
            attrs = {}
            for row in infobox.select('tr, .attribute, .infobox-row, dt'):
                cells = row.find_all(['td', 'th', 'dd', 'span'])
                if len(cells) >= 2:
                    k = cells[0].get_text(strip=True)
                    v = cells[1].get_text(strip=True)
                    if k and v:
                        attrs[k] = v
            if attrs:
                infobox_data['attributes'] = attrs
            link = infobox.select_one('a[href]')
            if link:
                infobox_data['url'] = link['href']
            break

    suggestions = []
    for sug in soup.select('.suggestion a, .suggestions a, #suggestions a, [data-suggestion]'):
        t = sug.get_text(strip=True)
        if t and t not in suggestions:
            suggestions.append(t)

    corrections = []
    for cor in soup.select('.correction a, #correction a, .spell-check a'):
        t = cor.get_text(strip=True)
        if t and t not in corrections:
            corrections.append(t)

    answers = []
    for ans in soup.select('.answer, #answer, .direct-answer, .featured-snippet'):
        t = ans.get_text(strip=True)
        if t and len(t) > 5 and t not in answers:
            answers.append(t)

    return {
        'results': results,
        'infobox': infobox_data if infobox_data else None,
        'suggestions': suggestions,
        'corrections': corrections,
        'answers': answers
    }


def fetch_from_instance(instance, params, categories):
    try:
        session = make_session()
        resp = session.get(
            f"{instance}/search",
            params=params,
            timeout=10,
            allow_redirects=True
        )
        if resp.status_code in (429, 503, 403, 401, 302):
            return None
        if resp.status_code != 200:
            return None
        if len(resp.text) < 500:
            return None
        parsed = parse_html_results(resp.text, instance, categories)
        if parsed['results']:
            parsed['source'] = instance
            parsed['number_of_results'] = len(parsed['results'])
            return parsed
        return None
    except Exception:
        return None


@lru_cache(maxsize=512)
def execute_search(query, categories_str, engines_str, language, time_range,
                   safesearch, pageno):
    categories = [c.strip() for c in categories_str.split(',') if c.strip()] if categories_str else []
    engines = [e.strip() for e in engines_str.split(',') if e.strip()] if engines_str else []

    params = {
        'q': query,
        'pageno': pageno,
        'safesearch': safesearch
    }
    if categories:
        params['categories'] = ','.join(categories)
    if engines:
        params['engines'] = ','.join(engines)
    if language and language != 'all':
        params['language'] = language
    if time_range:
        params['time_range'] = time_range

    instances = random.sample(SEARX_INSTANCES, len(SEARX_INSTANCES))

    with ThreadPoolExecutor(max_workers=len(instances)) as executor:
        futures = {
            executor.submit(fetch_from_instance, inst, params, tuple(categories)): inst
            for inst in instances
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                return result

    return None


def validate_search_params(data):
    errors = []

    categories_raw = data.get('categories', '')
    if isinstance(categories_raw, list):
        categories_raw = ','.join(categories_raw)
    if categories_raw:
        for cat in categories_raw.split(','):
            cat = cat.strip()
            if cat and cat not in VALID_CATEGORIES:
                errors.append(f'Invalid category "{cat}". Valid: {", ".join(VALID_CATEGORIES)}')

    engines_raw = data.get('engines', '')
    if isinstance(engines_raw, list):
        engines_raw = ','.join(engines_raw)

    language = data.get('language', 'all')
    if language not in VALID_LANGUAGES:
        errors.append(f'Invalid language "{language}". Valid: {", ".join(VALID_LANGUAGES)}')

    time_range = data.get('time_range', '')
    if time_range not in VALID_TIME_RANGES:
        errors.append(f'Invalid time_range "{time_range}". Valid: day, week, month, year (or empty)')

    safesearch = data.get('safesearch', 1)
    try:
        safesearch = int(safesearch)
        if safesearch not in VALID_SAFESEARCH:
            errors.append(f'Invalid safesearch value. Valid: 0 (off), 1 (moderate), 2 (strict)')
    except (ValueError, TypeError):
        errors.append('safesearch must be 0, 1, or 2')
        safesearch = 1

    pageno = data.get('pageno', 1)
    try:
        pageno = int(pageno)
        if pageno < 1:
            pageno = 1
    except (ValueError, TypeError):
        errors.append('pageno must be a positive integer')
        pageno = 1

    per_page = data.get('per_page', None)
    if per_page is not None:
        try:
            per_page = int(per_page)
            if per_page < 1 or per_page > 100:
                errors.append('per_page must be between 1 and 100')
        except (ValueError, TypeError):
            errors.append('per_page must be a valid integer')
            per_page = None

    return {
        'errors': errors,
        'categories_str': categories_raw,
        'engines_str': engines_raw,
        'language': language,
        'time_range': time_range,
        'safesearch': safesearch,
        'pageno': pageno,
        'per_page': per_page
    }


def build_result_response(raw, query, params, per_page):
    results = raw.get('results', [])
    total = len(results)

    if per_page is not None:
        displayed = results[:per_page]
    else:
        displayed = results

    by_type = {}
    for r in displayed:
        t = r.get('type') or r.get('category', 'general')
        by_type.setdefault(t, []).append(r)

    return {
        'success': True,
        'query': query,
        'params': {
            'categories': params['categories_str'] or 'general',
            'engines': params['engines_str'] or 'auto',
            'language': params['language'],
            'time_range': params['time_range'] or 'any',
            'safesearch': params['safesearch'],
            'pageno': params['pageno'],
            'per_page': per_page
        },
        'meta': {
            'source_instance': raw.get('source', 'unknown'),
            'number_of_results': raw.get('number_of_results', total),
            'total_returned': total,
            'displayed': len(displayed)
        },
        'answers': raw.get('answers', []),
        'infobox': raw.get('infobox'),
        'suggestions': raw.get('suggestions', []),
        'corrections': raw.get('corrections', []),
        'results': {
            'all': displayed,
            'by_type': by_type
        },
        'pagination': {
            'current_page': params['pageno'],
            'per_page': per_page if per_page is not None else total,
            'total_on_page': total,
            'returned': len(displayed),
            'has_next': True,
            'next_page': params['pageno'] + 1
        }
    }


def stream_search(query, params, per_page):
    raw = execute_search(
        query,
        params['categories_str'],
        params['engines_str'],
        params['language'],
        params['time_range'],
        params['safesearch'],
        params['pageno']
    )

    if raw is None:
        yield f"data: {json.dumps({'success': False, 'error': 'All search providers are currently unavailable.'})}\n\n"
        return

    results = raw.get('results', [])
    if per_page is not None:
        results = results[:per_page]

    meta = {
        'type': 'meta',
        'success': True,
        'query': query,
        'answers': raw.get('answers', []),
        'infobox': raw.get('infobox'),
        'suggestions': raw.get('suggestions', []),
        'corrections': raw.get('corrections', []),
        'total_count': len(results),
        'source': raw.get('source', 'unknown')
    }
    yield f"data: {json.dumps(meta)}\n\n"

    for i, result in enumerate(results):
        yield f"data: {json.dumps({'type': 'result', 'index': i, 'data': result})}\n\n"
        time.sleep(0.05)

    yield f"data: {json.dumps({'type': 'complete', 'total_sent': len(results)})}\n\n"


@app.route('/', methods=['GET'])
def docs():
    return jsonify({
        'name': 'Cyron Search API',
        'version': '3.0',
        'description': 'Privacy-focused meta search engine API powered by SearX. Returns web, images, videos, news, files, music, social media, science, and IT results.',
        'endpoints': {
            '/': {'method': 'GET', 'description': 'API documentation'},
            '/search': {
                'method': 'POST',
                'description': 'Full search with JSON body',
                'body': {
                    'query': 'string (required)',
                    'categories': 'string or array: general, images, videos, news, music, files, social_media, science, it',
                    'engines': 'string or array of specific engines',
                    'language': 'language code e.g. en, de, fr (default: all)',
                    'time_range': 'day, week, month, year (default: any)',
                    'safesearch': '0=off, 1=moderate, 2=strict (default: 1)',
                    'pageno': 'integer (default: 1)',
                    'per_page': 'integer 1-100 (default: all)',
                }
            },
            '/search/<query>': {
                'method': 'GET',
                'description': 'Search via URL path',
                'params': 'categories, engines, language, time_range, safesearch, pageno, per_page, stream'
            },
            '/search/stream': {
                'method': 'POST',
                'description': 'Streaming search via Server-Sent Events',
                'response_type': 'text/event-stream'
            },
            '/categories': {'method': 'GET', 'description': 'List all categories'},
            '/engines': {'method': 'GET', 'description': 'List all engines'},
            '/languages': {'method': 'GET', 'description': 'List all supported languages'},
            '/examples': {'method': 'GET', 'description': 'Example queries'},
            '/health': {'method': 'GET', 'description': 'Health check'},
            '/stats': {'method': 'GET', 'description': 'Cache and provider statistics'}
        },
        'quick_start': {
            'web_search': '/search/artificial intelligence?categories=general&per_page=10',
            'image_search': '/search/mountains?categories=images&per_page=20',
            'video_search': '/search/tutorials?categories=videos',
            'news_search': '/search/technology?categories=news&time_range=day',
            'multi_category': '/search/python?categories=general,science,it',
            'curl_post': 'curl -X POST /search -H "Content-Type: application/json" -d \'{"query":"AI","categories":"general","language":"en","per_page":20}\'',
            'streaming': '/search/news?categories=news&stream=true'
        }
    })


@app.route('/categories', methods=['GET'])
def list_categories():
    return jsonify({
        'success': True,
        'categories': [
            {'name': 'general', 'description': 'Web search results'},
            {'name': 'images', 'description': 'Image search results with img_src and thumbnails'},
            {'name': 'videos', 'description': 'Video results with iframe_src and duration'},
            {'name': 'news', 'description': 'News articles with publishedDate'},
            {'name': 'music', 'description': 'Music tracks with artist and album'},
            {'name': 'files', 'description': 'File and torrent results with filesize, seed, leech'},
            {'name': 'social_media', 'description': 'Social media posts and profiles'},
            {'name': 'science', 'description': 'Academic papers with authors, journal, doi'},
            {'name': 'it', 'description': 'IT resources, code, repositories'}
        ]
    })


@app.route('/engines', methods=['GET'])
def list_engines():
    category_filter = request.args.get('category', '')
    engine_map = {
        'general': ['google', 'bing', 'duckduckgo', 'brave', 'yahoo', 'startpage', 'qwant', 'wikipedia', 'wikidata', 'openstreetmap'],
        'images': ['bing_images', 'google_images', 'flickr', 'unsplash'],
        'videos': ['bing_videos', 'google_videos', 'youtube', 'dailymotion', 'vimeo'],
        'news': ['bing_news', 'google_news', 'reuters', 'bbc', 'techcrunch'],
        'music': ['soundcloud', 'bandcamp', 'mixcloud'],
        'files': ['piratebay', 'nyaa'],
        'social_media': ['reddit', 'twitter', 'mastodon'],
        'science': ['arxiv', 'pubmed', 'semantic_scholar'],
        'it': ['github', 'gitlab', 'stackoverflow']
    }

    if category_filter and category_filter in engine_map:
        return jsonify({
            'success': True,
            'category': category_filter,
            'engines': engine_map[category_filter]
        })

    return jsonify({
        'success': True,
        'engines_by_category': engine_map,
        'all_engines': VALID_ENGINES
    })


@app.route('/languages', methods=['GET'])
def list_languages():
    language_names = {
        'all': 'All languages', 'en': 'English', 'de': 'German', 'fr': 'French',
        'es': 'Spanish', 'it': 'Italian', 'pt': 'Portuguese', 'nl': 'Dutch',
        'pl': 'Polish', 'ru': 'Russian', 'zh': 'Chinese', 'ja': 'Japanese',
        'ko': 'Korean', 'ar': 'Arabic', 'hi': 'Hindi', 'tr': 'Turkish',
        'vi': 'Vietnamese', 'th': 'Thai', 'uk': 'Ukrainian', 'cs': 'Czech',
        'sv': 'Swedish', 'da': 'Danish', 'fi': 'Finnish', 'no': 'Norwegian',
        'hu': 'Hungarian', 'ro': 'Romanian', 'bg': 'Bulgarian', 'hr': 'Croatian',
        'sk': 'Slovak', 'sl': 'Slovenian'
    }
    return jsonify({
        'success': True,
        'languages': [{'code': code, 'name': name} for code, name in language_names.items()]
    })


@app.route('/examples', methods=['GET'])
def get_examples():
    return jsonify({
        'success': True,
        'examples': [
            {
                'category': 'General Web Search',
                'queries': [
                    {'name': 'Basic web search', 'url': '/search/python programming?per_page=10', 'post': {'query': 'python programming', 'per_page': 10}},
                    {'name': 'Filtered language', 'url': '/search/news?language=en&per_page=20', 'post': {'query': 'news', 'language': 'en', 'per_page': 20}},
                    {'name': 'Recent results', 'url': '/search/AI models?time_range=week&per_page=15', 'post': {'query': 'AI models', 'time_range': 'week', 'per_page': 15}}
                ]
            },
            {
                'category': 'Images',
                'queries': [
                    {'name': 'Image search', 'url': '/search/mountains?categories=images&per_page=20', 'post': {'query': 'mountains', 'categories': 'images', 'per_page': 20}},
                    {'name': 'Recent images', 'url': '/search/aurora borealis?categories=images&time_range=month', 'post': {'query': 'aurora borealis', 'categories': 'images', 'time_range': 'month'}},
                    {'name': 'Specific engine', 'url': '/search/architecture?categories=images&engines=flickr', 'post': {'query': 'architecture', 'categories': 'images', 'engines': 'flickr'}}
                ]
            },
            {
                'category': 'Videos',
                'queries': [
                    {'name': 'Video search', 'url': '/search/cooking tutorials?categories=videos&per_page=10', 'post': {'query': 'cooking tutorials', 'categories': 'videos', 'per_page': 10}},
                    {'name': 'YouTube only', 'url': '/search/music?categories=videos&engines=youtube', 'post': {'query': 'music', 'categories': 'videos', 'engines': 'youtube'}},
                    {'name': 'Recent videos', 'url': '/search/news?categories=videos&time_range=day', 'post': {'query': 'news', 'categories': 'videos', 'time_range': 'day'}}
                ]
            },
            {
                'category': 'News',
                'queries': [
                    {'name': 'Latest news', 'url': '/search/technology?categories=news&time_range=day', 'post': {'query': 'technology', 'categories': 'news', 'time_range': 'day'}},
                    {'name': 'Weekly news', 'url': '/search/climate?categories=news&time_range=week', 'post': {'query': 'climate', 'categories': 'news', 'time_range': 'week'}},
                    {'name': 'Safe news', 'url': '/search/finance?categories=news&safesearch=2', 'post': {'query': 'finance', 'categories': 'news', 'safesearch': 2}}
                ]
            },
            {
                'category': 'Science & Academic',
                'queries': [
                    {'name': 'Academic papers', 'url': '/search/neural networks?categories=science', 'post': {'query': 'neural networks', 'categories': 'science'}},
                    {'name': 'PubMed only', 'url': '/search/cancer treatment?categories=science&engines=pubmed', 'post': {'query': 'cancer treatment', 'categories': 'science', 'engines': 'pubmed'}},
                    {'name': 'ArXiv only', 'url': '/search/quantum computing?engines=arxiv', 'post': {'query': 'quantum computing', 'engines': 'arxiv'}}
                ]
            },
            {
                'category': 'IT & Code',
                'queries': [
                    {'name': 'GitHub repos', 'url': '/search/react components?categories=it&engines=github', 'post': {'query': 'react components', 'categories': 'it', 'engines': 'github'}},
                    {'name': 'Stack Overflow', 'url': '/search/async await javascript?engines=stackoverflow', 'post': {'query': 'async await javascript', 'engines': 'stackoverflow'}},
                    {'name': 'General IT', 'url': '/search/docker deployment?categories=it', 'post': {'query': 'docker deployment', 'categories': 'it'}}
                ]
            },
            {
                'category': 'Multi-Category',
                'queries': [
                    {'name': 'Web and news', 'url': '/search/OpenAI?categories=general,news', 'post': {'query': 'OpenAI', 'categories': ['general', 'news']}},
                    {'name': 'Images and videos', 'url': '/search/sunset?categories=images,videos', 'post': {'query': 'sunset', 'categories': ['images', 'videos']}},
                    {'name': 'All categories', 'url': '/search/python?categories=general,science,it,news', 'post': {'query': 'python', 'categories': ['general', 'science', 'it', 'news']}}
                ]
            },
            {
                'category': 'Streaming',
                'queries': [
                    {'name': 'Stream web results', 'url': '/search/space exploration?stream=true', 'post_endpoint': '/search/stream', 'post': {'query': 'space exploration'}},
                    {'name': 'Stream images', 'url': '/search/galaxies?categories=images&stream=true', 'post_endpoint': '/search/stream', 'post': {'query': 'galaxies', 'categories': 'images'}}
                ]
            }
        ]
    })


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Cyron Search API',
        'version': '3.0',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'providers': {
            'total': len(SEARX_INSTANCES),
            'instances': SEARX_INSTANCES,
            'status': 'operational'
        },
        'supported': {
            'categories': VALID_CATEGORIES,
            'time_ranges': VALID_TIME_RANGES,
            'safesearch_levels': VALID_SAFESEARCH,
            'languages': len(VALID_LANGUAGES),
            'engines': len(VALID_ENGINES)
        },
        'features': {
            'cache_enabled': True,
            'cors_enabled': True,
            'streaming': True,
            'flexible_pagination': True,
            'infobox': True,
            'suggestions': True,
            'answers': True,
            'multi_category': True,
            'engine_selection': True
        }
    })


@app.route('/stats', methods=['GET'])
def get_stats():
    cache_info = execute_search.cache_info()
    total = cache_info.hits + cache_info.misses
    hit_rate = (cache_info.hits / total * 100) if total > 0 else 0

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
            'failover': 'automatic',
            'timeout_seconds': 15
        },
        'api': {
            'version': '3.0',
            'categories': len(VALID_CATEGORIES),
            'engines': len(VALID_ENGINES),
            'languages': len(VALID_LANGUAGES),
            'max_per_page': 100
        }
    })


@app.route('/search/stream', methods=['POST'])
def search_stream():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON body'}), 400

    query = data.get('query', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'query is required'}), 400

    validated = validate_search_params(data)
    if validated['errors']:
        return jsonify({'success': False, 'errors': validated['errors']}), 400

    per_page = validated['per_page']

    return Response(
        stream_search(query, validated, per_page),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@app.route('/search', methods=['POST'])
def search_post():
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'error': 'Invalid JSON body',
            'example': {
                'query': 'artificial intelligence',
                'categories': 'general',
                'language': 'en',
                'time_range': 'week',
                'safesearch': 1,
                'pageno': 1,
                'per_page': 20
            }
        }), 400

    query = data.get('query', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'query is required'}), 400

    validated = validate_search_params(data)
    if validated['errors']:
        return jsonify({'success': False, 'errors': validated['errors']}), 400

    raw = execute_search(
        query,
        validated['categories_str'],
        validated['engines_str'],
        validated['language'],
        validated['time_range'],
        validated['safesearch'],
        validated['pageno']
    )

    if raw is None:
        resp = make_response(jsonify({
            'success': False,
            'error': 'All search providers are currently unavailable.',
            'providers_attempted': len(SEARX_INSTANCES)
        }), 503)
        return resp

    if not raw.get('results'):
        resp = make_response(jsonify({
            'success': False,
            'error': 'No results found for this query.',
            'query': query,
            'suggestions': raw.get('suggestions', []),
            'corrections': raw.get('corrections', [])
        }), 404)
        return resp

    payload = build_result_response(raw, query, validated, validated['per_page'])
    resp = make_response(jsonify(payload), 200)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/search/<path:query>', methods=['GET'])
def search_get(query):
    query = query.strip()
    if not query:
        return jsonify({'success': False, 'error': 'query cannot be empty'}), 400

    data = {
        'categories': request.args.get('categories', ''),
        'engines': request.args.get('engines', ''),
        'language': request.args.get('language', 'all'),
        'time_range': request.args.get('time_range', ''),
        'safesearch': request.args.get('safesearch', 1),
        'pageno': request.args.get('pageno', 1),
        'per_page': request.args.get('per_page', None)
    }

    stream_mode = request.args.get('stream', 'false').lower() == 'true'

    validated = validate_search_params(data)
    if validated['errors']:
        return jsonify({'success': False, 'errors': validated['errors']}), 400

    if stream_mode:
        return Response(
            stream_search(query, validated, validated['per_page']),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )

    raw = execute_search(
        query,
        validated['categories_str'],
        validated['engines_str'],
        validated['language'],
        validated['time_range'],
        validated['safesearch'],
        validated['pageno']
    )

    if raw is None:
        return jsonify({
            'success': False,
            'error': 'All search providers are currently unavailable.',
            'providers_attempted': len(SEARX_INSTANCES)
        }), 503

    if not raw.get('results'):
        return jsonify({
            'success': False,
            'error': 'No results found.',
            'query': query,
            'suggestions': raw.get('suggestions', []),
            'corrections': raw.get('corrections', [])
        }), 404

    payload = build_result_response(raw, query, validated, validated['per_page'])
    resp = make_response(jsonify(payload), 200)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/debug', methods=['GET', 'POST'])
def debug_search():
    if request.method == 'POST':
        data = request.get_json() or {}
        query = data.get('query', 'test')
    else:
        query = request.args.get('q', 'test')

    results_per_instance = []
    shuffled = random.sample(SEARX_INSTANCES, min(3, len(SEARX_INSTANCES)))

    for instance in shuffled:
        entry = {'instance': instance, 'status': None, 'html_length': 0, 'article_count': 0, 'error': None}
        try:
            session = make_session()
            resp = session.get(f"{instance}/search", params={'q': query, 'categories': 'general'}, timeout=15)
            entry['status'] = resp.status_code
            entry['html_length'] = len(resp.text)
            entry['content_type'] = resp.headers.get('Content-Type', '')

            soup = BeautifulSoup(resp.text, 'html.parser')
            articles = soup.select('article.result, div.result, .search-result, li.result')
            entry['article_count'] = len(articles)

            if articles:
                first = articles[0]
                entry['first_article_classes'] = first.get('class', [])
                entry['first_article_html_preview'] = str(first)[:500]

            entry['page_title'] = soup.title.get_text(strip=True) if soup.title else None

            all_articles_by_selector = {}
            for sel in ['article.result', 'div.result', '#results article', '#main_results .result', '.search-result']:
                count = len(soup.select(sel))
                if count:
                    all_articles_by_selector[sel] = count
            entry['selectors_found'] = all_articles_by_selector

        except Exception as e:
            entry['error'] = str(e)

        results_per_instance.append(entry)

    return jsonify({
        'success': True,
        'query': query,
        'instances_tested': len(shuffled),
        'debug': results_per_instance
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': ['/', '/search (POST)', '/search/<query> (GET)', '/search/stream (POST)', '/categories', '/engines', '/languages', '/examples', '/health', '/stats']
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