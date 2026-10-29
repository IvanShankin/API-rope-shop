const assert = require('node:assert/strict');
const mod = require('./frontend-module.cjs');
(async () => {
  const { canonicalUrl, pages, pageMetadata } = await mod('seo/metadata.js');
  const { getLanguage } = await mod('i18n/locale.js');
  const origin = 'https://example.test';
  assert.equal(canonicalUrl(`${origin}/category.html?lang=en&group=12&diameter=8&utm_source=x#item`, 'en', origin), `${origin}/category/?group=12&lang=en`);
  assert.equal(canonicalUrl(`${origin}/category/?group=13&lang=de`, 'de', origin), `${origin}/category/?group=13`);
  assert.equal(canonicalUrl(`${origin}/index.html?lang=ru`, 'ru', origin), `${origin}/?lang=ru`);
  assert.notEqual(canonicalUrl(`${origin}/category/?group=12`, 'de', origin), canonicalUrl(`${origin}/category/?group=13`, 'de', origin));
  for (const route of Object.keys(pages)) for (const language of ['de','en','ru']) {
    const row = pageMetadata(route, language);
    assert.ok(row.title && row.description);
    assert.equal(new URL(canonicalUrl(origin+route, language, origin)).searchParams.get('lang'), language === 'de' ? null : language);
  }
  assert.match(pageMetadata('/category/', 'de', 'Test & Seile').title, /^Test & Seile/);
  global.window = {location:{search:'',pathname:'/'},localStorage:{getItem:()=> 'ru'}};
  assert.equal(getLanguage(),'de');
  window.location.search='?lang=en';assert.equal(getLanguage(),'en');
  window.location.search='?lang=invalid';assert.equal(getLanguage(),'de');
  window.location.pathname='/admin/';assert.equal(getLanguage(),'ru');
  console.log('PASS: canonical language/category identity, filters, aliases, metadata and deterministic default language');
})().catch(error => { console.error(error); process.exitCode = 1; });
