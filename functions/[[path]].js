const SEARX_INSTANCES = [
    "https://searx.be",
    "https://search.disroot.org",
    "https://searx.work",
    "https://search.projectsegfau.lt",
    "https://searx.prvcy.eu",
    "https://searx.tiekoetter.com",
    "https://search.ononoki.org",
    "https://searx.si",
    "https://searx.garudalinux.org",
    "https://metasearx.com",
];

const VALID_CATEGORIES = ["general", "images", "videos", "news", "music", "files", "social_media", "science", "it"];
const VALID_TIME_RANGES = ["", "day", "week", "month", "year"];
const VALID_SAFESEARCH = [0, 1, 2];
const VALID_LANGUAGES = ["all", "en", "de", "fr", "es", "it", "pt", "nl", "pl", "ru", "zh", "ja", "ko", "ar", "hi", "tr", "vi", "th", "uk", "cs", "sv", "da", "fi", "no", "hu", "ro", "bg", "hr", "sk", "sl"];

const USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
];

const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000;

function getCacheKey(query, cats, engines, lang, timeRange, safesearch, pageno) {
    return `${query}|${cats}|${engines}|${lang}|${timeRange}|${safesearch}|${pageno}`;
}

function cacheGet(key) {
    const entry = cache.get(key);
    if (!entry) return null;
    if (Date.now() - entry.ts > CACHE_TTL) { cache.delete(key); return null; }
    return entry.value;
}

function cacheSet(key, value) {
    if (cache.size > 512) {
        const oldest = cache.keys().next().value;
        cache.delete(oldest);
    }
    cache.set(key, { value, ts: Date.now() });
}

function randomUA() {
    return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

function shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

function extractText(el) {
    if (!el) return null;
    return el.textContent?.trim() || null;
}

function resolveUrl(href, instance) {
    if (!href) return null;
    if (href.startsWith("http")) return href;
    if (href.startsWith("/")) return instance + href;
    return null;
}

function parseResults(html, instance, categories) {
    const results = [];
    const infobox = {};
    const suggestions = [];
    const corrections = [];
    const answers = [];

    const articleRegex = /<article[^>]*class="[^"]*result[^"]*"[^>]*>([\s\S]*?)<\/article>/gi;
    const divResultRegex = /<div[^>]*class="[^"]*\bresult\b[^"]*"[^>]*>([\s\S]*?)<\/div>/gi;

    function extractAttr(html, tag, attr) {
        const re = new RegExp(`<${tag}[^>]*\\s${attr}="([^"]*)"`, 'i');
        const m = html.match(re);
        return m ? m[1] : null;
    }

    function extractInnerText(html, selector) {
        const tagMatch = selector.match(/^(\w+)/);
        const classMatch = selector.match(/\.([^\s.]+)/);
        const idMatch = selector.match(/#([^\s]+)/);
        let pattern;
        if (idMatch) {
            pattern = new RegExp(`id="${idMatch[1]}"[^>]*>([\\s\\S]*?)<\\/`, 'i');
        } else if (classMatch && tagMatch) {
            pattern = new RegExp(`<${tagMatch[1]}[^>]*class="[^"]*${classMatch[1]}[^"]*"[^>]*>([\\s\\S]*?)<\\/${tagMatch[1]}>`, 'i');
        } else if (classMatch) {
            pattern = new RegExp(`class="[^"]*${classMatch[1]}[^"]*"[^>]*>([\\s\\S]*?)<\/`, 'i');
        } else if (tagMatch) {
            pattern = new RegExp(`<${tagMatch[1]}[^>]*>([\\s\\S]*?)<\\/${tagMatch[1]}>`, 'i');
        }
        if (!pattern) return null;
        const m = html.match(pattern);
        if (!m) return null;
        return m[1].replace(/<[^>]+>/g, '').trim() || null;
    }

    function parseArticle(articleHtml) {
        const result = {};

        const classMatch = articleHtml.match(/<article[^>]*class="([^"]*)"/i) ||
            articleHtml.match(/<div[^>]*class="([^"]*)"/i);
        const classes = classMatch ? classMatch[1] : '';

        if (/result-images|result-image|image-result/.test(classes)) result.type = 'images';
        else if (/result-videos|result-video|video-result/.test(classes)) result.type = 'videos';
        else if (/result-news|news-result/.test(classes)) result.type = 'news';
        else if (/result-files|files-result|torrent/.test(classes)) result.type = 'files';
        else if (/result-music|music-result/.test(classes)) result.type = 'music';
        else if (/result-social|social-result/.test(classes)) result.type = 'social_media';
        else if (/result-science|science-result|paper-result/.test(classes)) result.type = 'science';
        else if (/result-it|it-result|code-result/.test(classes)) result.type = 'it';
        else result.type = (categories && categories[0]) || 'general';

        const hrefMatch = articleHtml.match(/<h[234][^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>/i) ||
            articleHtml.match(/<a[^>]*href="(https?[^"]+)"[^>]*class="[^"]*result[^"]*"/i) ||
            articleHtml.match(/<a[^>]*href="(https?[^"]+)"/i);
        if (hrefMatch) {
            const href = hrefMatch[1];
            if (href.startsWith('http') && !/(searx|search\.|metasearx)/.test(href)) {
                result.url = href;
            }
        }

        const titleMatch = articleHtml.match(/<h[234][^>]*>(?:<a[^>]*>)?([^<]+)/i);
        if (titleMatch) result.title = titleMatch[1].trim();

        const contentSelectors = [
            /class="[^"]*(?:result-content|content|description)[^"]*"[^>]*>([\s\S]{20,500}?)<\//i,
            /<p[^>]*>([\s\S]{20,500}?)<\/p>/i,
        ];
        for (const re of contentSelectors) {
            const m = articleHtml.match(re);
            if (m) {
                const text = m[1].replace(/<[^>]+>/g, '').trim();
                if (text.length > 20) { result.content = text; break; }
            }
        }

        const imgSrcMatch = articleHtml.match(/data-img-src="(https?[^"]+)"/i) ||
            articleHtml.match(/data-original="(https?[^"]+)"/i) ||
            articleHtml.match(/data-src="(https?[^"]+)"/i);
        if (imgSrcMatch) {
            if (result.type === 'images') result.img_src = imgSrcMatch[1];
            else result.thumbnail = imgSrcMatch[1];
        } else {
            const imgTagMatch = articleHtml.match(/<img[^>]*src="(https?[^"]+(?:jpg|jpeg|png|webp|gif)[^"]*)"[^>]*>/i);
            if (imgTagMatch) {
                if (result.type === 'images') result.img_src = imgTagMatch[1];
                else result.thumbnail = imgTagMatch[1];
            }
        }

        const dateMatch = articleHtml.match(/<time[^>]*datetime="([^"]+)"/i) ||
            articleHtml.match(/class="[^"]*(?:date|publishedDate)[^"]*"[^>]*>([^<]{6,30})</i);
        if (dateMatch) result.publishedDate = dateMatch[1].trim();

        const enginesMatch = articleHtml.match(/class="[^"]*engines[^"]*"[^>]*>([\s\S]*?)<\/(?:div|span|p)>/i);
        if (enginesMatch) {
            const engineText = enginesMatch[1].replace(/<[^>]+>/g, ',').split(',').map(s => s.trim()).filter(Boolean);
            if (engineText.length) result.engines = engineText;
        }

        if (result.type === 'videos') {
            const durMatch = articleHtml.match(/class="[^"]*duration[^"]*"[^>]*>([^<]+)</i);
            if (durMatch) result.duration = durMatch[1].trim();
            const iframeMatch = articleHtml.match(/<iframe[^>]*src="([^"]+)"/i);
            if (iframeMatch) result.iframe_src = iframeMatch[1];
        }

        if (result.type === 'files') {
            const fsMatch = articleHtml.match(/data-filesize="([^"]+)"/i);
            if (fsMatch) result.filesize = fsMatch[1];
            const seedMatch = articleHtml.match(/class="[^"]*seeds?[^"]*"[^>]*>([^<]+)</i);
            if (seedMatch) result.seed = seedMatch[1].trim();
            const leechMatch = articleHtml.match(/class="[^"]*leech[^"]*"[^>]*>([^<]+)</i);
            if (leechMatch) result.leech = leechMatch[1].trim();
            const magnetMatch = articleHtml.match(/href="(magnet:[^"]+)"/i);
            if (magnetMatch) result.magnet = magnetMatch[1];
        }

        if (result.type === 'science') {
            const authMatch = articleHtml.match(/class="[^"]*authors?[^"]*"[^>]*>([^<]+)</i);
            if (authMatch) result.authors = authMatch[1].trim();
            const journalMatch = articleHtml.match(/class="[^"]*journal[^"]*"[^>]*>([^<]+)</i);
            if (journalMatch) result.journal = journalMatch[1].trim();
            const doiMatch = articleHtml.match(/class="[^"]*doi[^"]*"[^>]*>([^<]+)</i);
            if (doiMatch) result.doi = doiMatch[1].trim();
        }

        if (result.type === 'music') {
            const artistMatch = articleHtml.match(/class="[^"]*artist[^"]*"[^>]*>([^<]+)</i);
            if (artistMatch) result.artist = artistMatch[1].trim();
            const albumMatch = articleHtml.match(/class="[^"]*album[^"]*"[^>]*>([^<]+)</i);
            if (albumMatch) result.album = albumMatch[1].trim();
        }

        if (result.type === 'social_media') {
            const userMatch = articleHtml.match(/class="[^"]*(?:username|handle|author)[^"]*"[^>]*>([^<]+)</i);
            if (userMatch) result.username = userMatch[1].trim();
        }

        return (result.url || result.title || result.img_src) ? result : null;
    }

    let matches = [...html.matchAll(/<article[^>]*class="[^"]*result[^"]*"[\s\S]*?<\/article>/gi)];

    if (!matches.length) {
        const divPattern = /<div[^>]*class="[^"]*\bresult\b[^"]*"[^>]*>[\s\S]{50,2000}?(?=<div[^>]*class="[^"]*\bresult\b|$)/gi;
        matches = [...html.matchAll(divPattern)];
    }

    for (const m of matches) {
        const parsed = parseArticle(m[0]);
        if (parsed) results.push(parsed);
    }

    const infoboxMatch = html.match(/<div[^>]*(?:class="[^"]*infobox[^"]*"|id="infobox")[^>]*>([\s\S]*?)<\/div>/i);
    if (infoboxMatch) {
        const ibHtml = infoboxMatch[1];
        const ibTitle = ibHtml.match(/<h[234][^>]*>([^<]+)</i);
        if (ibTitle) infobox.title = ibTitle[1].trim();
        const ibDesc = ibHtml.match(/<p[^>]*>([\s\S]{10,500}?)<\/p>/i);
        if (ibDesc) infobox.content = ibDesc[1].replace(/<[^>]+>/g, '').trim();
    }

    const sugPattern = /class="[^"]*suggestion[^"]*"[^>]*>[\s\S]*?<a[^>]*>([^<]+)<\/a>/gi;
    for (const m of html.matchAll(sugPattern)) {
        const s = m[1].trim();
        if (s && !suggestions.includes(s)) suggestions.push(s);
    }

    const ansPattern = /class="[^"]*(?:answer|direct-answer|featured-snippet)[^"]*"[^>]*>([\s\S]{5,500}?)<\/(?:div|p|span)>/gi;
    for (const m of html.matchAll(ansPattern)) {
        const a = m[1].replace(/<[^>]+>/g, '').trim();
        if (a.length > 5 && !answers.includes(a)) answers.push(a);
    }

    return { results, infobox: Object.keys(infobox).length ? infobox : null, suggestions, corrections, answers };
}

async function fetchFromInstance(instance, params) {
    const url = new URL(`${instance}/search`);
    for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v));
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 9000);

    try {
        const resp = await fetch(url.toString(), {
            signal: controller.signal,
            headers: {
                'User-Agent': randomUA(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'DNT': '1',
            },
            redirect: 'follow',
        });

        clearTimeout(timer);

        if (!resp.ok) return null;
        const html = await resp.text();
        if (html.length < 500) return null;

        const categories = params.categories ? params.categories.split(',') : [];
        const parsed = parseResults(html, instance, categories);
        if (!parsed.results.length) return null;
        return { ...parsed, source: instance, number_of_results: parsed.results.length };
    } catch {
        clearTimeout(timer);
        return null;
    }
}

async function executeSearch(query, categoriesStr, enginesStr, language, timeRange, safesearch, pageno) {
    const cacheKey = getCacheKey(query, categoriesStr, enginesStr, language, timeRange, safesearch, pageno);
    const cached = cacheGet(cacheKey);
    if (cached) return cached;

    const params = { q: query, pageno, safesearch };
    if (categoriesStr) params.categories = categoriesStr;
    if (enginesStr) params.engines = enginesStr;
    if (language && language !== 'all') params.language = language;
    if (timeRange) params.time_range = timeRange;

    const instances = shuffle(SEARX_INSTANCES);

    const result = await new Promise((resolve) => {
        let resolved = false;
        let pending = instances.length;

        for (const instance of instances) {
            fetchFromInstance(instance, params).then((res) => {
                pending--;
                if (res && !resolved) {
                    resolved = true;
                    resolve(res);
                } else if (pending === 0 && !resolved) {
                    resolve(null);
                }
            }).catch(() => {
                pending--;
                if (pending === 0 && !resolved) resolve(null);
            });
        }
    });

    if (result) cacheSet(cacheKey, result);
    return result;
}

function validateParams(data) {
    const errors = [];

    let categoriesStr = data.categories || '';
    if (Array.isArray(categoriesStr)) categoriesStr = categoriesStr.join(',');
    for (const cat of categoriesStr.split(',').map(s => s.trim()).filter(Boolean)) {
        if (!VALID_CATEGORIES.includes(cat)) errors.push(`Invalid category "${cat}". Valid: ${VALID_CATEGORIES.join(', ')}`);
    }

    let enginesStr = data.engines || '';
    if (Array.isArray(enginesStr)) enginesStr = enginesStr.join(',');

    const language = data.language || 'all';
    if (!VALID_LANGUAGES.includes(language)) errors.push(`Invalid language "${language}"`);

    const timeRange = data.time_range || '';
    if (!VALID_TIME_RANGES.includes(timeRange)) errors.push(`Invalid time_range "${timeRange}". Valid: day, week, month, year`);

    let safesearch = parseInt(data.safesearch ?? 1, 10);
    if (isNaN(safesearch) || !VALID_SAFESEARCH.includes(safesearch)) { errors.push('safesearch must be 0, 1, or 2'); safesearch = 1; }

    let pageno = parseInt(data.pageno ?? 1, 10);
    if (isNaN(pageno) || pageno < 1) pageno = 1;

    let perPage = data.per_page != null ? parseInt(data.per_page, 10) : null;
    if (perPage !== null && (isNaN(perPage) || perPage < 1 || perPage > 100)) {
        errors.push('per_page must be between 1 and 100'); perPage = null;
    }

    return { errors, categoriesStr, enginesStr, language, timeRange, safesearch, pageno, perPage };
}

function buildResponse(raw, query, params, perPage) {
    const all = perPage != null ? raw.results.slice(0, perPage) : raw.results;
    const byType = {};
    for (const r of all) {
        const t = r.type || 'general';
        if (!byType[t]) byType[t] = [];
        byType[t].push(r);
    }
    return {
        success: true,
        query,
        params: {
            categories: params.categoriesStr || 'general',
            engines: params.enginesStr || 'auto',
            language: params.language,
            time_range: params.timeRange || 'any',
            safesearch: params.safesearch,
            pageno: params.pageno,
            per_page: perPage,
        },
        meta: {
            source_instance: raw.source || 'unknown',
            number_of_results: raw.number_of_results || all.length,
            total_returned: raw.results.length,
            displayed: all.length,
        },
        answers: raw.answers || [],
        infobox: raw.infobox || null,
        suggestions: raw.suggestions || [],
        corrections: raw.corrections || [],
        results: { all, by_type: byType },
        pagination: {
            current_page: params.pageno,
            per_page: perPage ?? all.length,
            total_on_page: raw.results.length,
            returned: all.length,
            has_next: true,
            next_page: params.pageno + 1,
        },
    };
}

function json(data, status = 200) {
    return new Response(JSON.stringify(data), {
        status,
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Cache-Control': 'no-store',
        },
    });
}

async function* streamSearch(query, params, perPage) {
    const raw = await executeSearch(query, params.categoriesStr, params.enginesStr, params.language, params.timeRange, params.safesearch, params.pageno);

    const encoder = new TextEncoder();

    if (!raw) {
        yield encoder.encode(`data: ${JSON.stringify({ success: false, error: 'All search providers are currently unavailable.' })}\n\n`);
        return;
    }

    const results = perPage != null ? raw.results.slice(0, perPage) : raw.results;

    yield encoder.encode(`data: ${JSON.stringify({
        type: 'meta', success: true, query,
        answers: raw.answers || [], infobox: raw.infobox || null,
        suggestions: raw.suggestions || [], corrections: raw.corrections || [],
        total_count: results.length, source: raw.source || 'unknown',
    })}\n\n`);

    for (let i = 0; i < results.length; i++) {
        yield encoder.encode(`data: ${JSON.stringify({ type: 'result', index: i, data: results[i] })}\n\n`);
    }

    yield encoder.encode(`data: ${JSON.stringify({ type: 'complete', total_sent: results.length })}\n\n`);
}

function makeStream(query, params, perPage) {
    const gen = streamSearch(query, params, perPage);
    const stream = new ReadableStream({
        async pull(controller) {
            const { value, done } = await gen.next();
            if (done) { controller.close(); return; }
            controller.enqueue(value);
        },
    });
    return new Response(stream, {
        headers: {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
        },
    });
}


const CATEGORIES_LIST = [
    { name: 'general', description: 'Web search results' },
    { name: 'images', description: 'Image search results with img_src and thumbnails' },
    { name: 'videos', description: 'Video results with iframe_src and duration' },
    { name: 'news', description: 'News articles with publishedDate' },
    { name: 'music', description: 'Music tracks with artist and album' },
    { name: 'files', description: 'File and torrent results with filesize, seed, leech' },
    { name: 'social_media', description: 'Social media posts and profiles' },
    { name: 'science', description: 'Academic papers with authors, journal, doi' },
    { name: 'it', description: 'IT resources, code, repositories' },
];

const ENGINES_BY_CATEGORY = {
    general: ['google', 'bing', 'duckduckgo', 'brave', 'yahoo', 'startpage', 'qwant', 'wikipedia', 'wikidata', 'openstreetmap'],
    images: ['bing_images', 'google_images', 'flickr', 'unsplash'],
    videos: ['bing_videos', 'google_videos', 'youtube', 'dailymotion', 'vimeo'],
    news: ['bing_news', 'google_news', 'reuters', 'bbc', 'techcrunch'],
    music: ['soundcloud', 'bandcamp', 'mixcloud'],
    files: ['piratebay', 'nyaa'],
    social_media: ['reddit', 'twitter', 'mastodon'],
    science: ['arxiv', 'pubmed', 'semantic_scholar'],
    it: ['github', 'gitlab', 'stackoverflow'],
};

const ALL_ENGINES = Object.values(ENGINES_BY_CATEGORY).flat();

const LANGUAGE_NAMES = {
    all: 'All languages', en: 'English', de: 'German', fr: 'French', es: 'Spanish', it: 'Italian',
    pt: 'Portuguese', nl: 'Dutch', pl: 'Polish', ru: 'Russian', zh: 'Chinese', ja: 'Japanese',
    ko: 'Korean', ar: 'Arabic', hi: 'Hindi', tr: 'Turkish', vi: 'Vietnamese', th: 'Thai',
    uk: 'Ukrainian', cs: 'Czech', sv: 'Swedish', da: 'Danish', fi: 'Finnish', no: 'Norwegian',
    hu: 'Hungarian', ro: 'Romanian', bg: 'Bulgarian', hr: 'Croatian', sk: 'Slovak', sl: 'Slovenian',
};

let cacheHits = 0;
let cacheMisses = 0;

const origGet = cacheGet;
const wrappedGet = (key) => {
    const v = origGet(key);
    if (v) cacheHits++; else cacheMisses++;
    return v;
};

export async function onRequest(context) {
    const { request } = context;
    const url = new URL(request.url);
    const pathname = url.pathname.replace(/\/$/, '') || '/';
    const method = request.method.toUpperCase();

    if (method === 'OPTIONS') {
        return new Response(null, {
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
        });
    }

    if (pathname === '' || pathname === '/') {
        return json({
            name: 'Cyron Search API',
            version: '4.0',
            description: 'Privacy-focused meta search engine API powered by SearX. Returns structured results across web, images, videos, news, music, files, social media, science, and IT.',
            endpoints: {
                'GET /': 'API documentation (this response)',
                'POST /search': 'Full search with JSON body',
                'GET /search/<query>': 'Search via URL path with query parameters',
                'POST /search/stream': 'Streaming search via Server-Sent Events',
                'GET /categories': 'List all supported categories',
                'GET /engines': 'List all engines, optionally filtered by ?category=',
                'GET /languages': 'List all 30 supported language codes',
                'GET /health': 'Health check and feature flags',
                'GET /stats': 'Cache performance and provider statistics',
            },
            search_parameters: {
                query: 'string (required)',
                categories: 'string or array — general, images, videos, news, music, files, social_media, science, it',
                engines: 'string or array — specific engines to target',
                language: 'string — language code e.g. en, de, fr (default: all)',
                time_range: 'string — day, week, month, year (default: any)',
                safesearch: 'integer — 0=off, 1=moderate, 2=strict (default: 1)',
                pageno: 'integer — page number (default: 1)',
                per_page: 'integer — results per page, 1-100 (default: all)',
                stream: 'boolean — GET only, enables SSE streaming (default: false)',
            },
            quick_start: {
                web: '/search/artificial intelligence?per_page=10',
                images: '/search/mountains?categories=images&per_page=20',
                videos: '/search/tutorials?categories=videos',
                news: '/search/technology?categories=news&time_range=day',
                science: '/search/neural networks?categories=science&engines=arxiv',
                it: '/search/react hooks?categories=it&engines=github,stackoverflow',
                multi_category: '/search/python?categories=general,science,it',
                stream: '/search/space?stream=true',
            },
        });
    }

    if (pathname === '/categories') {
        return json({ success: true, categories: CATEGORIES_LIST });
    }

    if (pathname === '/engines') {
        const cat = url.searchParams.get('category') || '';
        if (cat && ENGINES_BY_CATEGORY[cat]) {
            return json({ success: true, category: cat, engines: ENGINES_BY_CATEGORY[cat] });
        }
        return json({ success: true, engines_by_category: ENGINES_BY_CATEGORY, all_engines: ALL_ENGINES });
    }

    if (pathname === '/languages') {
        return json({ success: true, languages: Object.entries(LANGUAGE_NAMES).map(([code, name]) => ({ code, name })) });
    }

    if (pathname === '/health') {
        return json({
            status: 'healthy',
            service: 'Cyron Search API',
            version: '4.0',
            timestamp: new Date().toISOString(),
            providers: { total: SEARX_INSTANCES.length, instances: SEARX_INSTANCES },
            supported: { categories: VALID_CATEGORIES, time_ranges: VALID_TIME_RANGES, safesearch_levels: VALID_SAFESEARCH, languages: VALID_LANGUAGES.length, engines: ALL_ENGINES.length },
            features: { cache: true, cors: true, streaming: true, pagination: true, infobox: true, suggestions: true, answers: true },
        });
    }

    if (pathname === '/stats') {
        const total = cacheHits + cacheMisses;
        const hitRate = total > 0 ? ((cacheHits / total) * 100).toFixed(2) + '%' : '0.00%';
        return json({
            success: true,
            cache: { hits: cacheHits, misses: cacheMisses, hit_rate: hitRate, current_size: cache.size, max_size: 512 },
            providers: { total_instances: SEARX_INSTANCES.length, instances: SEARX_INSTANCES, rotation: 'random', failover: 'automatic' },
            api: { version: '4.0', categories: VALID_CATEGORIES.length, engines: ALL_ENGINES.length, languages: VALID_LANGUAGES.length },
        });
    }

    if (pathname === '/search/stream' && method === 'POST') {
        let body;
        try { body = await request.json(); } catch { return json({ success: false, error: 'Invalid JSON body' }, 400); }
        const query = (body.query || '').trim();
        if (!query) return json({ success: false, error: 'query is required' }, 400);
        const validated = validateParams(body);
        if (validated.errors.length) return json({ success: false, errors: validated.errors }, 400);
        return makeStream(query, validated, validated.perPage);
    }

    if (pathname === '/search' && method === 'POST') {
        let body;
        try { body = await request.json(); } catch { return json({ success: false, error: 'Invalid JSON body' }, 400); }
        const query = (body.query || '').trim();
        if (!query) return json({ success: false, error: 'query is required' }, 400);
        const validated = validateParams(body);
        if (validated.errors.length) return json({ success: false, errors: validated.errors }, 400);

        const raw = await executeSearch(query, validated.categoriesStr, validated.enginesStr, validated.language, validated.timeRange, validated.safesearch, validated.pageno);
        if (!raw) return json({ success: false, error: 'All search providers are currently unavailable.', providers_attempted: SEARX_INSTANCES.length }, 503);
        if (!raw.results.length) return json({ success: false, error: 'No results found.', query, suggestions: raw.suggestions || [], corrections: raw.corrections || [] }, 404);
        return json(buildResponse(raw, query, validated, validated.perPage));
    }

    if (pathname.startsWith('/search/') && pathname !== '/search/stream') {
        const queryPath = decodeURIComponent(pathname.slice('/search/'.length)).trim();
        if (!queryPath) return json({ success: false, error: 'query cannot be empty' }, 400);

        const sp = url.searchParams;
        const data = {
            categories: sp.get('categories') || '',
            engines: sp.get('engines') || '',
            language: sp.get('language') || 'all',
            time_range: sp.get('time_range') || '',
            safesearch: sp.get('safesearch') ?? 1,
            pageno: sp.get('pageno') ?? 1,
            per_page: sp.get('per_page') ?? null,
        };

        const streamMode = sp.get('stream') === 'true';
        const validated = validateParams(data);
        if (validated.errors.length) return json({ success: false, errors: validated.errors }, 400);

        if (streamMode) return makeStream(queryPath, validated, validated.perPage);

        const raw = await executeSearch(queryPath, validated.categoriesStr, validated.enginesStr, validated.language, validated.timeRange, validated.safesearch, validated.pageno);
        if (!raw) return json({ success: false, error: 'All search providers are currently unavailable.' }, 503);
        if (!raw.results.length) return json({ success: false, error: 'No results found.', query: queryPath, suggestions: raw.suggestions || [] }, 404);
        return json(buildResponse(raw, queryPath, validated, validated.perPage));
    }

    return json({
        success: false,
        error: 'Endpoint not found',
        available_endpoints: ['/', '/search (POST)', '/search/<query> (GET)', '/search/stream (POST)', '/categories', '/engines', '/languages', '/health', '/stats'],
    }, 404);
}