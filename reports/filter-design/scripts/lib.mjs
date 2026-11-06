import puppeteer from 'puppeteer-core';
import fs from 'node:fs';

export const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
export const BASE = 'http://localhost/category/?group=1';
export const OUT = 'reports/filter-design';
export const sleep = ms => new Promise(r => setTimeout(r, ms));

export async function launch() {
  return puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--force-color-profile=srgb', '--hide-scrollbars'],
  });
}

export async function openPage(browser, { width = 1440, height = 1000, dpr = 1, url = BASE } = {}) {
  const page = await browser.newPage();
  page.on('pageerror', e => console.log('PAGE EXCEPTION:', e.message));
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

export async function scrollToFilter(page, pad = 20) {
  await page.evaluate(pad => {
    const el = document.querySelector('.products--filtered') || document.querySelector('.products');
    const y = el.getBoundingClientRect().top + window.scrollY - 84 - pad;
    window.scrollTo({ top: Math.max(0, y), behavior: 'instant' });
  }, pad);
  await sleep(600);
}

export async function clipShot(page, file, clip) {
  fs.mkdirSync(OUT, { recursive: true });
  const vp = page.viewport();
  const x = Math.max(0, Math.round(clip.x));
  const y = Math.max(0, Math.round(clip.y));
  const width = Math.min(Math.round(clip.width), vp.width - x);
  const height = Math.min(Math.round(clip.height), vp.height - y);
  if (width < 2 || height < 2) {
    console.log('SKIP SHOT (invalid clip):', file, { clip, x, y, width, height });
    return;
  }
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      await page.screenshot({ path: file, clip: { x, y, width, height }, captureBeyondViewport: false });
      return;
    } catch (err) {
      console.log(`SHOT RETRY ${attempt} ${file}: ${err.message}`);
      await sleep(350);
    }
  }
}

export async function frameFilter(page) {
  const info = await page.evaluate(() => {
    const f = document.querySelector('.catalog-filter');
    const h = document.querySelector('.header');
    const t = parseFloat(getComputedStyle(f).top);
    const headerH = h ? h.getBoundingClientRect().height : 0;
    const desired = Number.isFinite(t) ? Math.max(t, headerH + 12) : headerH + 12;
    return { scroll: Math.max(0, f.getBoundingClientRect().top + window.scrollY - desired) };
  });
  await page.evaluate(s => window.scrollTo({ top: s, behavior: 'instant' }), info.scroll);
  await sleep(600);
}

export async function elementShot(page, selector, file, pad = 16) {
  const box = await page.evaluate((sel, pad) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: Math.max(0, r.x - pad), y: Math.max(0, r.y - pad), width: r.width + pad * 2, height: r.height + pad * 2 };
  }, selector, pad);
  if (!box) throw new Error('element not found: ' + selector);
  await clipShot(page, file, box);
  return box;
}

export async function elemShot(page, selector, file) {
  fs.mkdirSync(OUT, { recursive: true });
  const el = await page.$(selector);
  if (!el) { console.log('SKIP ELEM SHOT, not found:', selector, file); return; }
  await el.screenshot({ path: file });
}

export async function decoder(browser) {
  const page = await browser.newPage();
  await page.setContent('<!doctype html><html><body><canvas id="c"></canvas></body></html>');
  return {
    async palette(buf) {
      return page.evaluate(async b64 => {
        const img = new Image();
        img.src = 'data:image/png;base64,' + b64;
        await img.decode();
        const c = document.createElement('canvas');
        c.width = img.width; c.height = img.height;
        const ctx = c.getContext('2d', { willReadFrequently: true });
        ctx.drawImage(img, 0, 0);
        const data = ctx.getImageData(0, 0, c.width, c.height).data;
        const counts = new Map();
        for (let i = 0; i < data.length; i += 4) {
          const k = `${data[i]},${data[i + 1]},${data[i + 2]},${data[i + 3]}`;
          counts.set(k, (counts.get(k) || 0) + 1);
        }
        return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, n]) => ({ rgba: k.split(',').map(Number), n }));
      }, buf.toString('base64'));
    },
    async close() { await page.close(); },
  };
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
  return { r: Math.round(fg.r * a + bg.r * (1 - a)), g: Math.round(fg.g * a + bg.g * (1 - a)), b: Math.round(fg.b * a + bg.b * (1 - a)), a: 1 };
}
export function contrast(fg, bg) {
  const l1 = lum(fg), l2 = lum(bg);
  return +(((Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)).toFixed(2));
}
export function hex(c) { return '#' + [c.r, c.g, c.b].map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase(); }

export function report(token, value, bg) {
  return {
    token,
    value: `${hex(value)} / ${hex(bg)}`,
    ratio: contrast(value, bg),
  };
}
