import { apiClient } from './apiClient.js?v=20261027.10';
import { API_CONFIG } from './config.js?v=20261027.10';
import { apiLocale } from '../i18n/locale.js?v=20261027.10';
import { normalizeProduct } from './productAdapter.js?v=20261027.10';

export const productsApi = {
  async getCatalogFilters() {
    if (!API_CONFIG.CATALOG_V2) return { constructions: [] };
    return apiClient.get('/catalog/filters', { params: { locale: apiLocale() } });
  },
  async listDetailedProducts(params = {}) {
    if (API_CONFIG.CATALOG_V2) {
      const result = await apiClient.get('/products', { params: { locale: apiLocale(), is_active: true, product_type: 'rope', ...params } });
      if (!Array.isArray(result?.items)) throw new Error('Некорректный ответ каталога');
      return result.items.filter(p => p.price_unit === 'meter').map(p => ({ ...normalizeProduct(p), material_group_id: p.category_id }));
    }
    const products = await this.listRopeProducts(params);
    if (!Array.isArray(products)) throw new Error('Некорректный ответ каталога');
    return Promise.all(products.map(async (product) => {
      const detail = await this.getRopeProduct(product.product_id);
      return {
        ...product, ...detail,
        name: detail.name || detail.construction || 'Канат',
        description: [detail.core_description, detail.cover_description].filter(Boolean).join(' · '),
        variants: (detail.variants || []).filter((variant) => variant.is_active !== false),
      };
    }));
  },

  async getMaterialGroups() {
    if (API_CONFIG.CATALOG_V2) {
      const result = await apiClient.get('/categories', { params: { locale: apiLocale(), is_active: true } });
      if (!Array.isArray(result?.items)) throw new Error('Не получены разделы каталога');
      return result.items;
    }
    return apiClient.get(API_CONFIG.ENDPOINTS.MATERIAL_GROUPS, { params: { locale: apiLocale(), is_active: true } });
  },
  /**
   * Получить список канатов
   * @param {Object} [params] - { material_group_id, can_be_spliced }
   */
  async listRopeProducts(params = {}) {
    return apiClient.get(API_CONFIG.ENDPOINTS.ROPE_PRODUCTS, { params });
  },

  /**
   * Получить детальную информацию о канате (с вариантами, цветами и доступными сплайсами)
   * @param {number} productId
   */
  async getRopeProduct(productId) {
    return apiClient.get(API_CONFIG.ENDPOINTS.ROPE_PRODUCT_DETAIL(productId));
  },

  /**
   * Получить список вариантов диаметров конкретного каната
   * @param {number} productId
   * @param {boolean} [isActive=true]
   */
  async listProductVariants(productId, isActive = true) {
    return apiClient.get(API_CONFIG.ENDPOINTS.ROPE_VARIANTS(productId), {
      params: { is_active: isActive },
    });
  },

  /**
   * Получить список цветов каната
   * @param {number} productId
   * @param {string} [locale] - 'ru', 'en', 'de'
   */
  async getProductColors(productId, locale = null) {
    return apiClient.get(API_CONFIG.ENDPOINTS.ROPE_PRODUCT_COLORS(productId), {
      params: locale ? { locale } : {},
    });
  },
};
