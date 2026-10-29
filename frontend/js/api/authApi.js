import { apiClient } from './apiClient.js?v=20261027.10';
import { API_CONFIG } from './config.js?v=20261027.10';

export const authApi = {
  clearSession() { apiClient.clearTokens(); },
  /**
   * Вход по логину/email и паролю (OAuth2 Password flow)
   * @param {string} username
   * @param {string} password
   */
  async login(username, password) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const result = await apiClient.post(API_CONFIG.ENDPOINTS.AUTH_LOGIN, formData);
    if (result && result.access_token) {
      apiClient.setTokens(result.access_token, result.refresh_token);
    }
    return result;
  },

  /**
   * Получить профиль текущего пользователя
   */
  async getMe() {
    const user = await apiClient.get(API_CONFIG.ENDPOINTS.USERS_ME, { requiresAuth: true });
    // Temporary compatibility for the local backend whose profile DTO omits role.
    // The protected endpoint checks ADMIN on the server; a token alone is not proof.
    if (user && user.role == null
      && ['localhost', '127.0.0.1'].includes(window.location.hostname)) {
      try {
        const requests = await apiClient.get(API_CONFIG.ENDPOINTS.QUOTE_REQUESTS, {
          params: { limit: 1 }, requiresAuth: true,
        });
        if (!Array.isArray(requests)) throw new Error('Некорректный ответ проверки прав администратора');
        return { ...user, role: 'admin' };
      } catch (error) {
        if (error.status === 403) return { ...user, role: 'user' };
        throw error;
      }
    }
    return user;
  },

  /**
   * Обновить токен
   * @param {string} refreshToken
   */
  async refreshTokens(refreshToken) {
    const result = await apiClient.post(API_CONFIG.ENDPOINTS.AUTH_REFRESH, {
      refresh_token: refreshToken,
    });
    if (result && result.access_token) {
      apiClient.setTokens(result.access_token, result.refresh_token);
    }
    return result;
  },

  /**
   * Выход из системы
   */
  async logout() {
    const refreshToken = localStorage.getItem(API_CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
    try {
      if (refreshToken) {
        await apiClient.post(API_CONFIG.ENDPOINTS.AUTH_LOGOUT, {
          refresh_token: refreshToken,
        }, { requiresAuth: true });
      }
    } finally {
      apiClient.clearTokens();
    }
  },

  /**
   * Проверить, авторизован ли пользователь
   */
  isAuthenticated() {
    return Boolean(apiClient.getAccessToken());
  },
};
