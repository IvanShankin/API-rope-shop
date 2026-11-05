import fs from 'node:fs';
import path from 'node:path';
import { launch, openPage, frameFilter, measurements, state, readCls, OUT, sleep } from './lib.mjs';

const browser = await launch();
const result = { capturedAt: new Date().toISOString(), desktop: {}, mobile: {}, states: {}, cls: {} };

let page = await openPage(browser, { width: 1440, height: 1000 });
result.desktop = await measurements(page);
result.states.default = await state(page);
result.cls.desktop = await readCls(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'before-1440.png') });
await page.close();

page = await openPage(browser, { width: 390, height: 844 });
result.mobile = await measurements(page);
result.states.mobileDefault = await state(page);
result.cls.mobile = await readCls(page);
await frameFilter(page);
await page.screenshot({ path: path.join(OUT, 'before-390.png') });
await page.close();

fs.writeFileSync(path.join(OUT, 'before-measurements.json'), JSON.stringify(result, null, 2));
await browser.close();
console.log('BEFORE DONE');
