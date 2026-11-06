import { apiClient } from './apiClient.js?v=20261106.1';
import { API_CONFIG } from './config.js?v=20261106.1';

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
    // /users/me returns role; admin rights are still checked by the server on every admin request.
    return apiClient.get(API_CONFIG.ENDPOINTS.USERS_ME, { requiresAuth: true });
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
