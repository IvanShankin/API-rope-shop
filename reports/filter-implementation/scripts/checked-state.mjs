import { launch, openPage, frameFilter, state, sleep } from './lib.mjs';

const browser = await launch();
const page = await openPage(browser, { width: 1440, height: 1000 });
await page.evaluate(() => document.querySelector('[name="configurator"]').click());
await sleep(900);
const st = await state(page);
await frameFilter(page);
await page.screenshot({ path: 'reports/filter-implementation/after-checked-1440.png' });
console.log(JSON.stringify(st));
await page.close();
await browser.close();
console.log('CHECKED DONE');
