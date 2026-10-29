const http = require('http');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const port = Number(process.env.PORT || 8080);
const apiTarget = (process.env.API_TARGET ?? 'https://kgosew-31-29-142-236.a.2na.am').replace(/\/+$/, '');
const blockAdmin = process.env.BLOCK_ADMIN === '1';
const pages = new Set(['admin', 'b2b', 'b2c', 'catalog', 'category', 'configurator', 'legal', 'login']);
const types = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.gif': 'image/gif',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.txt': 'text/plain; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8',
  '.webmanifest': 'application/manifest+json',
};

function sendFile(res, relative, extraHeaders = {}) {
  const file = path.resolve(root, relative);
  if (!file.startsWith(root + path.sep)) {
    res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Forbidden');
    return;
  }
  fs.readFile(file, (error, data) => {
    if (error) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not found');
      return;
    }
    res.writeHead(200, {
      'Content-Type': types[path.extname(file).toLowerCase()] || 'application/octet-stream',
      'Cache-Control': 'no-cache',
      ...extraHeaders,
    });
    res.end(data);
  });
}

function redirect(res, location) {
  res.writeHead(301, { Location: location });
  res.end();
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

async function proxy(req, res, pathname, search) {
  if (!apiTarget) {
    res.writeHead(502, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('API_TARGET is not configured');
    return;
  }
  const upstreamPath = pathname.startsWith('/api') ? pathname.slice(4) || '/' : pathname;
  const target = apiTarget + upstreamPath + search;
  const headers = { 'ngrok-skip-browser-warning': 'true' };
  for (const name of ['accept', 'content-type', 'authorization', 'range', 'if-none-match']) {
    if (req.headers[name]) headers[name] = req.headers[name];
  }
  const hasBody = !['GET', 'HEAD'].includes(req.method);
  const body = hasBody ? await readBody(req) : undefined;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30000);
  try {
    const upstream = await fetch(target, {
      method: req.method,
      headers,
      body,
      redirect: 'manual',
      signal: controller.signal,
    });
    const payload = Buffer.from(await upstream.arrayBuffer());
    const out = { 'Content-Type': upstream.headers.get('content-type') || 'application/octet-stream' };
    for (const name of ['content-range', 'accept-ranges', 'etag', 'last-modified']) {
      const value = upstream.headers.get(name);
      if (value) out[name] = value;
    }
    res.writeHead(upstream.status, out);
    res.end(payload);
  } catch (error) {
    res.writeHead(502, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end(`Upstream error: ${error.message}`);
  } finally {
    clearTimeout(timer);
  }
}

http.createServer(async (req, res) => {
  const [rawPath, search = ''] = (req.url || '/').split('?');
  const pathname = decodeURIComponent(rawPath);
  const page = pathname.match(/^\/([a-z0-9-]+)\/?$/);
  if (/^\/(api|media|assets)(\/|$)/.test(pathname)) {
    await proxy(req, res, pathname, search ? `?${search}` : '');
    return;
  }
  if (blockAdmin && /^\/(admin|login)\//.test(pathname)) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Not found');
    return;
  }
  if (pathname === '/' || pathname === '/index.html' || pathname === '/index' || pathname === '/index/') {
    sendFile(res, 'index.html');
    return;
  }
  if (/^\/order-tracking\/[^/]+\/?$/.test(pathname)) {
    sendFile(res, 'order-tracking.html', { 'Referrer-Policy': 'no-referrer', 'Cache-Control': 'no-store' });
    return;
  }
  if (page && pages.has(page[1])) {
    if (!pathname.endsWith('/')) {
      redirect(res, `/${page[1]}/`);
      return;
    }
    sendFile(res, `${page[1]}.html`);
    return;
  }
  if (/^\/(js|css|img)\//.test(pathname)) {
    sendFile(res, pathname.slice(1));
    return;
  }
  res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('Not found');
}).listen(port, '127.0.0.1', () => {
  console.log(`Site: http://localhost:${port}`);
  console.log(`API proxy: ${apiTarget || 'disabled'}`);
});
