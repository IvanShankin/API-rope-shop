import { seoConfig } from './config.js?v=20261027.10';

// Texts describe existing services; no invented prices, ratings or company details.
export const pages = {
  '/': {
    de: ['Seile und professioneller Spleißservice | Rope-Pro-Line', 'Seile, Spleißarbeiten und individuelle Seillösungen von Rope-Pro-Line. Entdecken Sie den Katalog und konfigurieren Sie Ihre Anfrage.'],
    en: ['Ropes and professional splicing | Rope-Pro-Line', 'Ropes, professional splicing and individual rope solutions. Explore the Rope-Pro-Line catalogue and configure your enquiry.'],
    ru: ['Канаты и профессиональное сращивание | Rope-Pro-Line', 'Канаты, профессиональное сращивание и индивидуальные решения Rope-Pro-Line. Выберите канат в каталоге и рассчитайте свою заявку.'],
  },
  '/catalog/': {
    de: ['Seilkatalog: Kategorien und Auswahl | Rope-Pro-Line', 'Entdecken Sie die Seilkategorien von Rope-Pro-Line. Vergleichen Sie die verfügbaren Modelle und wählen Sie ein Seil für Ihre Anwendung.'],
    en: ['Rope catalogue: categories and selection | Rope-Pro-Line', 'Explore rope categories from Rope-Pro-Line. Compare available models and choose a rope for your application.'],
    ru: ['Каталог канатов: категории и выбор | Rope-Pro-Line', 'Категории канатов Rope-Pro-Line. Сравните доступные модели и выберите канат для своей задачи.'],
  },
  '/category/': {
    de: ['Seile: Modelle und Durchmesser | Rope-Pro-Line', 'Vergleichen Sie Seile, Durchmesser und Eigenschaften im Katalog von Rope-Pro-Line und stellen Sie Ihre Anfrage zusammen.'],
    en: ['Ropes: models and diameters | Rope-Pro-Line', 'Compare ropes, diameters and specifications in the Rope-Pro-Line catalogue and prepare your enquiry.'],
    ru: ['Канаты: модели и диаметры | Rope-Pro-Line', 'Сравните канаты, диаметры и характеристики в каталоге Rope-Pro-Line и подготовьте свою заявку.'],
  },
  '/configurator/': {
    de: ['Seil- und Spleißkonfiguratoren | Rope-Pro-Line', 'Konfigurieren Sie Seile, Schlaufen und Spleißarbeiten. Wählen Sie die verfügbaren Optionen und senden Sie Ihre individuelle Anfrage an Rope-Pro-Line.'],
    en: ['Rope and splicing configurators | Rope-Pro-Line', 'Configure ropes, loops and splicing work. Select the available options and send your individual enquiry to Rope-Pro-Line.'],
    ru: ['Конфигураторы канатов и сращивания | Rope-Pro-Line', 'Настройте канат, петли и работы по сращиванию. Выберите доступные параметры и отправьте индивидуальную заявку в Rope-Pro-Line.'],
  },
  '/b2b/': {
    de: ['Seile und Spleißarbeiten für Unternehmen | Rope-Pro-Line', 'Individuelle Seillösungen und Spleißarbeiten für Unternehmen. Beschreiben Sie Ihre Anforderungen und fragen Sie bei Rope-Pro-Line an.'],
    en: ['Ropes and splicing for businesses | Rope-Pro-Line', 'Individual rope solutions and splicing services for businesses. Describe your requirements and contact Rope-Pro-Line.'],
    ru: ['Канаты и сращивание для бизнеса | Rope-Pro-Line', 'Индивидуальные решения из канатов и работы по сращиванию для бизнеса. Опишите задачу и отправьте запрос в Rope-Pro-Line.'],
  },
  '/b2c/': {
    de: ['Seile und Spleißservice für Privatkunden | Rope-Pro-Line', 'Seile und individuelle Spleißarbeiten für Privatkunden. Teilen Sie Rope-Pro-Line Ihre Wünsche für Ihr Projekt mit.'],
    en: ['Ropes and splicing for private customers | Rope-Pro-Line', 'Ropes and individual splicing services for private customers. Tell Rope-Pro-Line what you need for your project.'],
    ru: ['Канаты и сращивание для частных клиентов | Rope-Pro-Line', 'Канаты и индивидуальные работы по сращиванию для частных клиентов. Расскажите Rope-Pro-Line о своей задаче.'],
  },
};

export function pagePath(pathname) {
  if (/^\/index(?:\.html|\/)?$/.test(pathname)) return '/';
  return pathname.replace(/\.html$/, '/').replace(/^(\/(?:catalog|category|configurator|b2b|b2c))$/, '$1/');
}

export function canonicalUrl(input, language, origin) {
  const source = new URL(input);
  const url = new URL(pagePath(source.pathname), origin || source.origin);
  if (url.pathname === '/category/' && source.searchParams.has('group')) {
    url.searchParams.set('group', source.searchParams.get('group'));
  }
  if (language !== seoConfig.defaultLanguage) url.searchParams.set('lang', language);
  return url.href;
}

export function pageMetadata(path, language, categoryName = '') {
  const row = pages[path]?.[language];
  if (!row) return null;
  if (path !== '/category/' || !categoryName) return { title: row[0], description: row[1] };
  const suffix = { de: 'Seilkatalog', en: 'Rope catalogue', ru: 'Каталог канатов' }[language];
  return { title: `${categoryName} | ${suffix} | Rope-Pro-Line`, description: `${categoryName}. ${row[1]}` };
}
