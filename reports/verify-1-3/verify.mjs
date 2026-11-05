import puppeteer from 'puppeteer-core';
import fs from 'node:fs';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE = 'http://localhost';
const OUT = new URL('.', import.meta.url).pathname;

const results = {
  meta: { date: new Date().toISOString(), base: BASE },
  catalog: {},
  catalogMock7: {},
  catalogMock3: {},
  cardText: {},
  gallery: {},
  cls: {},
  consoleErrors: [],
  pageErrors: [],
};

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

function attachLogging(page, tag) {
  page.on('console', (msg) => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error' || /failed|error|404/i.test(text)) {
      results.consoleErrors.push({ page: tag, type, text });
    }
  });
  page.on('pageerror', (err) => {
    results.pageErrors.push({ page: tag, text: String(err) });
  });
  page.on('requestfailed', (req) => {
    results.consoleErrors.push({ page: tag, type: 'requestfailed', text: `${req.url()} ${req.failure()?.errorText}` });
  });
}

async function launch(width, height) {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    args: [`--window-size=${width},${height}`, '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width, height },
  });
  return browser;
}

// ---------- 1) Catalog grid geometry ----------
async function checkCatalogGrid(width, height, mockCount = null, tag = 'catalog') {
  const browser = await launch(width, height);
  const page = await browser.newPage();
  attachLogging(page, tag);

  if (mockCount !== null) {
    await page.evaluateOnNewDocument((count) => {
      const origFetch = window.fetch;
      window.fetch = async (url, opts) => {
        const s = String(url);
        if (s.includes('/api/material_groups')) {
          const groups = Array.from({ length: count }, (_, i) => ({
            id: i + 1,
            code: `mock-${i + 1}`,
            name: `Mock ${i + 1}`,
            is_active: true,
            image_url: null,
          }));
          return new Response(JSON.stringify(groups), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }
        if (s.includes('/api/products/detailed')) {
          return new Response(JSON.stringify([]), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }
        return origFetch(url, opts);
      };
    }, mockCount);
  }

  await page.goto(`${BASE}/catalog/`, { waitUntil: 'networkidle0', timeout: 30000 });
  await page.waitForSelector('.catalog__list .catalog__item:not(.catalog__item--skeleton)', { timeout: 15000 }).catch(() => {});
  await sleep(500);

  const data = await page.evaluate(() => {
    const list = document.querySelector('.catalog__list');
    if (!list) return { error: 'no .catalog__list' };
    const listRect = list.getBoundingClientRect();
    const items = [...list.querySelectorAll('.catalog__item')].map((li, i) => {
      const r = li.getBoundingClientRect();
      return {
        index: i,
        classes: li.className,
        x: Math.round(r.x * 10) / 10,
        y: Math.round(r.y * 10) / 10,
        width: Math.round(r.width * 10) / 10,
        height: Math.round(r.height * 10) / 10,
        right: Math.round(r.right * 10) / 10,
        bottom: Math.round(r.bottom * 10) / 10,
        text: li.textContent.trim().replace(/\s+/g, ' '),
      };
    });
    // Detect rows by y
    const rows = [];
    for (const it of items) {
      const row = rows.find(r => Math.abs(r.y - it.y) < 5);
      if (row) row.items.push(it);
      else rows.push({ y: it.y, items: [it] });
    }
    rows.sort((a, b) => a.y - b.y);
    // Check for gaps between consecutive items in same row
    const gaps = [];
    for (const row of rows) {
      row.items.sort((a, b) => a.x - b.x);
      for (let i = 0; i < row.items.length - 1; i++) {
        const gap = Math.round((row.items[i + 1].x - row.items[i].right) * 10) / 10;
        gaps.push({ rowY: row.y, between: [row.items[i].index, row.items[i + 1].index], gap });
      }
    }
    // Check if last row items fill to list right edge (no empty cell at right)
    const listRight = Math.round(listRect.right * 10) / 10;
    const lastRow = rows[rows.length - 1];
    const lastItem = lastRow?.items[lastRow.items.length - 1];
    return {
      count: items.length,
      listRect: { x: listRect.x, y: listRect.y, width: listRect.width, height: listRect.height, right: listRect.right },
      items,
      rows: rows.map(r => ({ y: r.y, count: r.items.length, indexes: r.items.map(i => i.index) })),
      gaps,
      lastRowRight: lastItem ? lastItem.right : null,
      listRight,
      rightGap: lastItem ? Math.round((listRight - lastItem.right) * 10) / 10 : null,
    };
  });

  await page.screenshot({ path: `${OUT}${tag}-${width}.png`, fullPage: false });
  await browser.close();
  return data;
}

// ---------- 2) Card text check ----------
async function checkCardText(lang) {
  const browser = await launch(1440, 900);
  const page = await browser.newPage();
  attachLogging(page, `card-text-${lang}`);
  const url = lang === 'de' ? `${BASE}/catalog/` : `${BASE}/catalog/?lang=${lang}`;
  await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
  await page.waitForSelector('.catalog__list .catalog__item:not(.catalog__item--skeleton)', { timeout: 15000 }).catch(() => {});
  await sleep(300);
  const texts = await page.evaluate(() => {
    return [...document.querySelectorAll('.catalog__item .catalog__card')].map(c => c.textContent.trim().replace(/\s+/g, ' '));
  });
  await browser.close();
  return { url, texts };
}

// ---------- 3) Gallery check ----------
async function checkGallery(pageUrl, tag) {
  const browser = await launch(1440, 900);
  const page = await browser.newPage();
  attachLogging(page, `gallery-${tag}`);
  await page.goto(pageUrl, { waitUntil: 'networkidle0', timeout: 30000 });
  await page.waitForSelector('.work-gallery__grid .work-gallery__photo img', { timeout: 15000 }).catch(() => {});
  await sleep(800);
  const data = await page.evaluate(async () => {
    const imgs = [...document.querySelectorAll('.work-gallery__photo img')];
    const checks = await Promise.all(imgs.map(async (img) => {
      let status = null;
      try {
        const r = await fetch(img.src, { method: 'HEAD' });
        status = r.status;
      } catch (e) {
        status = 'fetch-error';
      }
      return {
        src: img.src,
        status,
        naturalWidth: img.naturalWidth,
        naturalHeight: img.naturalHeight,
        complete: img.complete,
      };
    }));
    return {
      count: imgs.length,
      broken: checks.filter(c => c.status !== 200 || c.naturalWidth === 0).length,
      checks,
    };
  });
  await page.screenshot({ path: `${OUT}gallery-${tag}-1440.png`, fullPage: false });
  await browser.close();
  return data;
}

// ---------- 4) CLS measurement ----------
async function measureCls(width, height, tag) {
  const browser = await launch(width, height);
  const page = await browser.newPage();
  attachLogging(page, `cls-${tag}`);
  await page.evaluateOnNewDocument(() => {
    window.__clsShifts = [];
    const po = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          window.__clsShifts.push({
            value: entry.value,
            sources: entry.sources ? entry.sources.map(s => {
              const el = s.node;
              let desc = el ? (el.tagName || el.nodeName) : 'unknown';
              if (el && el.className && typeof el.className === 'string') desc += `.${el.className.split(' ')[0]}`;
              return { node: desc, currentRect: s.currentRect ? { x: s.currentRect.x, y: s.currentRect.y, w: s.currentRect.width, h: s.currentRect.height } : null, previousRect: s.previousRect ? { x: s.previousRect.x, y: s.previousRect.y, w: s.previousRect.width, h: s.previousRect.height } : null };
            }) : [],
            startTime: entry.startTime,
          });
        }
      }
    });
    po.observe({ type: 'layout-shift', buffered: true });
  });
  await page.goto(`${BASE}/category/?group=1`, { waitUntil: 'networkidle0', timeout: 30000 });
  await sleep(1000);
  const clsData = await page.evaluate(() => {
    const total = window.__clsShifts.reduce((a, s) => a + s.value, 0);
    return { total: Math.round(total * 10000) / 10000, shifts: window.__clsShifts };
  });
  await page.screenshot({ path: `${OUT}category-cls-${tag}-${width}.png`, fullPage: false });
  await browser.close();
  return clsData;
}

// ---------- Run all ----------
(async () => {
  // 1) Catalog real data
  results.catalog[1440] = await checkCatalogGrid(1440, 900);
  results.catalog[390] = await checkCatalogGrid(390, 844);
  // 1b) Mocks
  results.catalogMock7 = await checkCatalogGrid(1440, 900, 7, 'catalog-mock7');
  results.catalogMock3 = await checkCatalogGrid(1440, 900, 3, 'catalog-mock3');
  results.catalogMock3[390] = await checkCatalogGrid(390, 844, 3, 'catalog-mock3');
  results.catalogMock7[390] = await checkCatalogGrid(390, 844, 7, 'catalog-mock7');

  // 2) Card text
  results.cardText.de = await checkCardText('de');
  results.cardText.ru = await checkCardText('ru');

  // 3) Gallery
  results.gallery.catalog = await checkGallery(`${BASE}/catalog/`, 'catalog');
  results.gallery.home = await checkGallery(`${BASE}/`, 'home');

  // 4) CLS
  results.cls[390] = await measureCls(390, 844, '390');
  results.cls[1440] = await measureCls(1440, 900, '1440');

  fs.writeFileSync(`${OUT}results.json`, JSON.stringify(results, null, 2));
  console.log('DONE');
  console.log(JSON.stringify({
    catalog1440: results.catalog[1440]?.rows,
    catalog390: results.catalog[390]?.rows,
    mock7: results.catalogMock7[1440]?.rows,
    mock3: results.catalogMock3[1440]?.rows,
    cardTextDe: results.cardText.de?.texts,
    cardTextRu: results.cardText.ru?.texts,
    galleryCatalog: { count: results.gallery.catalog?.count, broken: results.gallery.catalog?.broken },
    galleryHome: { count: results.gallery.home?.count, broken: results.gallery.home?.broken },
    cls390: results.cls[390]?.total,
    cls1440: results.cls[1440]?.total,
    consoleErrors: results.consoleErrors.length,
    pageErrors: results.pageErrors.length,
  }, null, 2));
})().catch(e => { console.error('FATAL', e); process.exit(1); });
