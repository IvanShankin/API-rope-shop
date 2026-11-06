/**
 * Конфигурация API клиента и эндпоинтов бэкенда
 */
export const API_CONFIG = {
  // Адрес API не зависит от домена; при необходимости переопределяется в remote-api.js.
  BASE_URL: window.__API_BASE_URL__ || '/api',
  // Public company contacts (GET /settings/public: company_name, contact_email, contact_phone).
  PUBLIC_CONTACTS_URL: window.__PUBLIC_CONTACTS_URL__ || '/settings/public',

  // Таймаут запросов по умолчанию (мс)
  TIMEOUT_MS: 15000,

  // Эндпоинты бэкенда (согласно API-rope-shop)
  ENDPOINTS: {
    // Аутентификация и пользователи
    AUTH_LOGIN: '/auth/login',
    AUTH_REFRESH: '/auth/refresh_tokens',
    AUTH_LOGOUT: '/auth/logout',
    USERS_ME: '/users/me',

    // Заявки и заказы
    QUOTE_REQUESTS: '/quote_requests',
    QUOTE_CALCULATE: '/quote_requests/calculate',
    QUOTE_REQUEST_DETAIL: (id) => `/quote_requests/${id}`,
  },

  // Ключи локального хранилища
  STORAGE_KEYS: {
    ACCESS_TOKEN: 'rope_access_token',
    REFRESH_TOKEN: 'rope_refresh_token',
    USER_INFO: 'rope_user_info',
  }
};
