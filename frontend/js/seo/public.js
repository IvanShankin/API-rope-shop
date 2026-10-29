import { getLanguage } from '../i18n/locale.js?v=20261027.10';
import { seoConfig } from './config.js?v=20261027.10';
import { canonicalUrl, pageMetadata, pagePath } from './metadata.js?v=20261027.10';

let categoryName = '';
let categoryState = 'loading';
function meta(key, value, property = false) {
  const attribute = property ? 'property' : 'name';
  let node = document.head.querySelector(`meta[${attribute}="${key}"]`);
  if (!node) { node = document.createElement('meta'); node.setAttribute(attribute, key); document.head.append(node); }
  node.content = value;
}
function link(rel, href, language) {
  const node = document.createElement('link'); node.rel = rel; node.href = href; node.dataset.seo = '';
  if (language) node.hreflang = language;
  document.head.append(node);
}

export function updateSeo() {
  const path = pagePath(location.pathname), language = getLanguage();
  const data = pageMetadata(path, language, categoryName);
  if (!data) return;
  document.title = data.title;
  meta('description', data.description);
  document.head.querySelectorAll('[data-seo]').forEach(node => node.remove());
  const missing = path === '/category/' && categoryState === 'missing';
  const error = path === '/category/' && categoryState === 'error';
  let robots = document.head.querySelector('meta[data-seo-robots]');
  if (missing || error) {
    if (!robots) { robots = document.createElement('meta'); robots.name = 'robots'; robots.dataset.seoRobots = ''; document.head.append(robots); }
    robots.content = 'noindex, follow';
    document.title = ({ de: 'Kategorie nicht verfügbar', en: 'Category unavailable', ru: 'Раздел недоступен' })[language] + ' | Rope-Pro-Line';
  } else robots?.remove();
  const origin = seoConfig.origin || location.origin;
  const canonical = canonicalUrl(location.href, language, origin);
  // Local URLs are preview-only until the production origin has been confirmed.
  document.documentElement.dataset.seoOrigin = seoConfig.origin ? 'configured' : 'preview';
  if (!missing && !error) {
    link('canonical', canonical);
    for (const lang of seoConfig.languages) link('alternate', canonicalUrl(location.href, lang, origin), lang);
    link('alternate', canonicalUrl(location.href, seoConfig.defaultLanguage, origin), 'x-default');
  }
  meta('og:title', document.title, true); meta('og:description', data.description, true);
  meta('og:type', 'website', true); meta('og:site_name', 'Rope-Pro-Line', true);
  meta('og:url', canonical, true); meta('og:locale', {de:'de_DE',en:'en_GB',ru:'ru_RU'}[language], true);
  if (missing || error) return;
  const graph = [{ '@type': 'Organization', '@id': `${origin}/#organization`, name: 'Rope-Pro-Line', url: `${origin}/` },
    { '@type': 'WebSite', '@id': `${origin}/#website`, name: 'Rope-Pro-Line', url: `${origin}/`, inLanguage: seoConfig.languages,
      publisher: { '@id': `${origin}/#organization` } }];
  if (path !== '/') {
    const home = {de:'Startseite',en:'Home',ru:'Главная'}[language];
    const items = [{ '@type':'ListItem', position:1, name:home, item:canonicalUrl(`${origin}/`,language,origin) }];
    if (path === '/category/') items.push({ '@type':'ListItem', position:2, name:{de:'Katalog',en:'Catalogue',ru:'Каталог'}[language], item:canonicalUrl(`${origin}/catalog/`,language,origin) });
    items.push({ '@type':'ListItem', position:items.length+1, name:categoryName || document.querySelector('h1')?.textContent.trim() || data.title, item:canonical });
    graph.push({ '@type':'BreadcrumbList', itemListElement:items });
  }
  const json = document.createElement('script'); json.type = 'application/ld+json'; json.dataset.seo = '';
  json.textContent = JSON.stringify({ '@context':'https://schema.org', '@graph':graph }); document.head.append(json);
}

document.addEventListener('seo:category', event => { categoryName = event.detail.name || ''; categoryState = event.detail.state; updateSeo(); });
window.addEventListener('popstate', updateSeo);
document.addEventListener('seo:url', updateSeo);
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', updateSeo, { once:true });
else updateSeo();
