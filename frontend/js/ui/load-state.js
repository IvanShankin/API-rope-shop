import { getLanguage } from '../i18n/locale.js?v=20261027.10';

// GET failures are recoverable; never use this helper to retry a submitted order.
export function loadErrorMessage(error) {
  if (globalThis.navigator?.onLine === false) return 'Нет подключения к интернету. Проверьте соединение и повторите загрузку.';
  return 'Не удалось получить данные. Попробуйте загрузить ещё раз через несколько секунд.';
}

export function catalogLink() {
  const link = document.createElement('a');
  link.href = `/catalog/?lang=${getLanguage()}`;
  link.className = 'button button--ghost button--small';
  link.textContent = 'Перейти в каталог';
  link.hidden = true;
  return link;
}

export function updateLoadState(root, message, state) {
  root.dataset.loadState = state;
  root.setAttribute('aria-busy', String(state === 'loading'));
  message.classList.add('load-state');
  message.dataset.state = state;
  message.setAttribute('role', 'status');
  message.setAttribute('aria-atomic', 'true');
  message.hidden = !message.textContent;
}
