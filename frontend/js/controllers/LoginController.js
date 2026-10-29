import { BaseController } from './BaseController.js?v=20261027.10';
import { AuthModel } from '../models/AuthModel.js?v=20261027.10';
import { NotificationView } from '../views/common/NotificationView.js?v=20261027.10';

export class LoginController extends BaseController {
  constructor() {
    super();
    this.authModel = new AuthModel();
  }

  async init() {
    await super.init();

    // 1. Если администратор уже имеет валидную сессию, перенаправляем в панель
    try {
      const user = await this.authModel.checkSession();
      if (user && user.role === 'admin') {
        window.location.replace('/admin/');
        return;
      }
    } catch (_) {
      // Игнорируем ошибку при первом входе
    }

    const form = document.querySelector('#admin-login-form');
    if (!form) return;

    const errorEl = document.querySelector('#auth-error-msg');
    const submitBtn = document.querySelector('#auth-submit-btn');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (errorEl) errorEl.style.display = 'none';

      const username = form.username.value.trim();
      const password = form.password.value;

      if (!username || !password) {
        if (errorEl) {
          errorEl.textContent = 'Пожалуйста, укажите логин и пароль';
          errorEl.style.display = 'block';
        }
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="admin-spinner" style="width: 18px; height: 18px; border-width: 2px;"></div> Вход...';
      }

      try {
        const user = await this.authModel.login(username, password);
        if (!user || user.role !== 'admin') {
          await this.authModel.logout();
          throw new Error('Доступ запрещен: учетная запись не обладает правами администратора');
        }

        NotificationView.success('Успешный вход', 'Перенаправление в панель управления...');
        window.location.replace('/admin/');
      } catch (err) {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span class="btn-text">Войти в панель</span>';
        }

        let message = 'Неверный логин или пароль';
        if (err.message && err.message !== 'Failed to fetch') {
          message = err.message;
        } else if (err.status === 401 || err.status === 400) {
          message = 'Неверный логин или пароль';
        } else if (err.message === 'Failed to fetch') {
          message = 'Сервер бэкенда недоступен (проверьте подключение)';
        }

        if (errorEl) {
          errorEl.textContent = message;
          errorEl.style.display = 'block';
        }
      }
    });
  }
}
