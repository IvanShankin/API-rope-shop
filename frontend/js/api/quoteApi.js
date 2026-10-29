import { apiClient } from './apiClient.js?v=20261027.10';
import { API_CONFIG } from './config.js?v=20261027.10';

export const quoteApi = {
  /**
   * Отправить новую заявку из конфигуратора (публичный эндпоинт)
   * @param {Object} data - QuoteRequestCreate DTO
   */
  async createQuoteRequest(data) {
    return apiClient.post(API_CONFIG.ENDPOINTS.QUOTE_REQUESTS, data);
  },

  /**
   * Получить список заявок (для панели управления, требуется роль ADMIN)
   * @param {Object} [params] - фильтры (status, search, skip, limit и др.)
   */
  async listQuoteRequests(params = {}) {
    const result = await apiClient.get(API_CONFIG.ENDPOINTS.QUOTE_REQUESTS, {
      params,
      requiresAuth: true,
    });
    return API_CONFIG.CATALOG_V2 ? result.items : result;
  },

  /**
   * Получить подробную информацию о заявке
   * @param {number} id
   */
  async getQuoteRequest(id) {
    return apiClient.get(API_CONFIG.ENDPOINTS.QUOTE_REQUEST_DETAIL(id), {
      requiresAuth: true,
    });
  },

  /**
   * Изменить статус заявки (admin)
   * @param {number} id
   * @param {string} status - 'new', 'in_progress', 'confirmed', 'completed', 'cancelled'
   */
  async updateStatus(id, status) {
    return apiClient.patch(`${API_CONFIG.ENDPOINTS.QUOTE_REQUEST_DETAIL(id)}/status`, { status }, {
      requiresAuth: true,
    });
  },
  update: (id, data) => apiClient.patch(API_CONFIG.ENDPOINTS.QUOTE_REQUEST_DETAIL(id), data, { requiresAuth: true }),
  remove: id => apiClient.delete(API_CONFIG.ENDPOINTS.QUOTE_REQUEST_DETAIL(id), { requiresAuth: true }),
};
