import puppeteer from 'puppeteer-core';

const browser = await puppeteer.connect({
  browserWSEndpoint: 'ws://127.0.0.1:9233/devtools/browser/398fdc1e-49be-4e2a-af94-f57b61a9dcb9',
  defaultViewport: { width: 1440, height: 900 },
});
const page = await browser.newPage();
await page.goto('http://localhost/catalog/', { waitUntil: 'networkidle0', timeout: 30000 });
const title = await page.title();
const url = page.url();
console.log(JSON.stringify({ title, url }));
await browser.disconnect();
