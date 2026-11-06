import { AdminNotificationView } from '../views/admin/AdminNotificationView.js?v=20261106.1';
import {settingsApi} from '../api/settingsApi.js?v=20261106.1';
import {authApi} from '../api/authApi.js?v=20261106.1';
import {escapeHtml as esc} from '../utils/text.js?v=20261106.1';

const textFields = {
  company_name: ['Название компании в письмах', 'text', 255],
  contact_email: ['Почта для писем', 'email', 255],
  contact_phone: ['Телефон в письмах', 'tel', 100],
  site_url: ['Адрес сайта для писем', 'url', 255],
  telegram_chat_id: ['Номер чата в Telegram', 'text', 255],
  manager_notification_email: ['Почта менеджера', 'email', 255],
};
const flags = {
  email_notifications_enabled: 'Письмо клиенту о заявке',
  telegram_notifications_enabled: 'Уведомление менеджеру в Telegram',
  manager_email_notifications_enabled: 'Копия заявки на почту менеджера',
};
const hints = {
  site_url: 'Например: https://example.ru',
  telegram_chat_id: 'Куда приходят уведомления. Номер подскажет техник.',
  manager_notification_email: 'Сюда придёт копия каждой заявки.',
};

export class AdminSettingsController {
  constructor(root) {
    this.root = root;
    this.ready = false;
    this.busy = false;
    this.section = 'all';
    this.baseline = '';
    this.events = new AbortController();
    window.addEventListener('company-settings-changed',event=>{if(event.detail!=='settings')this.ready=false;},{signal:this.events.signal});
    this.view = {root, allowDiscard: () => !this.dirty() || window.confirm('Выйти без сохранения?')};
    root.innerHTML = `<header class="panel__head"><h1 class="panel__title">Настройки и пароль</h1></header>
      <p>Данные компании и уведомления о заявках. Эти же данные есть в «Контактах»; почту и Telegram настраивает техник — галочка сама отправку не включает.</p>
      <button class="btn" type="button" data-settings-refresh>Обновить</button>
      <p role="status" data-settings-status></p><div data-settings-editor></div>
      <details class="admin-disclosure settings-card--disclosure"><summary>Сменить пароль</summary>
        <form class="settings-card settings-card--password" data-password-form>
          <div class="settings-card__grid">
            <label class="field">Текущий пароль<input class="field__input" name="current_password" type="password" autocomplete="current-password" required></label>
            <label class="field">Новый пароль<input class="field__input" name="new_password" type="password" autocomplete="new-password" minlength="8" required></label>
            <label class="field">Повторите новый пароль<input class="field__input" name="confirm_password" type="password" autocomplete="new-password" minlength="8" required></label>
            <p class="settings-card__hint">Минимум 8 символов. После смены пароля потребуется войти заново.</p>
          </div>
          <div class="settings-card__actions">
            <button class="btn btn--primary" type="submit">Сменить пароль</button>
          </div>
          <p role="status" data-password-status class="settings-card__status"></p>
        </form>
      </details>`;
    const options = {signal: this.events.signal};
    root.querySelector('[data-settings-refresh]').addEventListener('click', () => this.load(), options);
    root.addEventListener('submit', event => {
      event.preventDefault();
      if (!event.target.reportValidity()) return;
      if (event.target.matches('[data-password-form]')) this.changePassword(event.target);
      else this.save();
    }, options);
    window.addEventListener('beforeunload', event => {
      if (this.dirty()) {event.preventDefault(); event.returnValue = '';}
    }, options);
  }
  values() {
    const form = this.root.querySelector('[data-settings-form]');
    if (!form) return {};
    const values = Object.fromEntries(new FormData(form));
    const result = {};
    for (const key of Object.keys(textFields)) result[key] = values[key]?.trim() || null;
    for (const key of Object.keys(flags)) result[key] = form.elements[key].checked;
    return result;
  }
  dirty() {return !!this.baseline && JSON.stringify(this.values()) !== this.baseline;}
  message(message, type = 'info') {AdminNotificationView.message(this.root.querySelector('[data-settings-status]'), message, type);}
  lock(value) {this.busy = value; this.root.querySelectorAll('button,input').forEach(input => input.disabled = value);}
  render(item) {
    this.root.querySelector('[data-settings-editor]').innerHTML = `<form class="settings-card" data-settings-form>
      <div class="settings-card__grid">
        ${Object.entries(textFields).map(([name, [label, type, max]]) => `<label class="field">${label}<input class="field__input" name="${name}" type="${type}" maxlength="${max}" ${name === 'company_name' ? 'required' : ''} value="${esc(item[name] || '')}">${hints[name]?`<small class="field__hint">${hints[name]}</small>`:''}</label>`).join('')}
      </div>
      <div class="settings-card__flags">
        ${Object.entries(flags).map(([name,label]) => `<label class="settings-card__flag"><input name="${name}" type="checkbox" ${item[name] ? 'checked' : ''}> <span>${label}</span></label>`).join('')}
      </div>
      <div class="settings-card__actions">
        <button class="btn btn--primary" type="submit">Сохранить настройки</button>
      </div></form>`;
    this.baseline = JSON.stringify(this.values());
  }
  async load() {
    if (this.busy || !this.view.allowDiscard()) return;
    this.lock(true);
    try {this.render(await settingsApi.get()); this.ready = true;}
    catch {this.message('Не удалось загрузить настройки. Нажмите «Обновить».', 'error');}
    finally {this.lock(false);}
  }
  async save() {
    if (this.busy || !this.ready) return;
    const data = this.values();
    if (!data.company_name) {this.message('Укажите название компании.', 'warning'); return;}
    if (data.site_url && !/^https?:\/\//i.test(data.site_url)) {this.message('Укажите адрес сайта с http:// или https://.', 'warning'); return;}
    if (data.telegram_notifications_enabled && !data.telegram_chat_id) {this.message('Укажите номер чата в Telegram.', 'warning'); return;}
    if (data.manager_email_notifications_enabled && !data.manager_notification_email) {this.message('Укажите почту менеджера.', 'warning'); return;}
    this.lock(true); this.message('Сохраняем…');
    try {this.render(await settingsApi.save(data));window.dispatchEvent(new CustomEvent('company-settings-changed',{detail:'settings'})); this.message('Настройки сохранены.', 'success');}
    catch {this.message('Не сохранилось. Проверьте поля и нажмите «Сохранить настройки» ещё раз.', 'error');}
    finally {this.lock(false);}
  }
  async changePassword(form) {
    if (this.busy) return;
    const data = Object.fromEntries(new FormData(form));
    const status = form.querySelector('[data-password-status]');
    if (data.new_password !== data.confirm_password) {AdminNotificationView.message(status, 'Новые пароли не совпадают.', 'warning'); return;}
    this.lock(true); AdminNotificationView.message(status, 'Меняем пароль…');
    try {
      await settingsApi.changePassword(data);
      form.reset(); authApi.clearSession(); this.baseline = '';
      status.textContent = 'Пароль изменён. Войдите заново.';
      window.location.replace('/login/');
    } catch {form.reset(); AdminNotificationView.message(status, 'Не удалось сменить пароль. Попробуйте ещё раз.', 'error');}
    finally {this.lock(false);}
  }
  async select() {}
  async remove() {}
  destroy() {this.events.abort();}
}
