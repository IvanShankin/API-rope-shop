import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';

export const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
export const HOST = 'http://localhost';
export const BASE = HOST + '/category/?group=1';
export const OUT = 'reports/filter-implementation';
export const sleep = ms => new Promise(r => setTimeout(r, ms));

export async function launch() {
  return puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--force-color-profile=srgb', '--hide-scrollbars'],
  });
}

const CLS_INIT = () => {
  window.__layoutShifts = [];
  window.__clsAt = () => window.__layoutShifts.reduce((sum, e) => sum + e.value, 0);
  try {
    new PerformanceObserver(list => {
      for (const e of list.getEntries()) {
        if (e.hadRecentInput) continue;
        window.__layoutShifts.push({
          value: +e.value.toFixed(5),
          startTime: +e.startTime.toFixed(1),
          sources: (e.sources || []).map(s => ({
            node: s.node ? (s.node.nodeName + (s.node.className ? '.' + String(s.node.className).split(' ').join('.') : '')) : null,
            prev: s.previousRect ? `${Math.round(s.previousRect.x)},${Math.round(s.previousRect.y)} ${Math.round(s.previousRect.width)}x${Math.round(s.previousRect.height)}` : null,
            cur: s.currentRect ? `${Math.round(s.currentRect.x)},${Math.round(s.currentRect.y)} ${Math.round(s.currentRect.width)}x${Math.round(s.currentRect.height)}` : null,
          })),
        });
      }
    }).observe({ type: 'layout-shift', buffered: true });
  } catch { /* layout-shift is Chromium-only */ }
};

export async function openPage(browser, { width = 1440, height = 1000, dpr = 1, url = BASE } = {}) {
  const page = await browser.newPage();
  page.on('pageerror', e => console.log('PAGE EXCEPTION:', e.message));
  page.on('console', m => { if (m.type() === 'error') console.log('CONSOLE ERROR:', m.text()); });
  await page.evaluateOnNewDocument(CLS_INIT);
  await page.setViewport({ width, height, deviceScaleFactor: dpr });
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => {
    const s = document.querySelector('.catalog-filter .ss-main');
    const p = document.querySelector('.product--visible, .catalog-filter__empty');
    return Boolean(s && p);
  }, { timeout: 30000 });
  await page.evaluate(() => document.fonts.ready);
  await sleep(1500);
  return page;
}

export async function readCls(page) {
  return page.evaluate(() => ({
    total: +window.__layoutShifts.reduce((s, e) => s + e.value, 0).toFixed(4),
    entries: window.__layoutShifts,
  }));
}

export async function frameFilter(page, pad = 20) {
  await page.evaluate(pad => {
    const f = document.querySelector('.catalog-filter');
    const h = document.querySelector('.header');
    const t = parseFloat(getComputedStyle(f).top);
    const headerH = h ? h.getBoundingClientRect().height : 0;
    const desired = Number.isFinite(t) ? Math.max(t, headerH + 12) : headerH + 12;
    window.scrollTo({ top: Math.max(0, f.getBoundingClientRect().top + window.scrollY - desired), behavior: 'instant' });
  }, pad);
  await sleep(600);
}

export function shotPath(file) {
  fs.mkdirSync(OUT, { recursive: true });
  return path.join(OUT, file);
}

export async function viewportShot(page, file, clip) {
  await page.screenshot({ path: shotPath(file), ...(clip ? { clip } : {}) });
}

export async function elementShot(page, selector, file) {
  const el = await page.$(selector);
  if (!el) throw new Error('element not found: ' + selector);
  await el.screenshot({ path: shotPath(file) });
}

export async function clipShot(page, selector, file, pad = 16) {
  const box = await page.evaluate((sel, pad) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: r.x - pad, y: r.y - pad, width: r.width + pad * 2, height: r.height + pad * 2 };
  }, selector, pad);
  if (!box) throw new Error('element not found: ' + selector);
  const vp = page.viewport();
  const x = Math.max(0, Math.round(box.x));
  const y = Math.max(0, Math.round(box.y));
  await page.screenshot({
    path: shotPath(file),
    captureBeyondViewport: false,
    clip: { x, y, width: Math.min(Math.round(box.width), vp.width - x), height: Math.min(Math.round(box.height), vp.height - y) },
  });
}

export async function state(page) {
  return page.evaluate(() => ({
    url: location.search,
    lang: document.documentElement.lang,
    products: document.querySelectorAll('.product--visible').length,
    empty: Boolean(document.querySelector('.catalog-filter__empty')),
    resetDisabled: document.querySelector('.catalog-filter__reset')?.disabled,
    values: [...document.querySelectorAll('.catalog-filter select')].map(s => s.value),
    ssValues: [...document.querySelectorAll('.ss-single')].map(s => s.textContent.trim()),
    checked: document.querySelector('[name="configurator"]')?.checked,
    title: document.querySelector('.catalog-filter__title')?.textContent.trim() || null,
    fieldLabels: [...document.querySelectorAll('.catalog-filter__field')].map(el => el.textContent.trim().split('\n')[0].trim()),
  }));
}

export async function measurements(page) {
  return page.evaluate(() => {
    const q = s => document.querySelector(s);
    const box = s => {
      const el = q(s);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { x: +r.x.toFixed(1), y: +(r.top + window.scrollY).toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1) };
    };
    const cs = s => {
      const el = q(s);
      if (!el) return null;
      const c = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return {
        font: `${c.fontWeight} ${c.fontSize}/${c.lineHeight} ${c.fontFamily}`,
        color: c.color, background: c.backgroundColor,
        border: `${c.borderTopWidth} ${c.borderTopStyle} ${c.borderTopColor}`,
        radius: c.borderTopLeftRadius, padding: c.padding, gap: c.gap,
        minHeight: c.minHeight, opacity: c.opacity,
        w: +r.width.toFixed(1), h: +r.height.toFixed(1),
      };
    };
    const firstProduct = q('.product--visible');
    const items = q('.products__items');
    const vpWidth = window.innerWidth;
    return {
      viewport: { w: vpWidth, h: window.innerHeight, scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight },
      headerBox: box('.header'),
      filterBox: box('.catalog-filter'),
      fieldsetBox: box('.catalog-filter__fields'),
      titleBox: box('.catalog-filter__title'),
      ssBox: box('.ss-main.catalog-filter__select'),
      checkBox: box('.catalog-filter__check'),
      inputBox: box('.catalog-filter__check input'),
      resetBox: box('.catalog-filter__reset'),
      itemsBox: box('.products__items'),
      firstProductBox: firstProduct ? (() => { const r = firstProduct.getBoundingClientRect(); return { x: +r.x.toFixed(1), y: +(r.top + window.scrollY).toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1) }; })() : null,
      productsLeft: items ? +items.getBoundingClientRect().left.toFixed(1) : null,
      styles: {
        filter: cs('.catalog-filter'),
        title: cs('.catalog-filter__title'),
        field: cs('.catalog-filter__field'),
        ssMain: cs('.ss-main.catalog-filter__select'),
        ssText: cs('.ss-single'),
        check: cs('.catalog-filter__check'),
        input: cs('.catalog-filter__check input'),
        reset: cs('.catalog-filter__reset'),
      },
      titleExists: Boolean(q('.catalog-filter__title')),
      titleText: q('.catalog-filter__title')?.textContent.trim() || null,
      htmlLang: document.documentElement.lang,
    };
  });
}

export async function foreignColors(page) {
  return page.evaluate(() => {
    const foreign = ['rgb(40, 94, 137)', 'rgb(133, 197, 255)', 'rgb(121, 166, 207)', '#285E89', '#85C5FF', '#79A6CF'];
    const props = ['color', 'backgroundColor', 'borderTopColor', 'borderRightColor', 'borderBottomColor', 'borderLeftColor', 'outlineColor', 'boxShadow'];
    const hits = [];
    const root = document.querySelector('.catalog-filter');
    if (!root) return hits;
    for (const el of [root, ...root.querySelectorAll('*')]) {
      const c = getComputedStyle(el);
      for (const p of props) {
        const v = String(c[p] || '').toLowerCase();
        if (!v || v === 'rgba(0, 0, 0, 0)') continue;
        for (const f of foreign) if (v.includes(f.toLowerCase())) {
          hits.push({ el: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ').join('.') : ''), prop: p, value: v });
        }
      }
    }
    return hits;
  });
}

export function rgb(str) {
  const m = String(str).match(/rgba?\(([^)]+)\)/);
  if (!m) return null;
  const parts = m[1].split(/[,/ ]+/).filter(Boolean).map(Number);
  return { r: parts[0], g: parts[1], b: parts[2], a: parts[3] ?? 1 };
}
export function lum({ r, g, b }) {
  const f = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
export function blend(fg, bg) {
  const a = fg.a;
  return {
    r: Math.round(fg.r * a + bg.r * (1 - a)),
    g: Math.round(fg.g * a + bg.g * (1 - a)),
    b: Math.round(fg.b * a + bg.b * (1 - a)),
    a: 1,
  };
}
export function contrast(fg, bg) {
  const l1 = lum(fg), l2 = lum(bg);
  return +(((Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)).toFixed(2));
}
export function hex(c) {
  return '#' + [c.r, c.g, c.b].map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase();
}

export async function openDropdown(page, index) {
  await page.evaluate(i => document.querySelectorAll('.catalog-filter .ss-main')[i].click(), index);
  await page.waitForSelector('.ss-content.ss-open', { timeout: 5000 });
  await sleep(350);
}

export async function pickOpenOption(page, text) {
  const ok = await page.evaluate(t => {
    const content = document.querySelector('.ss-content.ss-open');
    const opt = [...content.querySelectorAll('.ss-option')].find(el => el.textContent.trim() === t);
    if (!opt) return false;
    opt.click();
    return true;
  }, text);
  await sleep(800);
  return ok;
}
