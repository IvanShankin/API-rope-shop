import fs from 'node:fs';
import path from 'node:path';
import { launch, openPage, frameFilter, elemShot, decoder, rgb, contrast, blend, hex, OUT, sleep } from './lib.mjs';

const browser = await launch();
const dec = await decoder(browser);
const result = { screenshots: [], checks: {}, desktop: {}, mobile: {}, pixels: {}, contrast: {} };

const state = async page => page.evaluate(() => ({
  url: location.search,
  products: document.querySelectorAll('.product--visible').length,
  empty: Boolean(document.querySelector('.catalog-filter__empty')),
  resetDisabled: document.querySelector('.catalog-filter__reset').disabled,
  values: [...document.querySelectorAll('.catalog-filter select')].map(s => s.value),
  ssValues: [...document.querySelectorAll('.ss-single')].map(s => s.textContent.trim()),
  checked: document.querySelector('[name="configurator"]').checked,
}));

async function openDropdown(page, index) {
  await page.evaluate(i => document.querySelectorAll('.catalog-filter .ss-main')[i].click(), index);
  await page.waitForSelector('.ss-content.ss-open', { timeout: 5000 });
  await sleep(350);
}
async function pickOpenOption(page, text) {
  const ok = await page.evaluate(t => {
    const content = document.querySelector('.ss-content.ss-open');
    const opt = [...content.querySelectorAll('.ss-option')].find(el => el.textContent.trim() === t);
    if (!opt) return false;
    opt.click();
    return true;
  }, text);
  await sleep(700);
  return ok;
}
async function scrollFilterTop(page) {
  await page.evaluate(() => {
    const el = document.querySelector('.products--filtered');
    window.scrollTo({ top: Math.max(0, el.getBoundingClientRect().top + window.scrollY - 84 - 10), behavior: 'instant' });
  });
  await sleep(700);
}

// ================= desktop 1440 =================
let page = await openPage(browser, { width: 1440, height: 1000 });
const measure = await page.evaluate(() => {
  const q = s => document.querySelector(s);
  const style = el => {
    if (!el) return null;
    const c = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return {
      color: c.color, background: c.backgroundColor, borderColor: c.borderTopColor, borderWidth: c.borderTopWidth,
      radius: c.borderTopLeftRadius, fontFamily: c.fontFamily, fontSize: c.fontSize, fontWeight: c.fontWeight, lineHeight: c.lineHeight,
      padding: c.padding, minHeight: c.minHeight, opacity: c.opacity, textDecoration: c.textDecorationLine,
      width: +r.width.toFixed(1), height: +r.height.toFixed(1), gap: c.gap,
    };
  };
  const box = s => { const el = q(s); if (!el) return null; const r = el.getBoundingClientRect(); return { x: +r.x.toFixed(1), y: +r.y.toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1) }; };
  return {
    filtersTitleExists: Boolean(q('.catalog-filter__title')),
    fieldsetLegendExists: Boolean(q('.catalog-filter legend')),
    filterBox: box('.catalog-filter'),
    fieldsetBox: box('.catalog-filter__fields'),
    fieldBox: box('.catalog-filter__field'),
    ssBox: box('.ss-main.catalog-filter__select'),
    checkBox: box('.catalog-filter__check'),
    inputBox: box('.catalog-filter__check input'),
    resetBox: box('.catalog-filter__reset'),
    options: [...document.querySelectorAll('.catalog-filter select')].map(s => ({ name: s.name, options: [...s.options].map(o => ({ value: o.value, text: o.text })) })),
    styles: {
      filter: style(q('.catalog-filter')), fields: style(q('.catalog-filter__fields')), field: style(q('.catalog-filter__field')),
      ssMain: style(q('.ss-main.catalog-filter__select')), ssText: style(q('.ss-single')),
      check: style(q('.catalog-filter__check')), input: style(q('.catalog-filter__check input')), reset: style(q('.catalog-filter__reset')),
      pageTitle: style(q('.page-head__title')), productTitle: style(q('.product__title')), productText: style(q('.product__text')),
      productTableHead: style(q('.product__row--head .product__cell')),
      productCellBody: style(q('.product__table tbody .product__cell')),
      productRowOdd: style(q('.product__table tbody .product__row:nth-child(odd) .product__cell')),
      primaryButton: style(q('.product__info .button--primary')),
      body: style(document.body), header: style(q('.header')),
    },
    htmlLang: document.documentElement.lang,
  };
});

await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'before-1440.png') });
result.screenshots.push('before-1440.png');

await page.evaluate(() => window.scrollTo(0, 0));
await sleep(300);
await page.screenshot({ path: path.join(OUT, 'before-1440-full.png'), fullPage: true });
result.screenshots.push('before-1440-full.png');

await frameFilter(page);
await page.hover('.ss-main.catalog-filter__select');
await sleep(500);
await page.screenshot({ path: path.join(OUT, 'before-hover-1440.png') });
result.screenshots.push('before-hover-1440.png');

await openDropdown(page, 1);
await page.screenshot({ path: path.join(OUT, 'before-select-open-1440.png') });
result.screenshots.push('before-select-open-1440.png');

const pickOk = await pickOpenOption(page, '16');
const applied = await state(page);
result.checks.pickDiameter16 = { clicked: pickOk, ...applied };
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'before-applied-1440.png') });
result.screenshots.push('before-applied-1440.png');
await page.evaluate(() => window.scrollTo(0, 0));
await sleep(300);
await page.screenshot({ path: path.join(OUT, 'before-applied-1440-full.png'), fullPage: true });

await frameFilter(page);
await page.evaluate(() => document.querySelector('.catalog-filter__reset').click());
await sleep(800);
result.checks.reset = await state(page);
await page.screenshot({ path: path.join(OUT, 'before-reset-1440.png') });
result.screenshots.push('before-reset-1440.png');

await page.evaluate(() => document.querySelector('[name="configurator"]').click());
await sleep(800);
result.checks.checkbox = await state(page);
await page.screenshot({ path: path.join(OUT, 'before-checked-1440.png') });
result.screenshots.push('before-checked-1440.png');
await page.close();

// ================= desktop dpr 2-3 closeups =================
page = await openPage(browser, { width: 1440, height: 1000, dpr: 2 });
await frameFilter(page);
await elemShot(page, '.catalog-filter', path.join(OUT, 'before-filter-1440.png'));
await page.close();

page = await openPage(browser, { width: 1440, height: 1000, dpr: 3 });
await frameFilter(page);
result.pixels.checkboxUnchecked = await dec.palette(await (await page.$('.catalog-filter__check input')).screenshot());
result.pixels.select = await dec.palette(await (await page.$('.ss-main.catalog-filter__select')).screenshot());
result.pixels.resetDisabled = await dec.palette(await (await page.$('.catalog-filter__reset')).screenshot());
await page.evaluate(() => document.querySelector('[name="configurator"]').click());
await sleep(500);
result.pixels.checkboxChecked = await dec.palette(await (await page.$('.catalog-filter__check input')).screenshot());
await elemShot(page, '.catalog-filter__check', path.join(OUT, 'before-checkbox-checked-1440.png'));
await page.screenshot({ path: path.join(OUT, 'before-checked-closeup-1440.png') });
await page.close();

// ================= mobile 390 =================
page = await openPage(browser, { width: 390, height: 844 });
const mobileMeasure = await page.evaluate(() => {
  const box = s => { const el = document.querySelector(s); if (!el) return null; const r = el.getBoundingClientRect(); return { x: +r.x.toFixed(1), y: +r.y.toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1) }; };
  const cs = s => { const el = document.querySelector(s); if (!el) return null; const c = getComputedStyle(el); return { font: `${c.fontWeight} ${c.fontSize}/${c.lineHeight}`, color: c.color, background: c.backgroundColor, padding: c.padding, radius: c.borderTopLeftRadius }; };
  return {
    viewport: { w: innerWidth, h: innerHeight, scrollWidth: document.documentElement.scrollWidth },
    filterBox: box('.catalog-filter'), fieldsetBox: box('.catalog-filter__fields'), ssBox: box('.ss-main.catalog-filter__select'),
    checkBox: box('.catalog-filter__check'), inputBox: box('.catalog-filter__check input'), resetBox: box('.catalog-filter__reset'),
    styles: { field: cs('.catalog-filter__field'), ssMain: cs('.ss-main.catalog-filter__select'), reset: cs('.catalog-filter__reset') },
  };
});
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'before-390.png') });
await page.screenshot({ path: path.join(OUT, 'before-390-full.png'), fullPage: true });
result.screenshots.push('before-390.png', 'before-390-full.png');

await openDropdown(page, 0);
await page.screenshot({ path: path.join(OUT, 'before-select-open-390.png') });
result.screenshots.push('before-select-open-390.png');
await page.keyboard.press('Escape');
await sleep(300);

await openDropdown(page, 1);
await pickOpenOption(page, '16');
result.checks.mobilePickDiameter16 = await state(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'before-applied-390.png') });
result.screenshots.push('before-applied-390.png');
await page.close();

page = await openPage(browser, { width: 390, height: 844, dpr: 2 });
await page.evaluate(() => {
  const el = document.querySelector('.products--filtered');
  window.scrollTo({ top: Math.max(0, el.getBoundingClientRect().top + window.scrollY - 84 - 10), behavior: 'instant' });
});
await sleep(700);
await elemShot(page, '.catalog-filter', path.join(OUT, 'before-filter-390.png'));
await page.close();

// ================= contrast math =================
const night = rgb('rgb(10, 25, 49)');
const deep = rgb('rgb(26, 61, 99)');
const snow = rgb('rgb(246, 250, 253)');
const mist = rgb('rgb(179, 207, 229)');
const line = { ...mist, a: 0.18 };
const surface = rgb('rgb(15, 36, 66)');
const lineOnDeep = blend(line, deep);
const resetDisabled = blend({ ...snow, a: 0.4 }, night);
const muted = blend({ ...mist, a: 0.78 }, night);
result.contrast = {
  labelText_on_page: { colors: `${hex(snow)} on ${hex(night)}`, ratio: contrast(snow, night) },
  selectText_on_selectBg: { colors: `${hex(snow)} on ${hex(deep)}`, ratio: contrast(snow, deep) },
  selectBg_vs_pageBg: { colors: `${hex(deep)} vs ${hex(night)}`, ratio: contrast(deep, night) },
  selectBorder_on_selectBg: { colors: `${hex(lineOnDeep)} on ${hex(deep)}`, ratio: contrast(lineOnDeep, deep) },
  mutedText_on_page: { colors: `${hex(muted)} on ${hex(night)}`, ratio: contrast(muted, night) },
  resetDisabledText_on_page: { colors: `${hex(resetDisabled)} on ${hex(night)}`, ratio: contrast(resetDisabled, night) },
  surfaceCard_on_page: { colors: `${hex(surface)} vs ${hex(night)}`, ratio: contrast(surface, night) },
  mist_on_page: { colors: `${hex(mist)} on ${hex(night)}`, ratio: contrast(mist, night) },
};

result.desktop = measure;
result.mobile = mobileMeasure;
fs.writeFileSync(path.join(OUT, 'before-measurements.json'), JSON.stringify(result, null, 2));
await dec.close();
await browser.close();
console.log('DONE');

