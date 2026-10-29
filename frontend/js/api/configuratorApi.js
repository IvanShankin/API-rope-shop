import { apiClient } from './apiClient.js?v=20261027.10';
import { apiLocale } from '../i18n/locale.js?v=20261027.10';
import { API_CONFIG } from './config.js?v=20261027.10';
import { normalizeProduct } from './productAdapter.js?v=20261027.10';

let sharedData = null;
export const configuratorApi = {
  async getData(type, locale = apiLocale(), { refresh = false } = {}) {
    // One snapshot per page and language. Explicit retries fetch fresh prices.
    if (refresh || !sharedData || sharedData.locale !== locale) {
      const entry = { locale };
      entry.promise = apiClient.get('/configurators', { params: { locale } })
        .catch(error => { if (sharedData === entry) sharedData = null; throw error; });
      sharedData = entry;
    }
    const data = structuredClone(await sharedData.promise);
    if (type !== 'rope_with_splice') {
      const category = type === 'loop_only' ? 'loop' : 'splice';
      data.splice_types = data.splice_types?.filter(item => item.category === category);
      const ids = new Set((data.splice_types || []).map(item => Number(item.id)));
      data.splice_price_rules = data.splice_price_rules?.filter(item => ids.has(Number(item.splice_type_id)));
      data.extras = data.extras?.filter(item => item.billing_type !== 'per_meter');
      data.rope_products = null;
    }
    data.apiVersion = API_CONFIG.CATALOG_V2 ? 2 : 1;
    if (!data?.settings || !['extras', 'splice_materials', 'splice_types', 'splice_price_rules'].every(key => Array.isArray(data[key]))
      || (type === 'rope_with_splice' && !Array.isArray(data.rope_products))) {
      throw new Error('Сервер вернул неполные данные конфигуратора.');
    }
    if (Array.isArray(data.rope_products)) data.rope_products = data.rope_products.map(product => ({ ...normalizeProduct(product),
      name: product.name || product.construction || 'Канат',
      description: [product.core_description,product.cover_description].filter(Boolean).join(' · '),
    }));
    return data;
  },
  /**
   * Получить глобальные настройки конфигуратора
   */
  async getSettings() {
    return apiClient.get(API_CONFIG.ENDPOINTS.CONFIGURATOR_SETTINGS);
  },

  /**
   * Получить дополнительные платные опции (чехлы, бирки)
   * @param {Object} [params] - { locale, is_active, billing_type }
   */
  async getExtras(params = {}) {
    return apiClient.get(API_CONFIG.ENDPOINTS.CONFIGURATOR_EXTRAS, { params });
  },

  /**
   * Получить список всех типов заделок / сплайсов
   * @param {Object} [params] - { locale, is_active, category }
   */
  async getSpliceTypes(params = {}) {
    return apiClient.get(API_CONFIG.ENDPOINTS.SPLICE_TYPES, { params });
  },

  /**
   * Получить применимые правила цен на сплайс
   * @param {Object} params - { material_id, diameter, splice_type_ids }
   */
  async getApplicableSplicePrices(params) {
    return apiClient.get(API_CONFIG.ENDPOINTS.SPLICE_PRICES_APPLICABLE, { params });
  },

  /**
   * Получить цвета с локализацией
   * @param {Object} [params] - { locale, is_active }
   */
  async getColors(params = {}) {
    return apiClient.get(API_CONFIG.ENDPOINTS.COLORS, { params });
  },
};
