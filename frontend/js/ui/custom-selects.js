import SlimSelect from '../vendor/slim-select/slimselect.es.js?v=20261106.1';
import { getLanguage } from '../i18n/locale.js?v=20261106.1';

const instances = new Map();
const valueProperty = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value');
let queued = false;
// Тексты выпадающих списков: на публичных страницах (html.page) — язык сайта, в админке и входе — русский.
const UI_TEXT = {
  ru: { search: 'Найти…', empty: 'Ничего не найдено', searching: 'Поиск…', placeholder: 'Выберите вариант', results: 'Найдено вариантов: {count}' },
  en: { search: 'Search…', empty: 'Nothing found', searching: 'Searching…', placeholder: 'Choose an option', results: 'Options found: {count}' },
  de: { search: 'Suchen…', empty: 'Nichts gefunden', searching: 'Suche…', placeholder: 'Option wählen', results: 'Gefundene Optionen: {count}' },
};
const schedule = () => {
  if (queued) return;
  queued = true;
  queueMicrotask(() => { queued = false; refresh(); });
};

function refresh() {
  for (const [select, entry] of instances) {
    if (!select.isConnected) {
      entry.instance.destroy();
      delete select.value;
      instances.delete(select);
      continue;
    }
    const selected = [...select.selectedOptions].map(option => option.value);
    if (JSON.stringify(selected) !== JSON.stringify(entry.instance.getSelected())) entry.instance.setSelected(selected, false);
    entry.instance.settings.showSearch = select.options.length > 8;
  }
  for (const select of document.querySelectorAll('select:not([data-native-select])')) {
    if (instances.has(select) || !select.getClientRects().length) continue;
    const text = (document.documentElement.classList.contains('page') && UI_TEXT[getLanguage()]) || UI_TEXT.ru;
    const label = select.getAttribute('aria-label') || [...(select.labels || [])].map(el => { const copy = el.cloneNode(true); copy.querySelectorAll('select, .ss-main').forEach(node => node.remove()); return copy.textContent.trim(); }).join(' ') || text.placeholder;
    const instance = new SlimSelect({ select, settings: {
      showSearch: select.options.length > 8,
      ariaLabel: label,
      searchPlaceholder: text.search, searchText: text.empty,
      searchingText: text.searching, placeholderText: text.placeholder,
      resultsText: text.results,
      contentLocation: document.body, modal: 'off',
    }});
    instances.set(select, { instance });
    // Existing controllers assign select.value without emitting change.
    // Mirror that assignment without triggering saves or recalculations twice.
    Object.defineProperty(select, 'value', {
      configurable: true,
      get() { return valueProperty.get.call(this); },
      set(value) { valueProperty.set.call(this, value); schedule(); },
    });
  }
}

const observer = new MutationObserver(records => {
  if (records.some(record => record.type === 'attributes' ||
    [...record.addedNodes, ...record.removedNodes].some(node => node.nodeType === 1 &&
      (node.matches('select, option, optgroup') || node.querySelector('select'))))) schedule();
});
// Slim Select emits change; native selects also emit input, used by the service calculators.
document.addEventListener('change', event => {
  if (instances.has(event.target)) event.target.dispatchEvent(new Event('input', { bubbles: true }));
});
observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['hidden'] });
document.addEventListener('toggle', schedule, true);
document.addEventListener('reset', () => setTimeout(schedule, 0), true);
refresh();
