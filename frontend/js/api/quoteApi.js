import { apiClient } from './apiClient.js?v=20261106.1';
import { API_CONFIG } from './config.js?v=20261106.1';

export const quoteApi = {
  /**
   * Отправить новую заявку из конфигуратора (публичный эндпоинт)
   * @param {Object} data - QuoteRequestCreate DTO
   */
  async createQuoteRequest(data) {
    return apiClient.post(API_CONFIG.ENDPOINTS.QUOTE_REQUESTS, data);
  },

  /**
   * Предварительный расчёт стоимости без создания заявки (публичный эндпоинт).
   * Тело как у заявки, но без контактов: configurator_type, is_urgent, locale, *_items.
   */
  calculate(data) {
    return apiClient.post(API_CONFIG.ENDPOINTS.QUOTE_CALCULATE, data);
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
    return result.items;
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

  update: (id, data) => apiClient.patch(API_CONFIG.ENDPOINTS.QUOTE_REQUEST_DETAIL(id), data, { requiresAuth: true }),
  remove: id => apiClient.delete(API_CONFIG.ENDPOINTS.QUOTE_REQUEST_DETAIL(id), { requiresAuth: true }),
};
