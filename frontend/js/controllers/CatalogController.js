import { loadErrorMessage } from '../ui/load-state.js?v=20261027.10';
import { BaseController } from './BaseController.js?v=20261027.10';
import { CatalogModel } from '../models/CatalogModel.js?v=20261027.10';
import { CatalogView } from '../views/catalog/CatalogView.js?v=20261027.10';
import { productsApi } from '../api/productsApi.js?v=20261027.10';

export class CatalogController extends BaseController {
  constructor() {
    super();
    this.model = new CatalogModel();
    this.view = new CatalogView('[data-catalog]');
  }

  async init() {
    if (!this.view.root) return;
    await super.init();

    const render = (products) => {
      this.view.renderProducts(products, this.model.materialGroups);
      this.view.syncFilters(this.model.filters, products.length);
    };
    this.model.on('data:loaded', render);
    this.model.on('filter:changed', render);
    this.view.initControls(() => this.loadCatalog());
    if (!this.view.groupsPage) {
      this.readFilters();
      this.view.onFilterChange = values => {
        this.model.setFilters(values);
        const url = new URL(window.location.href);
        for (const [key, value] of Object.entries(this.model.filters)) {
          if (value) url.searchParams.set(key, value === true ? '1' : value);
          else url.searchParams.delete(key);
        }
        window.history.pushState(null, '', url);
        document.dispatchEvent(new Event('seo:url'));
        this.syncLanguageLinks();
      };
      this.onPopState = () => { this.readFilters(); this.syncLanguageLinks(); };
      window.addEventListener('popstate', this.onPopState);
    }

    await this.loadCatalog();
  }

  async loadCatalog() {
    if (this.loading) return;
    this.loading = true;
    this.view.showStatus('Загружаем каталог…', false, 'loading');
    try {
      const group = new URLSearchParams(window.location.search).get('group');
      const metadataTask = this.view.groupsPage ? Promise.resolve(null)
        : productsApi.getCatalogFilters().catch(() => null);
      const [products, materialGroups] = await Promise.all([
        productsApi.listDetailedProducts(!this.view.groupsPage && group ? { category_id: group } : {}),
        productsApi.getMaterialGroups(),
      ]);
      if (!Array.isArray(materialGroups)) throw new Error('Не получены разделы каталога');
      if (group && !materialGroups.some((item) => Number(item.id) === Number(group))) { this.view.setTitle('Раздел не найден'); this.view.showStatus('Раздел не найден. Перейдите в каталог.', false, 'missing'); document.dispatchEvent(new CustomEvent('seo:category', {detail:{state:'missing'}})); return; }
      this.model.activeFilterGroupId = group ? Number(group) : null;
      this.view.emptyCategory = Boolean(group && !products.length);
      this.view.setTitle(materialGroups.find((item) => Number(item.id) === Number(group))?.name);
      if (!this.view.groupsPage) document.dispatchEvent(new CustomEvent('seo:category', {detail:{state:'ready',name:materialGroups.find(item => Number(item.id) === Number(group))?.name || ''}}));
      this.model.setData({ products, materialGroups });
      this.view.renderFilters(this.model.getFilterOptions(), [], this.model.filters);
      this.view.syncFilters(this.model.filters, this.model.getFilteredProducts().length);
      const metadata = await metadataTask;
      this.view.renderFilters(this.model.getFilterOptions(), metadata?.constructions || [], this.model.filters);
      this.view.syncFilters(this.model.filters, this.model.getFilteredProducts().length);
    } catch (err) {
      this.view.showStatus(loadErrorMessage(err), true);
      if (!this.view.groupsPage) document.dispatchEvent(new CustomEvent('seo:category', {detail:{state:'error'}}));
    } finally {
      this.loading = false;
    }
  }

  readFilters() {
    this.model.setFilters(Object.fromEntries(new URLSearchParams(window.location.search)));
  }

  syncLanguageLinks() {
    document.querySelectorAll('[data-lang]').forEach(link => {
      const url = new URL(window.location.href);
      if (link.dataset.lang === 'de') url.searchParams.delete('lang');
      else url.searchParams.set('lang', link.dataset.lang);
      link.href = url.pathname + url.search + url.hash;
    });
  }

  destroy() {
    window.removeEventListener('popstate', this.onPopState);
    super.destroy();
  }
}
