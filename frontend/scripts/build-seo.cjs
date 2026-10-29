// Generates reviewable publication artifacts only; does not change server configuration.
const fs = require('node:fs');
const path = require('node:path');
const mod = require('./frontend-module.cjs');
const escapeXml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
(async () => {
  const { seoConfig } = await mod('seo/config.js');
  const { pages, canonicalUrl } = await mod('seo/metadata.js');
  const preview = process.argv.includes('--preview');
  const origin = preview ? 'http://localhost:8082' : seoConfig.origin;
  if (!origin) throw Error('Set the confirmed domain in js/seo/config.js first, or use --preview.');
  const parsed = new URL(origin);
  if (!preview && (parsed.protocol !== 'https:' || parsed.origin !== origin || parsed.hostname === 'localhost' || parsed.hostname.endsWith('.test') || parsed.hostname.endsWith('.invalid') || parsed.username || parsed.password)) throw Error('Production origin must be a bare public HTTPS origin without a trailing slash.');
  const categoryArg = process.argv.find(arg => arg.startsWith('--categories='));
  if (!preview && !categoryArg) throw Error('Pass --categories=path.json with reviewed active category IDs (an empty array is allowed). Do not publish local DEMO IDs.');
  const ids = categoryArg ? JSON.parse(fs.readFileSync(categoryArg.slice('--categories='.length), 'utf8')) : [];
  if (!Array.isArray(ids) || ids.some(id => !Number.isSafeInteger(id) || id <= 0)) throw Error('Category manifest must be an array of positive integer IDs.');
  const routes = [...Object.keys(pages), ...new Set(ids.map(id => `/category/?group=${id}`))];
  const entries = [];
  for (const route of routes) for (const lang of seoConfig.languages) {
    const input = new URL(route, origin).href;
    const alternates = [...seoConfig.languages, 'x-default'].map(code => `<xhtml:link rel="alternate" hreflang="${code}" href="${escapeXml(canonicalUrl(input, code === 'x-default' ? seoConfig.defaultLanguage : code, origin))}"/>`).join('');
    entries.push(`  <url><loc>${escapeXml(canonicalUrl(input,lang,origin))}</loc>${alternates}</url>`);
  }
  const output = path.join('.local', preview ? 'seo-preview' : 'seo-release');
  fs.mkdirSync(output, { recursive:true });
  fs.writeFileSync(path.join(output,'sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n${entries.join('\n')}\n</urlset>\n`);
  // Keep CSS/JS/API crawlable: they are needed to render the public catalogue.
  // Service pages use their own noindex, so robots.txt must not hide that directive.
  fs.writeFileSync(path.join(output,'robots.txt'), preview ? 'User-agent: *\nDisallow: /\n' : `User-agent: *\nDisallow: /scripts/\nDisallow: /docs/\nDisallow: /.local/\n\nSitemap: ${origin}/sitemap.xml\n`);
  fs.writeFileSync(path.join(output,'README.txt'), preview ? 'LOCAL PREVIEW ONLY. Do not upload these files. Category IDs are omitted unless explicitly supplied.\n' : 'Review these files before publication. Server must expose /robots.txt and /sitemap.xml; current nginx does not. Never serve the project root publicly without an explicit allowlist.\n');
  console.log(`${preview ? 'PREVIEW' : 'RELEASE CANDIDATE'}: ${entries.length} URLs in ${output}`);
})().catch(error => { console.error(error.message); process.exitCode = 1; });
