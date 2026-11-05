import fs from 'node:fs';
import path from 'node:path';
import {
  launch, openPage, frameFilter, elementShot, measurements, state, readCls, foreignColors,
  openDropdown, pickOpenOption, rgb, blend, contrast, hex, OUT, sleep, HOST,
} from './lib.mjs';

const before = JSON.parse(fs.readFileSync(path.join(OUT, 'before-measurements.json'), 'utf8'));
const result = {
  capturedAt: new Date().toISOString(),
  desktop: {}, mobile: {},
  states: {}, checks: {}, contrast: {}, colors: {}, foreign: {}, cls: {},
  screenshots: [], group2: {}, comparison: {},
};

const browser = await launch();

async function tabTo(page, selector, max = 90) {
  for (let i = 1; i <= max; i += 1) {
    await page.keyboard.press('Tab');
    await sleep(60);
    const ok = await page.evaluate(s => Boolean(document.activeElement && document.activeElement.matches(s)), selector);
    if (ok) return i;
  }
  return -1;
}
async function blur(page) {
  await page.evaluate(() => { if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); });
  await sleep(250);
}
async function focusInfo(page, selector) {
  return page.evaluate(sel => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const c = getComputedStyle(el);
    return { outline: `${c.outlineWidth} ${c.outlineStyle} ${c.outlineColor}`, outlineOffset: c.outlineOffset, boxShadow: c.boxShadow, borderColor: c.borderTopColor };
  }, selector);
}
async function collectColors(page) {
  return page.evaluate(() => {
    const read = (sel, prop) => { const el = document.querySelector(sel); return el ? getComputedStyle(el)[prop] : null; };
    return {
      pageBg: getComputedStyle(document.body).backgroundColor,
      selectBg: read('.ss-main.catalog-filter__select', 'backgroundColor'),
      selectBorder: read('.ss-main.catalog-filter__select', 'borderTopColor'),
      selectText: read('.ss-main.catalog-filter__select', 'color'),
      labelColor: read('.catalog-filter__field', 'color'),
      checkBorder: read('.catalog-filter__check input', 'borderTopColor'),
      checkBg: read('.catalog-filter__check input', 'backgroundColor'),
      checkSize: (() => { const r = document.querySelector('.catalog-filter__check input').getBoundingClientRect(); return `${r.width}x${r.height}`; })(),
    };
  });
}
async function collectResetColors(page) {
  return page.evaluate(() => {
    const el = document.querySelector('.catalog-filter__reset');
    const c = getComputedStyle(el);
    return { border: c.borderTopColor, background: c.backgroundColor, color: c.color, opacity: c.opacity, disabled: el.disabled };
  });
}

// ==================== desktop 1440, DE (default) ====================
let page = await openPage(browser, { width: 1440, height: 1000 });
result.desktop = await measurements(page);
result.states.default = await state(page);
result.cls.desktop = await readCls(page);
result.foreign.default = await foreignColors(page);
result.colors = await collectColors(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-1440.png') });
result.screenshots.push('after-1440.png');

const tabsToSelect = await tabTo(page, '.ss-main.catalog-filter__select');
await sleep(600);
result.checks.tabsToFirstSelect = tabsToSelect;
result.checks.focusSelectVisible = await page.evaluate(() => {
  const el = document.querySelector('.ss-main.catalog-filter__select');
  return Boolean(el && el.matches(':focus-visible'));
});
result.checks.focusSelectActiveIndex = await page.evaluate(() => [...document.querySelectorAll('.catalog-filter .ss-main')].findIndex(el => el === document.activeElement));
result.checks.focusSelectStyle = await focusInfo(page, '.ss-main.catalog-filter__select');
result.foreign.focusSelect = await foreignColors(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-focus-select-1440.png') });
result.screenshots.push('after-focus-select-1440.png');
const tabsToCheckbox = await tabTo(page, '.catalog-filter__check input');
await sleep(300);
result.checks.tabsToCheckbox = tabsToCheckbox;
result.checks.focusCheckboxVisible = await page.evaluate(() => document.querySelector('.catalog-filter__check input').matches(':focus-visible'));
result.checks.focusCheckboxStyle = await focusInfo(page, '.catalog-filter__check input');
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-focus-checkbox-1440.png') });
result.screenshots.push('after-focus-checkbox-1440.png');
await blur(page);

await frameFilter(page);
await page.hover('.ss-main.catalog-filter__select');
await sleep(500);
result.checks.hoverStyle = await page.evaluate(() => {
  const c = getComputedStyle(document.querySelector('.ss-main.catalog-filter__select'));
  return { background: c.backgroundColor, border: c.borderTopColor };
});
await page.screenshot({ path: path.join(OUT, 'after-hover-1440.png') });
result.screenshots.push('after-hover-1440.png');

await openDropdown(page, 1);
result.checks.openListStyle = await page.evaluate(() => {
  const content = document.querySelector('.ss-content.ss-open');
  const opt = [...content.querySelectorAll('.ss-option')];
  const c = getComputedStyle(content);
  const first = getComputedStyle(opt[0]);
  return {
    background: c.backgroundColor, border: c.borderTopColor, radius: c.borderTopLeftRadius,
    optionColor: first.color, optionBackground: first.backgroundColor,
    options: opt.map(o => o.textContent.trim()),
  };
});
result.foreign.openList = await foreignColors(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-select-open-1440.png') });
result.screenshots.push('after-select-open-1440.png');
const optionBox = await page.evaluate(() => {
  const opt = [...document.querySelectorAll('.ss-content.ss-open .ss-option')].find(o => o.textContent.trim() === '16');
  const r = opt.getBoundingClientRect();
  return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
});
await page.mouse.move(optionBox.x, optionBox.y);
await sleep(400);
result.checks.optionHoverStyle = await page.evaluate(() => {
  const opt = [...document.querySelectorAll('.ss-content.ss-open .ss-option')].find(o => o.textContent.trim() === '16');
  const c = getComputedStyle(opt);
  return { background: c.backgroundColor, color: c.color, borderLeft: c.borderLeft };
});
result.foreign.optionHover = await foreignColors(page);
await page.screenshot({ path: path.join(OUT, 'after-option-hover-1440.png') });
result.screenshots.push('after-option-hover-1440.png');

const picked = await pickOpenOption(page, '16');
await blur(page);
result.checks.pickDiameter16 = { clicked: picked, ...(await state(page)) };
result.checks.appliedMeasurements = await measurements(page);
result.colors.resetEnabled = await collectResetColors(page);
result.foreign.applied = await foreignColors(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-applied-1440.png') });
result.screenshots.push('after-applied-1440.png');

const tabsToReset = await tabTo(page, '.catalog-filter__reset');
await sleep(300);
result.checks.tabsToReset = tabsToReset;
result.checks.focusResetVisible = await page.evaluate(() => document.querySelector('.catalog-filter__reset').matches(':focus-visible'));
result.checks.focusResetStyle = await focusInfo(page, '.catalog-filter__reset');
result.foreign.focusReset = await foreignColors(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-reset-focus-1440.png') });
result.screenshots.push('after-reset-focus-1440.png');

await page.evaluate(() => document.querySelector('.catalog-filter__reset').click());
await sleep(900);
result.checks.reset = await state(page);
result.checks.resetStyle = await page.evaluate(() => {
  const c = getComputedStyle(document.querySelector('.catalog-filter__reset'));
  return { opacity: c.opacity, border: c.borderTopColor, cursor: c.cursor };
});
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-reset-1440.png') });
result.screenshots.push('after-reset-1440.png');
await page.close();

// ==================== desktop closeup DPR 2 ====================
page = await openPage(browser, { width: 1440, height: 1000, dpr: 2 });
await frameFilter(page);
await elementShot(page, '.catalog-filter', 'after-filter-1440.png', 16);
result.screenshots.push('after-filter-1440.png');
await page.evaluate(() => document.querySelector('[name="configurator"]').click());
await sleep(500);
await blur(page);
await page.evaluate(() => {
  const el = document.querySelector('.catalog-filter__check');
  window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 200, behavior: 'instant' });
});
await sleep(500);
await elementShot(page, '.catalog-filter__check', 'after-checkbox-checked-1440.png', 8);
result.screenshots.push('after-checkbox-checked-1440.png');
await page.close();

// ==================== RU / EN titles ====================
page = await openPage(browser, { width: 1440, height: 1000, url: HOST + '/category/?group=1&lang=ru' });
result.states.ru = await state(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-ru-1440.png') });
result.screenshots.push('after-ru-1440.png');
await page.close();

page = await openPage(browser, { width: 1440, height: 1000, url: HOST + '/category/?group=1&lang=en' });
result.states.en = await state(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-en-1440.png') });
result.screenshots.push('after-en-1440.png');
await page.close();

// ==================== mobile 390 ====================
page = await openPage(browser, { width: 390, height: 844 });
result.mobile = await measurements(page);
result.states.mobileDefault = await state(page);
result.cls.mobile = await readCls(page);
result.foreign.mobile = await foreignColors(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-390.png') });
result.screenshots.push('after-390.png');
await openDropdown(page, 1);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-select-open-390.png') });
result.screenshots.push('after-select-open-390.png');
const pickedMobile = await pickOpenOption(page, '16');
await blur(page);
result.checks.mobilePickDiameter16 = { clicked: pickedMobile, ...(await state(page)) };
result.checks.mobileAppliedMeasurements = await measurements(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-applied-390.png') });
result.screenshots.push('after-applied-390.png');
await page.evaluate(() => document.querySelector('.catalog-filter__reset').click());
await sleep(900);
result.checks.mobileReset = await state(page);
result.checks.mobileResetMeasurements = await measurements(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-reset-390.png') });
result.screenshots.push('after-reset-390.png');
await page.close();

page = await openPage(browser, { width: 390, height: 844, dpr: 2 });
await frameFilter(page);
await elementShot(page, '.catalog-filter', 'after-filter-390.png', 16);
result.screenshots.push('after-filter-390.png');
await page.close();

// ==================== other category group=2 ====================
page = await openPage(browser, { width: 1440, height: 1000, url: HOST + '/category/?group=2' });
result.group2 = {
  measurements: await measurements(page),
  state: await state(page),
  foreign: await foreignColors(page),
  selectOptions: await page.evaluate(() => [...document.querySelectorAll('.catalog-filter select')].map(s => ({ name: s.name, count: s.options.length, values: [...s.options].map(o => o.value) }))),
};
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'after-group2-1440.png') });
result.screenshots.push('after-group2-1440.png');
const many = result.group2.selectOptions.find(s => s.count > 9);
if (many) {
  const idx = result.group2.selectOptions.findIndex(s => s.count > 9);
  await openDropdown(page, idx);
  result.group2.openListSearchVisible = await page.evaluate(() => {
    const content = document.querySelector('.ss-content.ss-open');
    const search = content.querySelector('.ss-search input');
    if (!search) return null;
    const c = getComputedStyle(search);
    return { background: c.backgroundColor, color: c.color, borderBottom: c.borderBottomColor, visible: Boolean(search.getClientRects().length) };
  });
  result.group2.openListOptions = await page.evaluate(() => [...document.querySelectorAll('.ss-content.ss-open .ss-option')].length);
  await page.screenshot({ path: path.join(OUT, 'after-group2-select-open-1440.png') });
  result.screenshots.push('after-group2-select-open-1440.png');
}
await page.close();

// ==================== contrast ====================
const pageBg = rgb(result.colors.pageBg);
const selectBg = rgb(result.colors.selectBg);
const selectBorder = rgb(result.colors.selectBorder);
const checkBorder = rgb(result.colors.checkBorder);
const resetEnabled = rgb(result.colors.resetEnabled.border);
const resetDisabled = rgb(result.checks.resetStyle.border);
const snow = rgb('rgb(246, 250, 253)');
const night = { r: 10, g: 25, b: 49, a: 1 };

const fieldBorderPixel = blend(selectBorder, selectBg);
const resetEnabledPixel = blend(resetEnabled, pageBg);
const resetDisabledPixel = blend({ ...resetDisabled, a: resetDisabled.a * Number(result.checks.resetStyle.opacity) }, pageBg);
const checkBorderPixel = blend(checkBorder, pageBg);

result.contrast = {
  fieldBorder_vs_page: { colors: `${hex(fieldBorderPixel)} on ${hex(pageBg)}`, ratio: contrast(fieldBorderPixel, pageBg) },
  fieldBorder_vs_own_fill: { colors: `${hex(fieldBorderPixel)} on ${hex(selectBg)}`, ratio: contrast(fieldBorderPixel, selectBg) },
  resetBorderEnabled_vs_page: { colors: `${hex(resetEnabledPixel)} on ${hex(pageBg)}`, ratio: contrast(resetEnabledPixel, pageBg) },
  resetBorderDisabled_vs_page: { colors: `${hex(resetDisabledPixel)} on ${hex(pageBg)}`, ratio: contrast(resetDisabledPixel, pageBg), note: 'disabled, WCAG 1.4.11 exempt' },
  checkboxBorder_vs_page: { colors: `${hex(checkBorderPixel)} on ${hex(pageBg)}`, ratio: contrast(checkBorderPixel, pageBg) },
  checkboxCheckedFill_vs_page: { colors: `${hex(snow)} on ${hex(pageBg)}`, ratio: contrast(snow, pageBg) },
  checkmark_vs_checkedFill: { colors: `${hex(night)} on ${hex(snow)}`, ratio: contrast(night, snow) },
  labelMicroText_vs_page: { colors: `${hex(blend(rgb(result.colors.labelColor), pageBg))} on ${hex(pageBg)}`, ratio: contrast(blend(rgb(result.colors.labelColor), pageBg), pageBg) },
  selectValueText_vs_selectFill: { colors: `${hex(rgb(result.colors.selectText))} on ${hex(selectBg)}`, ratio: contrast(rgb(result.colors.selectText), selectBg) },
  resetText_vs_page: { colors: `${hex(rgb(result.colors.resetEnabled.color))} on ${hex(pageBg)}`, ratio: contrast(rgb(result.colors.resetEnabled.color), pageBg) },
};

// ==================== comparison with before ====================
const d = before.desktop, m = before.mobile;
result.comparison = {
  desktop: {
    filterHeightBefore: d.filterBox.h, filterHeightAfter: result.desktop.filterBox.h,
    filterHeightDelta: +(result.desktop.filterBox.h - d.filterBox.h).toFixed(1),
    firstProductTopBefore: d.firstProductBox.y, firstProductTopAfter: result.desktop.firstProductBox.y,
    firstProductShift: +(result.desktop.firstProductBox.y - d.firstProductBox.y).toFixed(1),
    pageScrollHeightBefore: d.viewport.scrollHeight, pageScrollHeightAfter: result.desktop.viewport.scrollHeight,
    productsTopBefore: d.itemsBox.y, productsTopAfter: result.desktop.itemsBox.y,
  },
  mobile: {
    filterHeightBefore: m.filterBox.h, filterHeightAfter: result.mobile.filterBox.h,
    filterHeightDelta: +(result.mobile.filterBox.h - m.filterBox.h).toFixed(1),
    firstProductTopBefore: m.firstProductBox.y, firstProductTopAfter: result.mobile.firstProductBox.y,
    firstProductShift: +(result.mobile.firstProductBox.y - m.firstProductBox.y).toFixed(1),
    pageScrollHeightBefore: m.viewport.scrollHeight, pageScrollHeightAfter: result.mobile.viewport.scrollHeight,
  },
  cls: {
    desktopBefore: before.cls.desktop.total, desktopAfter: result.cls.desktop.total,
    mobileBefore: before.cls.mobile.total, mobileAfter: result.cls.mobile.total,
  },
};

// ==================== acceptance summary ====================
const st = result.states;
result.checks.acceptance = {
  titleDe: st.default.title,
  titleRu: st.ru.title,
  titleEn: st.en.title,
  labelsRu: st.ru.fieldLabels,
  labelsDe: st.default.fieldLabels,
  pickUrlOk: st.default.url === '?group=1' && result.checks.pickDiameter16.url === '?group=1&diameter=16' && result.checks.pickDiameter16.products === 1,
  resetOk: result.checks.reset.url === '?group=1' && result.checks.reset.products === 2 && result.checks.reset.resetDisabled === true,
  mobilePickOk: result.checks.mobilePickDiameter16.url === '?group=1&diameter=16' && result.checks.mobilePickDiameter16.products === 1,
  mobileResetOk: result.checks.mobileReset.url === '?group=1' && result.checks.mobileReset.products === 2,
  resetDisabledDefault: result.states.default.resetDisabled === true,
  resetDisabledAfterReset: result.checks.reset.resetDisabled === true,
  checkboxSize: result.colors.checkSize,
  hitAreas: {
    select: `${result.desktop.ssBox.w}x${result.desktop.ssBox.h}`,
    reset: `${result.desktop.resetBox.w}x${result.desktop.resetBox.h}`,
    checkLabel: `${result.desktop.checkBox.w}x${result.desktop.checkBox.h}`,
    checkbox: `${result.desktop.inputBox.w}x${result.desktop.inputBox.h}`,
  },
  mobileHitAreas: {
    select: `${result.mobile.ssBox.w}x${result.mobile.ssBox.h}`,
    reset: `${result.mobile.resetBox.h}px tall`,
    checkLabel: `${result.mobile.checkBox.w}x${result.mobile.checkBox.h}`,
    checkbox: `${result.mobile.inputBox.w}x${result.mobile.inputBox.h}`,
  },
  twoColumns390: result.mobile.ssBox.w < 200,
  scrollWidth390: result.mobile.viewport.scrollWidth,
  foreignColorHits: Object.fromEntries(Object.entries(result.foreign).map(([k, v]) => [k, v.length])),
  group2Products: result.group2.state.products,
  group2Title: result.group2.state.title,
  group2ForeignHits: result.group2.foreign.length,
};

fs.writeFileSync(path.join(OUT, 'after-measurements.json'), JSON.stringify(result, null, 2));
await browser.close();
console.log('AFTER DONE');
