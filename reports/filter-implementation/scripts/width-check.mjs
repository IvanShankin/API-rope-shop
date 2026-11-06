import { launch, openPage, measurements, state, foreignColors, OUT, sleep } from './lib.mjs';
import fs from 'node:fs';
import path from 'node:path';

const browser = await launch();
const result = {};
for (const [name, width, height] of [['tablet768', 768, 900], ['tablet1024', 1024, 900]]) {
  const page = await openPage(browser, { width, height });
  result[name] = {
    measurements: await measurements(page),
    state: await state(page),
    foreign: (await foreignColors(page)).length,
    columns: await page.evaluate(() => getComputedStyle(document.querySelector('.products--filtered')).gridTemplateColumns),
  };
  await page.evaluate(() => {
    const f = document.querySelector('.catalog-filter');
    window.scrollTo({ top: Math.max(0, f.getBoundingClientRect().top + window.scrollY - 160), behavior: 'instant' });
  });
  await sleep(600);
  await page.screenshot({ path: path.join(OUT, `check-${width}.png`) });
  await page.close();
}
fs.writeFileSync(path.join(OUT, 'width-check.json'), JSON.stringify(result, null, 2));
await browser.close();
console.log('WIDTHS DONE');
