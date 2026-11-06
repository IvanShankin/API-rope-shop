import fs from 'node:fs';
import path from 'node:path';
import { launch, openPage, frameFilter, elemShot, decoder, OUT, sleep } from './lib.mjs';

const CHECK_SVG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3E%3Cpath d='M5 10.4 8.6 14 15 6.6' fill='none' stroke='%230A1931' stroke-width='2.1' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E";

const CSS_A = `
/* ===== VARIANT A: ruhige Filterleiste РІР‚вЂќ nur CSS + eine Ueberschrift ===== */
.catalog-filter__title {
  margin: 0 0 20px;
  font: 400 24px/1.1 var(--font-display);
  letter-spacing: -0.01em;
  color: var(--color-snow);
}
.catalog-filter__fields { gap: 0; }
.catalog-filter__field {
  gap: 8px;
  padding: 18px 0;
  border-top: 1px solid var(--color-line);
  font: 600 12px/1.4 var(--font-text);
  letter-spacing: 0.02em;
  color: rgba(179, 207, 229, 0.7);
}
.catalog-filter__field:first-of-type { padding-top: 0; border-top: 0; }
.page .ss-main.catalog-filter__select {
  min-height: 48px;
  padding: 0 14px;
  border: 1px solid rgba(179, 207, 229, 0.22);
  border-radius: 12px;
  background: #112846;
  color: var(--color-snow);
  font: 500 15px/1.3 var(--font-text);
  text-transform: none;
  letter-spacing: normal;
  transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
.page .ss-main.catalog-filter__select:hover {
  background: #152e4f;
  border-color: rgba(179, 207, 229, 0.38);
}
.page .ss-main.catalog-filter__select:focus { box-shadow: none; }
.page .ss-main.catalog-filter__select:focus-visible,
.page .ss-main.catalog-filter__select:is(.ss-dir-below, .ss-dir-above) {
  border-color: var(--color-mist);
  box-shadow: 0 0 0 3px rgba(179, 207, 229, 0.14);
  outline: none;
}
.page .ss-main.catalog-filter__select .ss-arrow { width: 11px; height: 11px; margin: 0 0 0 6px; opacity: 0.8; }
.page .ss-main.catalog-filter__select .ss-arrow path { stroke: var(--color-mist); }
.page .ss-content.catalog-filter__select {
  background: #0f2442;
  border: 1px solid rgba(179, 207, 229, 0.22);
  border-radius: 0 0 12px 12px;
  box-shadow: 0 24px 48px rgba(2, 8, 20, 0.55);
  font-size: 15px;
}
.page .ss-content.catalog-filter__select.ss-dir-above { border-radius: 12px 12px 0 0; }
.page .ss-content.catalog-filter__select .ss-list .ss-option {
  padding: 11px 14px;
  color: var(--color-snow);
  background: transparent;
}
.page .ss-content.catalog-filter__select .ss-list .ss-option:not(.ss-disabled):hover,
.page .ss-content.catalog-filter__select .ss-list .ss-option.ss-highlighted {
  background: rgba(179, 207, 229, 0.14);
  color: var(--color-snow);
}
.page .ss-content.catalog-filter__select .ss-list .ss-option.ss-selected {
  background: rgba(179, 207, 229, 0.1);
  color: var(--color-snow);
}
.catalog-filter__check {
  min-height: 44px;
  padding: 16px 0;
  border-top: 1px solid var(--color-line);
  align-items: center;
  gap: 12px;
  font: 400 14px/1.5 var(--font-text);
  color: var(--color-snow);
}
.catalog-filter__check input {
  appearance: none;
  -webkit-appearance: none;
  flex: 0 0 20px;
  width: 20px;
  height: 20px;
  margin: 0;
  border: 1.5px solid rgba(179, 207, 229, 0.5);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}
.catalog-filter__check input:hover { border-color: var(--color-mist); }
.catalog-filter__check input:checked {
  border-color: var(--color-snow);
  background-color: var(--color-snow);
  background-image: url("${CHECK_SVG}");
  background-repeat: no-repeat;
  background-position: center;
  background-size: 14px 14px;
}
.catalog-filter__check input:focus-visible {
  outline: 2px solid var(--color-mist);
  outline-offset: 3px;
}
.catalog-filter__reset {
  justify-self: start;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  margin-top: 18px;
  padding: 0 18px;
  border: 1px solid rgba(179, 207, 229, 0.28);
  border-radius: 999px;
  background: transparent;
  color: var(--color-snow);
  font: 600 13px/1 var(--font-text);
  letter-spacing: 0.01em;
  text-decoration: none;
  text-underline-offset: 0;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease, opacity 0.2s ease;
}
.catalog-filter__reset:hover:not(:disabled) {
  background: rgba(179, 207, 229, 0.1);
  border-color: rgba(179, 207, 229, 0.5);
}
.catalog-filter__reset:focus-visible { outline: 2px solid var(--color-mist); outline-offset: 3px; }
.catalog-filter__reset:disabled { opacity: 0.55; border-color: rgba(179, 207, 229, 0.16); cursor: default; }
@media (max-width: 767px) {
  .catalog-filter__title { margin-bottom: 16px; }
  .catalog-filter__fields { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 14px; }
  .catalog-filter__field { padding: 0 0 14px; border-top: 0; }
  .catalog-filter__check { grid-column: 1 / -1; padding: 14px 0; border-top: 0; }
  .catalog-filter__reset { grid-column: 1 / -1; justify-self: stretch; margin-top: 10px; min-height: 44px; }
}
`;

const DOM_A = () => {
  const aside = document.querySelector('.catalog-filter');
  const h = document.createElement('h2');
  h.className = 'catalog-filter__title';
  h.textContent = 'Filter';
  aside.prepend(h);
};

const CSS_B = CSS_A + `
/* ===== VARIANT B: Filterkarte mit Zaehler und aktiven Chips ===== */
.products.products--filtered { grid-template-columns: 268px minmax(0, 1fr); gap: 48px; }
.catalog-filter {
  padding: 22px 20px 20px;
  background: #0f2442;
  border: 1px solid var(--color-line);
  border-radius: 20px;
}
.catalog-filter__head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.catalog-filter__title { margin: 0; }
.catalog-filter__count {
  margin: 0;
  font: 400 12px/1.4 var(--font-text);
  color: rgba(179, 207, 229, 0.66);
  white-space: nowrap;
}
.catalog-filter__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  padding: 16px 0 18px;
  border-top: 1px solid var(--color-line);
}
.catalog-filter__chips[hidden] { display: none; }
.catalog-filter__chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px 8px 12px;
  border: 1px solid rgba(179, 207, 229, 0.28);
  border-radius: 999px;
  font: 500 12px/1.2 var(--font-text);
  color: var(--color-snow);
}
.catalog-filter__chip button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  border: 0;
  background: transparent;
  color: rgba(179, 207, 229, 0.8);
  font: 400 15px/1 var(--font-text);
  cursor: pointer;
}
.catalog-filter__chip button:hover { color: var(--color-snow); }
.catalog-filter__reset { width: 100%; margin-top: 20px; min-height: 44px; }
@media (max-width: 1279px) {
  .products.products--filtered { grid-template-columns: 240px minmax(0, 1fr); gap: 32px; }
}
@media (max-width: 767px) {
  .products.products--filtered { grid-template-columns: minmax(0, 1fr); gap: 32px; }
  .catalog-filter { padding: 18px 16px 16px; }
  .catalog-filter__fields { grid-template-columns: 1fr; gap: 0; }
  .catalog-filter__field { padding: 0 0 14px; border-top: 0; }
  .catalog-filter__check { grid-column: 1 / -1; padding: 14px 0; border-top: 0; }
  .catalog-filter__chips { grid-column: 1 / -1; }
  .catalog-filter__reset { grid-column: 1 / -1; }
}
`;

const DOM_B = () => {
  const aside = document.querySelector('.catalog-filter');
  const head = document.createElement('div');
  head.className = 'catalog-filter__head';
  head.innerHTML = '<h2 class="catalog-filter__title">Filter</h2><p class="catalog-filter__count">2 Produkte</p>';
  const chips = document.createElement('div');
  chips.className = 'catalog-filter__chips';
  chips.hidden = true;
  aside.prepend(head, chips);
  window.__mockSync = () => {
    const count = document.querySelectorAll('.product--visible').length;
    document.querySelector('.catalog-filter__count').textContent = count === 1 ? '1 Produkt' : `${count} Produkte`;
    const chipsEl = document.querySelector('.catalog-filter__chips');
    const parts = [];
    const construction = document.querySelector('[name="construction"]');
    if (construction.value) parts.push(`Konstruktion: ${construction.selectedOptions[0].textContent}`);
    const diameter = document.querySelector('[name="diameter"]');
    if (diameter.value) parts.push(`Durchmesser: ${diameter.value} mm`);
    if (document.querySelector('[name="configurator"]').checked) parts.push('Im Konfigurator verfuegbar');
    chipsEl.innerHTML = parts.map(text => `<span class="catalog-filter__chip">${text}<button type="button" aria-label="Filter entfernen">&times;</button></span>`).join('');
    chipsEl.hidden = !parts.length;
  };
};

const CSS_C = CSS_A + `
/* ===== VARIANT C: Filterleiste ueber dem Katalog (Struktur) ===== */
.products.products--filtered { grid-template-columns: minmax(0, 1fr); gap: 36px; }
.products--filtered > .products__items { grid-column: 1; }
.products--filtered > .catalog-filter { grid-column: 1; }
.catalog-filter {
  position: sticky;
  top: calc(var(--header-height, var(--header-h)) + 12px);
  z-index: 20;
  display: flex;
  flex-direction: column;
  gap: 0;
  max-height: none;
  overflow: visible;
  padding: 16px 20px 18px;
  background: rgba(11, 27, 52, 0.94);
  border: 1px solid var(--color-line);
  border-radius: 16px;
  backdrop-filter: blur(14px);
}
.catalog-filter__head { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; }
.catalog-filter__title { margin: 0; font-size: 20px; }
.catalog-filter__count { margin: 0; font: 400 12px/1.4 var(--font-text); color: rgba(179, 207, 229, 0.66); }
.catalog-filter__fields {
  display: grid;
  grid-template-columns: minmax(190px, 240px) minmax(150px, 180px) minmax(200px, 1fr) auto;
  align-items: end;
  gap: 16px;
  margin-top: 14px;
}
.catalog-filter__field { gap: 7px; padding: 0; border-top: 0; }
.catalog-filter__check { min-height: 48px; padding: 0; border-top: 0; align-items: center; }
.catalog-filter__reset { justify-self: end; align-self: end; min-height: 48px; margin: 0; }
@media (max-width: 1279px) {
  .catalog-filter__fields { grid-template-columns: minmax(170px, 220px) minmax(140px, 170px) minmax(170px, 1fr) auto; }
}
@media (max-width: 1023px) {
  .catalog-filter__fields { grid-template-columns: 1fr 1fr; }
  .catalog-filter__check { grid-column: 1 / -1; min-height: 44px; }
  .catalog-filter__reset { grid-column: 1 / -1; justify-self: stretch; min-height: 44px; }
}
@media (max-width: 767px) {
  .products.products--filtered { gap: 28px; }
  .catalog-filter { position: static; padding: 16px; border-radius: 16px; }
  .catalog-filter__fields { grid-template-columns: 1fr; gap: 0; margin-top: 12px; }
  .catalog-filter__field { padding: 0 0 14px; }
  .catalog-filter__check { padding: 10px 0 14px; border-top: 0; }
  .catalog-filter__reset { width: 100%; }
}
`;

const DOM_C = () => {
  const aside = document.querySelector('.catalog-filter');
  const head = document.createElement('div');
  head.className = 'catalog-filter__head';
  head.innerHTML = '<h2 class="catalog-filter__title">Filter</h2><p class="catalog-filter__count">2 Produkte</p>';
  aside.prepend(head);
  window.__mockSync = () => {
    const count = document.querySelectorAll('.product--visible').length;
    document.querySelector('.catalog-filter__count').textContent = count === 1 ? '1 Produkt' : `${count} Produkte`;
  };
};

const VARIANTS = {
  a: { css: CSS_A, dom: DOM_A },
  b: { css: CSS_B, dom: DOM_B },
  c: { css: CSS_C, dom: DOM_C },
};

async function inject(page, variant) {
  const v = VARIANTS[variant];
  await page.addStyleTag({ content: v.css });
  await page.evaluate(v.dom);
  await sleep(400);
}

async function applyDiameter(page, value) {
  await page.evaluate(() => document.querySelectorAll('.catalog-filter .ss-main')[1].click());
  await page.waitForSelector('.ss-content.ss-open', { timeout: 5000 });
  await sleep(300);
  const ok = await page.evaluate(v => {
    const content = document.querySelector('.ss-content.ss-open');
    const opt = [...content.querySelectorAll('.ss-option')].find(el => el.textContent.trim() === v);
    if (!opt) return false;
    opt.click();
    return true;
  }, value);
  await sleep(700);
  await page.evaluate(() => document.querySelector('.catalog-filter .ss-main')?.blur?.());
  await sleep(250);
  return ok;
}

const state = async page => page.evaluate(() => ({
  url: location.search,
  products: document.querySelectorAll('.product--visible').length,
  empty: Boolean(document.querySelector('.catalog-filter__empty')),
  resetDisabled: document.querySelector('.catalog-filter__reset').disabled,
  values: [...document.querySelectorAll('.catalog-filter select')].map(s => s.value),
  checked: document.querySelector('[name="configurator"]').checked,
  title: document.querySelector('.catalog-filter__title')?.textContent || null,
  count: document.querySelector('.catalog-filter__count')?.textContent || null,
  chipCount: document.querySelectorAll('.catalog-filter__chip').length,
}));

const measurePage = page => page.evaluate(() => {
  const box = s => { const el = document.querySelector(s); if (!el) return null; const r = el.getBoundingClientRect(); return { x: +r.x.toFixed(1), y: +r.y.toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1) }; };
  const cs = s => { const el = document.querySelector(s); if (!el) return null; const c = getComputedStyle(el); const r = el.getBoundingClientRect(); return { font: `${c.fontWeight} ${c.fontSize}/${c.lineHeight} ${c.fontFamily}`, color: c.color, background: c.backgroundColor, radius: c.borderTopLeftRadius, border: `${c.borderTopWidth} ${c.borderTopColor}`, padding: c.padding, w: +r.width.toFixed(1), h: +r.height.toFixed(1) }; };
  return {
    filter: cs('.catalog-filter'), title: cs('.catalog-filter__title'), field: cs('.catalog-filter__field'),
    ss: cs('.ss-main.catalog-filter__select'), checkbox: cs('.catalog-filter__check input'), reset: cs('.catalog-filter__reset'),
    boxes: { filter: box('.catalog-filter'), ss: box('.ss-main.catalog-filter__select'), reset: box('.catalog-filter__reset'), checkbox: box('.catalog-filter__check input') },
    count: document.querySelector('.catalog-filter__count')?.textContent || null,
  };
});

const browser = await launch();
const dec = await decoder(browser);
const report = {};

for (const variant of ['a', 'b', 'c']) {
  const entry = { screenshots: [] };

  // desktop
  let page = await openPage(browser, { width: 1440, height: 1000 });
  await inject(page, variant);
  await frameFilter(page);
  await page.screenshot({ path: path.join(OUT, `variant-${variant}-1440.png`) });
  entry.screenshots.push(`variant-${variant}-1440.png`);
  entry.desktop = await measurePage(page);

  const applied = await applyDiameter(page, '16');
  await page.evaluate(() => window.__mockSync?.());
  await sleep(300);
  entry.picked = { clicked: applied, ...(await state(page)) };
  await frameFilter(page);
  await page.screenshot({ path: path.join(OUT, `variant-${variant}-applied-1440.png`) });
  entry.screenshots.push(`variant-${variant}-applied-1440.png`);

  await page.evaluate(() => document.querySelector('.catalog-filter__reset').click());
  await sleep(700);
  await page.evaluate(() => window.__mockSync?.());
  entry.reset = await state(page);
  await frameFilter(page);
  await page.screenshot({ path: path.join(OUT, `variant-${variant}-reset-1440.png`) });
  entry.screenshots.push(`variant-${variant}-reset-1440.png`);
  await page.close();

  // desktop closeup (dpr 2)
  page = await openPage(browser, { width: 1440, height: 1000, dpr: 2 });
  await inject(page, variant);
  await frameFilter(page);
  await elemShot(page, '.catalog-filter', path.join(OUT, `variant-${variant}-filter-1440.png`));
  await page.close();

  // mobile 390
  page = await openPage(browser, { width: 390, height: 844 });
  await inject(page, variant);
  await frameFilter(page);
  await page.screenshot({ path: path.join(OUT, `variant-${variant}-390.png`) });
  entry.screenshots.push(`variant-${variant}-390.png`);
  entry.mobile = await measurePage(page);

  const appliedM = await applyDiameter(page, '16');
  await page.evaluate(() => window.__mockSync?.());
  await sleep(300);
  entry.mobilePicked = { clicked: appliedM, ...(await state(page)) };
  await frameFilter(page);
  await page.screenshot({ path: path.join(OUT, `variant-${variant}-applied-390.png`) });
  entry.screenshots.push(`variant-${variant}-applied-390.png`);

  await page.evaluate(() => document.querySelector('.catalog-filter__reset').click());
  await sleep(700);
  await page.evaluate(() => window.__mockSync?.());
  entry.mobileReset = await state(page);
  await page.close();

  report[variant] = entry;
}

fs.writeFileSync(path.join(OUT, 'variants-measurements.json'), JSON.stringify(report, null, 2));
await dec.close();
await browser.close();
console.log('DONE');


