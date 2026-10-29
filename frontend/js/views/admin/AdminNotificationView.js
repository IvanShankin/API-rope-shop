const titles = { success: 'Готово', error: 'Ошибка', warning: 'Обратите внимание', notice: 'Уведомление' };

/** Shared feedback for admin actions. Informational form hints stay inline. */
export class AdminNotificationView {
  static container = null;
  static entries = new Map();

  static message(element, message, type = 'info') {
    if (element) {
      // Only one live region announces an action result, rather than both copies.
      if (type === 'info') {
        element.setAttribute('role', 'status');
        element.setAttribute('aria-live', 'polite');
      } else {
        element.removeAttribute('role');
        element.removeAttribute('aria-live');
      }
      element.textContent = message;
    }
    if (type !== 'info') {
      const section = element?.closest('.panel')?.querySelector('h1')?.textContent?.trim();
      this.show({ message, type, section });
    }
  }

  static show({ message = '', type = 'notice', title = titles[type], section = '' }) {
    if (typeof document === 'undefined' || !document.body) return;
    if (!Object.hasOwn(titles, type)) type = 'notice';
    const key = JSON.stringify([type, title, section, message]);
    const existing = this.entries.get(key);
    if (existing?.element.isConnected) { existing.resume(); return; }
    if (!this.container?.isConnected) {
      this.entries.clear();
      this.container = document.createElement('section');
      this.container.className = 'admin-notifications';
      this.container.setAttribute('aria-label', 'Уведомления панели управления');
      document.body.append(this.container);
    }

    const origin = document.activeElement;
    const toast = document.createElement('div');
    toast.className = `admin-notification admin-notification--${type}`;
    toast.dataset.notificationType = type;
    const content = document.createElement('div');
    content.className = 'admin-notification__content';
    content.setAttribute('role', type === 'error' || type === 'warning' ? 'alert' : 'status');
    content.setAttribute('aria-atomic', 'true');
    const heading = document.createElement('strong');
    heading.className = 'admin-notification__title';
    heading.textContent = section ? `${section} — ${title}` : title;
    const text = document.createElement('p');
    text.className = 'admin-notification__message';
    text.textContent = message;
    content.append(heading, text);

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'admin-notification__close';
    close.setAttribute('aria-label', 'Закрыть уведомление');
    close.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>';
    toast.append(content, close);

    let timer;
    const pause = () => clearTimeout(timer);
    const dismiss = () => {
      pause();
      const wasFocused = toast.contains(document.activeElement);
      toast.remove();
      this.entries.delete(key);
      if (wasFocused) {
        const next = this.container.querySelector('button');
        if (next) next.focus({ preventScroll: true });
        else if (origin?.isConnected && !origin.disabled) origin.focus({ preventScroll: true });
      }
      if (!this.container.childElementCount) this.container.remove();
    };
    const resume = () => {
      pause();
      if (toast.isConnected && (type === 'success' || type === 'notice') && !toast.matches(':hover, :focus-within')) {
        timer = setTimeout(() => {
          if (!toast.matches(':hover, :focus-within')) dismiss();
        }, 6000);
      }
    };
    close.addEventListener('click', dismiss);
    toast.addEventListener('mouseenter', pause);
    toast.addEventListener('mouseleave', resume);
    toast.addEventListener('focusin', pause);
    toast.addEventListener('focusout', () => queueMicrotask(resume));
    this.container.prepend(toast);
    this.container.scrollTop = 0;
    this.entries.set(key, { element: toast, resume });
    resume();
  }

  static success(title, message = '') { this.show({ title, message, type: 'success' }); }
}
