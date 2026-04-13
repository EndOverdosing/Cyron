# Configuration

## SearX Instances

Edit `SEARX_INSTANCES` at the top of `functions/[[path]].js` to add, remove, or replace instances:

```js
const SEARX_INSTANCES = [
  "https://searx.be",
  "https://your-private-instance.example.com",
];
```

All instances are queried in parallel on every request. The first one to return valid results wins. Dead or rate-limited instances are silently skipped.

A public list of available SearX instances is maintained at [searx.space](https://searx.space).

## Cache

Results are cached in-memory per Worker instance with a 5-minute TTL and a maximum of 512 entries. To adjust:

```js
const CACHE_TTL = 5 * 60 * 1000;  // milliseconds
```

```js
if (cache.size > 512) { ... }      // max entries
```

Note that Cloudflare Workers are stateless and may spin up multiple instances, so cache is not shared across instances. For a shared cache, replace the in-memory Map with [Cloudflare KV](https://developers.cloudflare.com/kv/).

## CORS

CORS is open (`*`) by default on all responses. To restrict to specific origins, edit the `json()` helper in `functions/[[path]].js`:

```js
function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': 'https://yourdomain.com',
      ...
    },
  });
}
```

## Request Timeout

Each SearX instance has a 9-second timeout per request. To adjust:

```js
const timer = setTimeout(() => controller.abort(), 9000);
```

## Cloudflare KV Cache (Optional)

To persist cache across Worker instances, bind a KV namespace in `wrangler.toml`:

```toml
[[kv_namespaces]]
binding = "CACHE"
id = "your-kv-namespace-id"
```

Then replace `cacheGet` / `cacheSet` in the Worker to use `context.env.CACHE.get()` and `context.env.CACHE.put()`.