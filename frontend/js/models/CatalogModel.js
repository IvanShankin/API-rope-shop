import { BaseModel } from './BaseModel.js?v=20261027.10';

/**
 * Модель каталога канатов
 */
export class CatalogModel extends BaseModel {
  constructor() {
    super();
    this.products = [];
    this.materialGroups = [];
    this.activeFilterGroupId = null;
    this.filters = { construction: '', diameter: '', configurator: false };
  }

  setData({ products, materialGroups }) {
    this.products = products || [];
    this.materialGroups = materialGroups || [];
    this.emit('data:loaded', this.getFilteredProducts());
  }

  setFilterGroup(groupId) {
    this.activeFilterGroupId = groupId ? Number(groupId) : null;
    this.emit('filter:changed', this.getFilteredProducts());
  }

  getFilteredProducts() {
    return this.products.filter((product) => {
      // Фильтр по группе материалов
      if (this.activeFilterGroupId && Number(product.material_group_id) !== this.activeFilterGroupId) {
        return false;
      }
      if (this.filters.construction && product.construction_type !== this.filters.construction) return false;
      if (this.filters.diameter && !(product.variants || []).some(v => v.is_active !== false && Number(v.diameter_mm) === Number(this.filters.diameter))) return false;
      if (this.filters.configurator && (product.has_configurator === false || !(product.variants || []).some(v => v.is_active !== false))) return false;
      return true;
    });
  }

  setFilters(values = {}) {
    const diameter = Number(values.diameter);
    this.filters = {
      construction: String(values.construction || '').slice(0, 50),
      diameter: Number.isFinite(diameter) && diameter > 0 ? String(diameter) : '',
      configurator: values.configurator === true || values.configurator === '1',
    };
    this.emit('filter:changed', this.getFilteredProducts());
  }

  getFilterOptions() {
    const products = this.products.filter(p => !this.activeFilterGroupId || Number(p.material_group_id) === this.activeFilterGroupId);
    return {
      constructions: [...new Set(products.map(p => p.construction_type).filter(Boolean))],
      diameters: [...new Set(products.flatMap(p => p.variants || []).filter(v => v.is_active !== false).map(v => Number(v.diameter_mm)).filter(n => Number.isFinite(n) && n > 0))].sort((a, b) => a - b),
    };
  }
}
