import { BaseController } from './BaseController.js?v=20261116.1';
import { AuthModel } from '../models/AuthModel.js?v=20261116.1';
import { NotificationView } from '../views/common/NotificationView.js?v=20261116.1';

export class LoginController extends BaseController {
  constructor() {
    super();
    this.authModel = new AuthModel();
  }

  async init() {
    await super.init();

    // Куда вернуться после входа: только страницы самой панели (/admin/...), иначе на /admin/.
    const next = new URLSearchParams(location.search).get('next') || '';
    const target = /^\/admin(?:[/?#]|$)/.test(next) ? next : '/admin/';

    // 1. Если администратор уже имеет валидную сессию, перенаправляем в панель
    try {
      const user = await this.authModel.checkSession();
      if (user && user.role === 'admin') {
        window.location.replace(target);
        return;
      }
    } catch (_) {
      // Игнорируем ошибку при первом входе
    }

    const form = document.querySelector('#admin-login-form');
    if (!form) return;

    // Кнопка-глаз: показать/скрыть пароль. Перед отправкой пароль снова скрывается.
    const passwordInput = form.querySelector('#auth-password');
    const eye = form.querySelector('[data-password-toggle]');
    const setVisible = visible => {
      if (!passwordInput || !eye) return;
      passwordInput.type = visible ? 'text' : 'password';
      const label = visible ? 'Скрыть пароль' : 'Показать пароль';
      eye.setAttribute('aria-pressed', String(visible));
      eye.setAttribute('aria-label', label);
      eye.title = label;
    };
    eye?.addEventListener('click', () => {
      const pos = passwordInput.selectionStart;
      setVisible(passwordInput.type === 'password');
      passwordInput.focus();
      if (pos != null) passwordInput.setSelectionRange(pos, pos);
    });

    const errorEl = document.querySelector('#auth-error-msg');
    const submitBtn = document.querySelector('#auth-submit-btn');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      setVisible(false);
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
        window.location.replace(target);
      } catch (err) {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span class="btn-text">Войти в панель</span>';
        }

        let message;
        if (err.status === 401 || err.status === 400) message = 'Неверный логин или пароль';
        else if (err.network) message = 'Сервер недоступен, проверьте подключение';
        else if (err.status === 429) message = 'Слишком много попыток входа, подождите немного';
        else message = err.message || 'Не удалось войти, попробуйте ещё раз';

        if (errorEl) {
          errorEl.textContent = message;
          errorEl.style.display = 'block';
        }
      }
    });
  }
}
