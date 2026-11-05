import fs from 'node:fs';
import path from 'node:path';
import { launch, openPage, frameFilter, openDropdown, pickOpenOption, OUT, sleep } from './lib.mjs';

const browser = await launch();
const result = {};

const page = await openPage(browser, { width: 1440, height: 1000 });
await frameFilter(page);
await openDropdown(page, 1);
await pickOpenOption(page, '16');
await page.mouse.move(700, 900);
await sleep(300);
await frameFilter(page);
await page.hover('.catalog-filter__reset');
await sleep(500);
result.resetHover = await page.evaluate(() => {
  const c = getComputedStyle(document.querySelector('.catalog-filter__reset'));
  return { background: c.backgroundColor, border: c.borderTopColor };
});
await page.screenshot({ path: path.join(OUT, 'after-hover-reset-1440.png') });
await page.hover('.catalog-filter__check input');
await sleep(500);
result.checkboxHover = await page.evaluate(() => getComputedStyle(document.querySelector('.catalog-filter__check input')).borderTopColor);
await page.mouse.move(700, 900);
await sleep(300);
await page.evaluate(() => document.querySelector('.catalog-filter .ss-main').focus());
await page.keyboard.press('Enter');
await sleep(500);
result.keyboardOpen = await page.evaluate(() => ({
  open: Boolean(document.querySelector('.ss-content.ss-open')),
  focused: document.activeElement?.className,
}));
await page.keyboard.press('Escape');
await sleep(400);
result.keyboardClose = await page.evaluate(() => Boolean(document.querySelector('.ss-content.ss-open')));
await page.screenshot({ path: path.join(OUT, 'after-keyboard-1440.png') });
const title = await page.evaluate(() => document.querySelector('.catalog-filter__title')?.textContent);
result.titleAfterKeyboard = title;
await page.close();

fs.writeFileSync(path.join(OUT, 'states-extra.json'), JSON.stringify(result, null, 2));
await browser.close();
console.log(JSON.stringify(result));
