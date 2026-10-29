/**
 * Конфигурация API клиента и эндпоинтов бэкенда
 */
export const API_CONFIG = {
  // Current API contract is independent of the hostname/port. Legacy previews
  // can explicitly override these values before loading the application.
  BASE_URL: window.__API_BASE_URL__ || '/api',
  CATALOG_V2: window.__API_CATALOG_V2__ ?? true,
  SPLICE_DETAIL: window.__API_SPLICE_DETAIL__ ?? true,
  // No public company-contact endpoint exists in the current backend.
  PUBLIC_CONTACTS_URL: window.__PUBLIC_CONTACTS_URL__ || null,

  // Таймаут запросов по умолчанию (мс)
  TIMEOUT_MS: 15000,

  // Эндпоинты бэкенда (согласно API-rope-shop)
  ENDPOINTS: {
    // Аутентификация и пользователи
    AUTH_LOGIN: '/auth/login',
    AUTH_REGISTER: '/auth/register',
    AUTH_REFRESH: '/auth/refresh_tokens',
    AUTH_LOGOUT: '/auth/logout',
    USERS_ME: '/users/me',

    // Товары и канаты
    ROPE_PRODUCTS: '/rope_products',
    ROPE_PRODUCT_DETAIL: (id) => `/rope_products/${id}`,
    ROPE_VARIANTS: (productId) => `/rope_products/${productId}/variants`,

    // Цвета
    COLORS: '/colors',
    ROPE_PRODUCT_COLORS: (productId) => `/rope_product_colors/by-product/${productId}`,

    // Материалы
    MATERIALS: '/materials',
    MATERIAL_GROUPS: '/material_groups',

    // Заделки и правила цен
    SPLICE_TYPES: '/splice_types',
    SPLICE_MATERIALS: '/splice_materials',
    SPLICE_PRICES: '/splice_prices',
    SPLICE_PRICES_APPLICABLE: '/splice_prices/applicable',

    // Настройки конфигуратора и доп. опции
    CONFIGURATOR_SETTINGS: '/configurator_settings',
    CONFIGURATOR_EXTRAS: '/configurator_extras',

    // Заявки и заказы
    QUOTE_REQUESTS: '/quote_requests',
    QUOTE_REQUEST_DETAIL: (id) => `/quote_requests/${id}`,
  },

  // Ключи локального хранилища
  STORAGE_KEYS: {
    ACCESS_TOKEN: 'rope_access_token',
    REFRESH_TOKEN: 'rope_refresh_token',
    USER_INFO: 'rope_user_info',
    CURRENT_LANG: 'rope_lang',
  }
};
