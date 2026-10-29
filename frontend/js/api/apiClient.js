import { API_CONFIG } from './config.js?v=20261027.10';

/**
 * Базовый HTTP-клиент для взаимодействия с бэкендом Rope-Pro-Line
 */
export class ApiClient {
  constructor(baseUrl = API_CONFIG.BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Получить access токен из localStorage
   */
  getAccessToken() {
    return localStorage.getItem(API_CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
  }

  /**
   * Сохранить токены
   */
  setTokens(accessToken, refreshToken) {
    if (accessToken) localStorage.setItem(API_CONFIG.STORAGE_KEYS.ACCESS_TOKEN, accessToken);
    if (refreshToken) localStorage.setItem(API_CONFIG.STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
  }

  /**
   * Очистить токены
   */
  clearTokens() {
    localStorage.removeItem(API_CONFIG.STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(API_CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(API_CONFIG.STORAGE_KEYS.USER_INFO);
  }

  // Read expiry only to schedule renewal. Identity and permissions are checked by the server.
  isAccessTokenExpired() {
    try {
      const payload = this.getAccessToken().split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      const { exp } = JSON.parse(atob(payload));
      return typeof exp === 'number' && exp * 1000 <= Date.now() + 30000;
    } catch { return false; }
  }

  async renewSession() {
    if (!this.refreshing) {
      const refreshToken = localStorage.getItem(API_CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
      this.refreshing = (async () => {
        if (!refreshToken) throw Object.assign(new Error('Войдите заново: сессия истекла.'), { status: 401 });
        const tokens = await this.post(API_CONFIG.ENDPOINTS.AUTH_REFRESH,
          { refresh_token: refreshToken }, { retried: true });
        if (!tokens?.access_token || !tokens?.refresh_token) throw new Error('Сервер не вернул обновлённую сессию.');
        this.setTokens(tokens.access_token, tokens.refresh_token);
      })().catch(error => {
        // This backend returns 404 when the refresh token no longer exists.
        if ([401, 403, 404].includes(error.status)) {
          this.clearTokens();
          throw Object.assign(new Error('Войдите заново: сессия истекла.'), { status: 401 });
        }
        throw error;
      }).finally(() => { this.refreshing = null; });
    }
    return this.refreshing;
  }

  /**
   * Базовый метод запроса
   */
  async request(endpoint, options = {}) {
    const {
      method = 'GET',
      data = null,
      params = null,
      headers = {},
      requiresAuth = false,
      timeout = API_CONFIG.TIMEOUT_MS,
      retried = false,
    } = options;

    let url = `${this.baseUrl}${endpoint}`;

    // Добавляем query параметры к URL
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          if (Array.isArray(value)) {
            value.forEach((v) => searchParams.append(key, v));
          } else {
            searchParams.append(key, value);
          }
        }
      });
      const queryStr = searchParams.toString();
      if (queryStr) {
        url += (url.includes('?') ? '&' : '?') + queryStr;
      }
    }

    const requestHeaders = {
      'Accept': 'application/json',
      ...headers,
    };
    // Free ngrok shows a browser warning page instead of the API response without this header.
    if (/ngrok/i.test(this.baseUrl)) {
      requestHeaders['ngrok-skip-browser-warning'] = 'true';
    }

    // Renew before sending an expired JWT: the current backend returns 500 for it.
    if (requiresAuth && !retried && endpoint !== API_CONFIG.ENDPOINTS.AUTH_REFRESH && this.isAccessTokenExpired()) {
      await this.renewSession();
    }
    // Автоматическая авторизация
    const token = this.getAccessToken();
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    } else if (requiresAuth) {
      throw new Error('Требуется авторизация');
    }

    // Если отправляем JSON
    let body = null;
    if (data) {
      if (data instanceof FormData) {
        body = data;
        // Для FormData браузер сам установит Content-Type с boundary
      } else {
        requestHeaders['Content-Type'] = 'application/json';
        body = JSON.stringify(data);
      }
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        method,
        headers: requestHeaders,
        body,
        signal: controller.signal,
      });

      // Проверка на 204 No Content
      if (response.status === 204) {
        return null;
      }

      const isJson = response.headers.get('content-type')?.includes('application/json');
      const responseData = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        if (response.status === 401 && requiresAuth && !retried && endpoint !== API_CONFIG.ENDPOINTS.AUTH_REFRESH
          && localStorage.getItem(API_CONFIG.STORAGE_KEYS.REFRESH_TOKEN)) {
          if (token !== this.getAccessToken() && this.getAccessToken()) {
            return this.request(endpoint, { ...options, retried: true });
          }
          await this.renewSession();
          return this.request(endpoint,{...options,retried:true});
        }
        const errorMessage = (isJson && responseData.detail)
          ? (typeof responseData.detail === 'string' ? responseData.detail : JSON.stringify(responseData.detail))
          : `HTTP Error ${response.status}: ${response.statusText}`;

        const error = new Error(errorMessage);
        error.status = response.status;
        error.data = responseData;
        throw error;
      }

      return responseData;
    } catch (err) {
      if (err.name === 'AbortError') {
        throw new Error(`Превышено время ожидания ответа сервера (${timeout} мс)`);
      }
      throw err;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  post(endpoint, data, options = {}) {
    return this.request(endpoint, { ...options, method: 'POST', data });
  }

  patch(endpoint, data, options = {}) {
    return this.request(endpoint, { ...options, method: 'PATCH', data });
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
}

// Экспортируем синглтон клиент
export const apiClient = new ApiClient();
