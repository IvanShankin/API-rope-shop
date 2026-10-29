import { BaseModel } from './BaseModel.js?v=20261027.10';
import { authApi } from '../api/authApi.js?v=20261027.10';

/**
 * Модель сессии пользователя и администратора
 */
export class AuthModel extends BaseModel {
  constructor() {
    super();
    this.user = null;
    this.isLoading = false;
  }

  get isAuthenticated() {
    return Boolean(this.user && authApi.isAuthenticated());
  }

  get isAdmin() {
    return this.user?.role === 'admin';
  }

  async checkSession() {
    if (!authApi.isAuthenticated()) {
      this.user = null;
      this.emit('auth:changed', this.user);
      return null;
    }

    try {
      this.isLoading = true;
      this.user = await authApi.getMe();
      this.emit('auth:changed', this.user);
      return this.user;
    } catch (err) {
      this.user = null;
      if (err.status === 401) {
        // A temporary network/server failure is not evidence of expired credentials.
        authApi.clearSession();
        this.emit('auth:changed', null);
        return null;
      }
      throw err;
    } finally {
      this.isLoading = false;
    }
  }

  async login(username, password) {
    this.isLoading = true;
    try {
      await authApi.login(username, password);
      this.user = await authApi.getMe();
      this.emit('auth:login_success', this.user);
      return this.user;
    } catch (err) {
      this.emit('auth:login_error', err);
      throw err;
    } finally {
      this.isLoading = false;
    }
  }

  async logout() {
    try {
      await authApi.logout();
    } finally {
      this.user = null;
      this.emit('auth:logout', null);
    }
  }
}
