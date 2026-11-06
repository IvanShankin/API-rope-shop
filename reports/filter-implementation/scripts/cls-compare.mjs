import fs from 'node:fs';
import path from 'node:path';
import { launch, OUT, sleep } from './lib.mjs';

const OLD = {
  css: fs.readFileSync(path.join(OUT, '.before', 'catalog-filter.css'), 'utf8'),
  app: fs.readFileSync(path.join(OUT, '.before', 'app.js'), 'utf8'),
  controller: fs.readFileSync(path.join(OUT, '.before', 'CatalogController.js'), 'utf8'),
  view: fs.readFileSync(path.join(OUT, '.before', 'CatalogView.js'), 'utf8'),
};

function route(url) {
  const p = new URL(url).pathname;
  if (p === '/css/catalog-filter.css') return { body: OLD.css, contentType: 'text/css' };
  if (p === '/js/app.js') return { body: OLD.app, contentType: 'application/javascript' };
  if (p === '/js/controllers/CatalogController.js') return { body: OLD.controller, contentType: 'application/javascript' };
  if (p === '/js/views/catalog/CatalogView.js') return { body: OLD.view, contentType: 'application/javascript' };
  return null;
}
function isFont(url) {
  return /fonts\.(googleapis|gstatic)\.com/.test(url);
}

const INIT = () => {
  window.__probe = { shifts: [], filterShownAt: null, productsShownAt: null };
  try {
    new PerformanceObserver(list => {
      for (const e of list.getEntries()) {
        if (e.hadRecentInput) continue;
        window.__probe.shifts.push({ value: +e.value.toFixed(5), time: +e.startTime.toFixed(1) });
      }
    }).observe({ type: 'layout-shift', buffered: true });
  } catch { /* ignore */ }
  const timer = setInterval(() => {
    const filter = document.querySelector('.catalog-filter');
    if (filter && !filter.hidden && window.__probe.filterShownAt === null) window.__probe.filterShownAt = +performance.now().toFixed(1);
    if (document.querySelector('.product--visible') && window.__probe.productsShownAt === null) window.__probe.productsShownAt = +performance.now().toFixed(1);
    if (window.__probe.filterShownAt !== null && window.__probe.productsShownAt !== null) clearInterval(timer);
  }, 10);
};

const browser = await launch();
const runs = {};

async function runMode(mode, viewport) {
  const [assets, fonts] = mode.split('+');
  const page = await browser.newPage();
  await page.setRequestInterception(true);
  page.on('request', req => {
    if (fonts === 'nofont' && isFont(req.url())) return req.abort();
    const hit = assets === 'before' ? route(req.url()) : null;
    if (hit) req.respond({ status: 200, contentType: hit.contentType, body: hit.body });
    else req.continue();
  });
  await page.evaluateOnNewDocument(INIT);
  await page.setViewport({ width: viewport.width, height: viewport.height });
  await page.goto('http://localhost/category/?group=1', { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => document.querySelector('.catalog-filter .ss-main') && document.querySelector('.product--visible'), { timeout: 30000 });
  await page.evaluate(() => document.fonts.ready);
  await sleep(2500);
  const data = await page.evaluate(() => {
    const shifts = window.__probe.shifts;
    return {
      clsTotal: +shifts.reduce((s, e) => s + e.value, 0).toFixed(4),
      shifts,
      filterShownAt: window.__probe.filterShownAt,
      productsShownAt: window.__probe.productsShownAt,
      title: document.querySelector('.catalog-filter__title')?.textContent.trim() || null,
      filterHeight: +document.querySelector('.catalog-filter').getBoundingClientRect().height.toFixed(1),
      firstProductTop: +(document.querySelector('.product--visible').getBoundingClientRect().top + scrollY).toFixed(1),
      fontFamily: getComputedStyle(document.body).fontFamily,
    };
  });
  await page.close();
  return data;
}

const viewports = {
  mobile: { width: 390, height: 844 },
  desktop: { width: 1440, height: 1000 },
};
const plan = {
  mobile: ['before+font', 'after+font', 'before+nofont', 'after+nofont'],
  desktop: ['before+font', 'after+font'],
};

for (const [vpName, modes] of Object.entries(plan)) {
  runs[vpName] = {};
  for (const mode of modes) {
    runs[vpName][mode] = [];
    for (let i = 0; i < 2; i += 1) runs[vpName][mode].push(await runMode(mode, viewports[vpName]));
  }
}

const summarize = list => ({
  runs: list.map(r => ({ cls: r.clsTotal, filterShownAt: r.filterShownAt, productsShownAt: r.productsShownAt, title: r.title, filterHeight: r.filterHeight, firstProductTop: r.firstProductTop, shifts: r.shifts, fontFamily: r.fontFamily })),
  clsMedian: [...list.map(r => r.clsTotal)].sort((a, b) => a - b)[list.length >> 1],
});
fs.writeFileSync(path.join(OUT, 'cls-comparison.json'), JSON.stringify(Object.fromEntries(Object.entries(runs).map(([vpName, modes]) => [vpName, Object.fromEntries(Object.entries(modes).map(([k, v]) => [k, summarize(v)]))])), null, 2));
await browser.close();
console.log('CLS DONE');
