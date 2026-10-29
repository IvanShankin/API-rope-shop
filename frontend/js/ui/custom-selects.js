import SlimSelect from '../vendor/slim-select/slimselect.es.js?v=20261027.10';

const instances = new Map();
const valueProperty = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value');
let queued = false;
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
    const label = select.getAttribute('aria-label') || [...(select.labels || [])].map(el => { const copy = el.cloneNode(true); copy.querySelectorAll('select, .ss-main').forEach(node => node.remove()); return copy.textContent.trim(); }).join(' ') || 'Выберите вариант';
    const instance = new SlimSelect({ select, settings: {
      showSearch: select.options.length > 8,
      ariaLabel: label,
      searchPlaceholder: 'Найти…', searchText: 'Ничего не найдено',
      searchingText: 'Поиск…', placeholderText: 'Выберите вариант',
      resultsText: 'Найдено вариантов: {count}',
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
