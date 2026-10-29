import { catalogLink, updateLoadState } from '../../ui/load-state.js?v=20261027.10';
import { BaseView } from '../BaseView.js?v=20261027.10';
import { escapeHtml as esc } from '../../utils/text.js?v=20261027.10';
import { translate } from '../../i18n/translate.js?v=20261027.10';
import { getLanguage } from '../../i18n/locale.js?v=20261027.10';
import { mediaUrl } from '../../utils/media.js?v=20261027.10';

const filterLabels = {
  title: ['Фильтр', 'Filter', 'Filter'],
  construction: ['Конструкция', 'Construction', 'Konstruktion'],
  all: ['Все варианты', 'All options', 'Alle Varianten'],
  diameter: ['Диаметр, мм', 'Diameter, mm', 'Durchmesser, mm'],
  configurator: ['Можно собрать в конфигураторе', 'Available in the configurator', 'Im Konfigurator verfügbar'],
  reset: ['Сбросить фильтр', 'Reset filter', 'Filter zurücksetzen'],
  count: ['Найдено товаров:', 'Products found:', 'Gefundene Produkte:'],
  empty: ['По этим параметрам товаров нет. Измените или сбросьте фильтр.', 'No products match these parameters. Change or reset the filter.', 'Keine passenden Produkte. Ändern Sie den Filter oder setzen Sie ihn zurück.'],
  emptyCategory: ['В этом разделе пока нет товаров.', 'There are no products in this category yet.', 'In dieser Kategorie gibt es noch keine Produkte.'],
};
const label = key => filterLabels[key][{ ru: 0, en: 1, de: 2 }[getLanguage()] ?? 0];

export class CatalogView extends BaseView {
  constructor(root) {
    super(root);
    if (!this.root) return;
    this.groupsPage = this.root.dataset.catalog === 'groups';
    this.container = document.createElement('div');
    this.container.className = this.groupsPage ? 'catalog__inner' : 'products__items';
    this.root.replaceChildren(this.container);
    if (!this.groupsPage) {
      this.root.classList.add('products--filtered');
      this.sidebar = document.createElement('aside');
      this.sidebar.className = 'catalog-filter';
      this.sidebar.hidden = true;
      this.sidebar.setAttribute('aria-label', label('title'));
      this.root.prepend(this.sidebar);
      this.sidebar.addEventListener('change', () => this.onFilterChange?.({
        construction: this.sidebar.querySelector('[name="construction"]').value,
        diameter: this.sidebar.querySelector('[name="diameter"]').value,
        configurator: this.sidebar.querySelector('[name="configurator"]').checked,
      }));
      this.sidebar.addEventListener('click', event => {
        if (event.target.closest('[data-filter-reset]')) this.onFilterChange?.({});
      });
    }
  }

  renderFilters(options, constructions, filters) {
    if (!this.sidebar) return;
    const codes = [...new Set([...options.constructions, filters.construction].filter(Boolean))];
    const diameters = [...new Set([...options.diameters, filters.diameter].filter(Boolean).map(Number))].sort((a, b) => a - b);
    this.sidebar.innerHTML = `<fieldset class="catalog-filter__fields">
        <label class="catalog-filter__field">${label('construction')}
          <select name="construction" class="catalog-filter__select"><option value="">${label('all')}</option>${codes.map(code => `<option value="${esc(code)}">${esc(constructions.find(c => c.code === code)?.name || code)}</option>`).join('')}</select>
        </label>
        <label class="catalog-filter__field">${label('diameter')}
          <select name="diameter" class="catalog-filter__select"><option value="">${label('all')}</option>${diameters.map(d => `<option value="${d}">${d}</option>`).join('')}</select>
        </label>
        <label class="catalog-filter__check"><input type="checkbox" name="configurator"><span>${label('configurator')}</span></label>
        <button class="catalog-filter__reset" type="button" data-filter-reset>${label('reset')}</button>
      </fieldset>`;
    this.sidebar.hidden = false;
  }

  syncFilters(filters) {
    if (!this.sidebar || this.sidebar.hidden) return;
    this.sidebar.querySelector('fieldset').disabled = false;
    for (const key of ['construction', 'diameter']) this.sidebar.querySelector(`[name="${key}"]`).value = filters[key];
    this.sidebar.querySelector('[name="configurator"]').checked = filters.configurator;
    this.sidebar.querySelector('[data-filter-reset]').disabled = !Object.values(filters).some(Boolean);
  }

  initControls(onRetry) {
    const controls = document.createElement('div');
    controls.className = 'catalog-controls';
    controls.hidden = true;
    this.controls = controls;
    this.retry = document.createElement('button');
    this.retry.type = 'button';
    this.retry.className = 'button button--ghost button--small';
    this.retry.textContent = 'Повторить загрузку';
    this.retry.hidden = true;
    this.retry.addEventListener('click', onRetry);
    this.catalogLink = catalogLink();
    controls.append(this.retry, this.catalogLink);
    this.root.append(controls);
  }

  setTitle(name) {
    if (this.groupsPage) return;
    const title = document.querySelector('#page-title');
    if (title) title.textContent = name || 'Все канаты';
    document.title = `${name || translate('Все канаты', getLanguage())} — Rope-Pro-Line`;
    const crumb = document.querySelector('.breadcrumbs__current');
    if (crumb) crumb.textContent = name || 'Все канаты';
  }

  showStatus(message, retry = false, state = retry ? 'error' : 'empty') {
    const status = document.createElement('p');
    status.setAttribute('role', 'status');
    status.textContent = message;
    this.container.replaceChildren(status);
    updateLoadState(this.root, status, state);
    this.catalogLink.hidden = this.groupsPage || state === 'loading';
    if (this.retry) this.retry.hidden = !retry;
    if (this.controls) this.controls.hidden = !retry && this.catalogLink.hidden;
    if (this.sidebar?.querySelector('fieldset')) this.sidebar.querySelector('fieldset').disabled = true;
  }

  renderProducts(products, groups) {
    this.retry.hidden = true;
    this.controls.hidden = true;
    this.root.setAttribute('aria-busy', 'false');
    this.root.dataset.loadState = 'ready';
    if (!products.length && !this.groupsPage) {
      const message = document.createElement('p'); message.className = 'catalog-filter__empty'; message.textContent = label(this.emptyCategory?'emptyCategory':'empty'); this.container.replaceChildren(message);
      return;
    }
    if (this.groupsPage) {
      const populated = groups.filter(group => group.is_active !== false);
      if (!populated.length) { this.showStatus('Доступных товаров пока нет.', true, 'empty'); return; }
      this.container.innerHTML = `<ul class="catalog__list">${populated.map((group, index) => {
        const items = products.filter((p) => Number(p.material_group_id) === Number(group.id));
        const prices = items.flatMap((p) => p.variants).filter(v => v.price_per_meter != null).map((v) => Number(v.price_per_meter)).filter(Number.isFinite);
        const picture = mediaUrl(group.image_url);
        return `<li class="catalog__item ${index === 0 ? 'catalog__item--wide' : index === 1 ? 'catalog__item--medium' : ''}">
          <a class="catalog__card category category--text" href="/category/?group=${Number(group.id)}">
            ${picture ? `<span class="category__media"><img class="category__image" src="${esc(picture)}" alt="" width="960" height="640" loading="lazy" decoding="async"></span>` : ''}
            <span class="category__info"><span class="category__title">${esc(group.name || group.code)}</span>
            <span class="category__specs">${items.length} моделей</span>
            <span class="category__price">${prices.length ? `от ${Math.min(...prices)} €/м` : items.length ? 'Нет доступных диаметров' : 'Товары пока не добавлены.'}</span></span>
          </a></li>`;
      }).join('')}</ul>`;
      return;
    }
    this.container.innerHTML = products.map((product, index) => `
      <article class="product product--api product--visible ${index % 2 ? 'product--reverse' : ''}" data-product-id="${Number(product.product_id)}">
        <div class="product__gallery">
          <div class="product__media">
            <img class="product__image" src="${esc(mediaUrl(product.main_image_url) || (index % 2 ? '/img/works/rope-red.jpg' : '/img/works/rope-blue.jpg'))}" alt="${esc(product.main_image_url ? product.name : 'Тестовое фото каната')}" loading="lazy">
          </div>
          ${product.main_image_url ? '' : '<p class="product__maker">Тестовое фото</p>'}
        </div>
        <div class="product__info">
          <h2 class="product__title">${esc(product.name)}</h2>
          <p class="product__text">${esc(product.description)}</p>
          <div class="product__table-wrap"><table class="product__table">
            <thead><tr class="product__row product__row--head"><th class="product__cell">Диаметр, мм</th><th class="product__cell">Нагрузка, daN</th><th class="product__cell">Вес, г/м</th><th class="product__cell product__cell--price">Цена, €/м</th></tr></thead>
            <tbody>${product.variants.map((variant) => `<tr class="product__row"><td class="product__cell product__cell--key">${esc(variant.diameter_mm)}</td><td class="product__cell">${esc(variant.breaking_load_dan ?? '—')}</td><td class="product__cell">${esc(variant.weight_g_per_m ?? '—')}</td><td class="product__cell product__cell--price">${esc(variant.price_per_meter)}</td></tr>`).join('')}</tbody>
          </table></div>
          ${product.variants.length && product.has_configurator !== false ? `<a class="button button--primary" href="/configurator/?product=${Number(product.product_id)}">Собрать трос</a>` : product.variants.length ? '' : '<p>Нет доступных диаметров.</p>'}
        </div>
      </article>`).join('');
  }
}
