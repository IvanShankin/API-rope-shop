import { escapeHtml as esc } from '../../utils/text.js?v=20261106.1';

// Единые языковые вкладки админки: канаты, цвета, тексты, галереи, отзывы, справочники.
// Разметка и классы — как в карточке каната (стили в css/admin/02-components, 11-product-editor).
export const LOCALES = [['rus', 'Русский'], ['eng', 'Английский'], ['ger', 'Немецкий']];
let lastLocale = 'rus';
let counter = 0;

/**
 * panels — { rus: html, eng: html, ger: html } с полями каждого языка.
 * filled — { rus: true, ... } для зелёной точки «заполнено». extra — кнопки справа от вкладок.
 */
export function langTabsMarkup({ label = 'Язык текста', panels, filled = {}, extra = '' }) {
  const id = `admin-lang-${++counter}`;
  const active = LOCALES.some(([locale]) => locale === lastLocale) ? lastLocale : 'rus';
  const tabs = LOCALES.map(([locale, title]) => `<button class="lang-switch__button${locale === active ? ' lang-switch__button--active' : ''}" type="button" role="tab"
      id="${id}-${locale}-tab" aria-controls="${id}-${locale}" aria-selected="${locale === active}" tabindex="${locale === active ? 0 : -1}" data-lang-tab="${locale}">
      <span class="lang-tab__indicator${filled[locale] ? ' lang-tab__indicator--filled' : ''}" data-lang-indicator="${locale}" aria-hidden="true"></span> ${title}</button>`).join('');
  const body = LOCALES.map(([locale]) => `<div class="lang-tab-panel" role="tabpanel" id="${id}-${locale}" aria-labelledby="${id}-${locale}-tab"
      data-lang-panel="${locale}"${locale === active ? '' : ' hidden'}>${panels[locale] || ''}</div>`).join('');
  return `<div class="lang-tabs" data-lang-tabs>
    <div class="product-lang-bar"><div class="lang-switch" role="tablist" aria-label="${esc(label)}">${tabs}</div>${extra}</div>
    ${body}
  </div>`;
}

function selectTab(tab, focus = false) {
  const group = tab.closest('[data-lang-tabs]');
  if (!group) return;
  const locale = tab.dataset.langTab;
  lastLocale = locale;
  group.querySelectorAll('[data-lang-tab]').forEach(button => {
    const active = button === tab;
    button.classList.toggle('lang-switch__button--active', active);
    button.setAttribute('aria-selected', String(active));
    button.tabIndex = active ? 0 : -1;
  });
  group.querySelectorAll('[data-lang-panel]').forEach(panel => { panel.hidden = panel.dataset.langPanel !== locale; });
  if (focus) tab.focus();
}

function updateIndicator(panel) {
  const group = panel.closest('[data-lang-tabs]');
  const filled = [...panel.querySelectorAll('input:not([type=checkbox]):not([type=file]), textarea')].some(field => field.value.trim());
  group?.querySelector(`[data-lang-indicator="${panel.dataset.langPanel}"]`)?.classList.toggle('lang-tab__indicator--filled', filled);
}

export function refreshLangIndicators(root) {
  root?.querySelectorAll('[data-lang-panel]').forEach(updateIndicator);
}

/** Один раз на корень раздела: клики, стрелки, точки «заполнено», показ вкладки с ошибкой. */
export function bindLangTabs(root, signal) {
  const options = { signal };
  root.addEventListener('click', event => {
    const tab = event.target.closest('[data-lang-tab]');
    if (tab && root.contains(tab)) selectTab(tab);
  }, options);
  root.addEventListener('keydown', event => {
    const tab = event.target.closest('[data-lang-tab]');
    if (!tab || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    const tabs = [...tab.closest('[role=tablist]').querySelectorAll('[data-lang-tab]')];
    const index = tabs.indexOf(tab);
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1
      : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    event.preventDefault();
    selectTab(tabs[next], true);
  }, options);
  root.addEventListener('input', event => {
    const panel = event.target.closest('[data-lang-panel]');
    if (panel) updateIndicator(panel);
  }, options);
  // Поле с ошибкой на скрытой вкладке: сначала показать вкладку, иначе браузер не сможет на него перейти.
  root.addEventListener('invalid', event => {
    const panel = event.target.closest('[data-lang-panel]');
    if (!panel?.hidden) return;
    const tab = panel.closest('[data-lang-tabs]')?.querySelector(`[data-lang-tab="${panel.dataset.langPanel}"]`);
    if (tab) selectTab(tab);
  }, { ...options, capture: true });
}
