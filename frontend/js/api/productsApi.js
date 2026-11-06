import { apiClient } from './apiClient.js?v=20261106.1';
import { apiLocale } from '../i18n/locale.js?v=20261106.1';
import { normalizeProduct } from './productAdapter.js?v=20261106.1';

export const productsApi = {
  async getCatalogFilters() {
    return apiClient.get('/catalog/filters', { params: { locale: apiLocale() } });
  },
  async listDetailedProducts(params = {}) {
    const result = await apiClient.get('/products', { params: { locale: apiLocale(), is_active: true, product_type: 'rope', ...params } });
    if (!Array.isArray(result?.items)) throw new Error('Некорректный ответ каталога');
    return result.items.filter(p => p.price_unit === 'meter').map(p => ({ ...normalizeProduct(p), material_group_id: p.category_id }));
  },

  async getMaterialGroups() {
    const result = await apiClient.get('/categories', { params: { locale: apiLocale(), is_active: true } });
    if (!Array.isArray(result?.items)) throw new Error('Не получены разделы каталога');
    return result.items;
  },
};
