import { AdminRecordList } from './AdminRecordList.js?v=20261027.10';
import { escapeHtml as esc, displayName } from '../../utils/text.js?v=20261027.10';

export function tariffRows(items, sources = {}) {
  const groups = new Map();
  for (const item of items) {
    const key = `${item.splice_type_id}:${item.splice_material_id}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }
  const rows = [];
  for (const [group, tariffs] of groups) {
    const first = tariffs[0];
    const work = displayName(sources.splice_types?.find(x => Number(x.id) === Number(first.splice_type_id))) || `Работа #${first.splice_type_id}`;
    const material = displayName(sources.splice_materials?.find(x => Number(x.id) === Number(first.splice_material_id))) || `Материал #${first.splice_material_id}`;
    for (const item of tariffs) {
      const low = item.diameter_from_mm == null ? -Infinity : Number(item.diameter_from_mm);
      const high = item.diameter_to_mm == null ? Infinity : Number(item.diameter_to_mm);
      const conflicts = item.is_active === false ? [] : tariffs.filter(other => other !== item && other.is_active !== false
        && (other.diameter_from_mm ?? -Infinity) <= high && (other.diameter_to_mm ?? Infinity) >= low).map(other => other.id);
      const range = low === -Infinity && high === Infinity ? 'Любой диаметр'
        : low === -Infinity ? `До ${high} мм включительно`
        : high === Infinity ? `От ${low} мм` : `${low}–${high} мм`;
      const price = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'EUR' }).format(Number(item.price));
      const status = item.is_active === false ? 'Отключён' : conflicts.length ? `Пересечение с ${conflicts.map(id => `#${id}`).join(', ')}` : 'Активен';
      rows.push({ id: item.id, group, work, material, low, high, range, price, priceValue: Number(item.price), conflicts,
        label: `${work} · ${material}`, detail: `${range} · ${price} · ${status}`, status });
    }
  }
  return rows.sort((a, b) => a.work.localeCompare(b.work, 'ru') || a.material.localeCompare(b.material, 'ru')
    || a.group.localeCompare(b.group) || a.low - b.low || a.high - b.high || Number(a.id) - Number(b.id));
}

// Retain the shared search, paging, selection and controller discard checks.
export class AdminTariffTable extends AdminRecordList {
  constructor(root, signal) {
    super(root, signal);
    this.priceDrafts = new Map();
    root.insertAdjacentHTML('beforeend','<div class="admin-tariffs__save" data-tariff-save-panel hidden><button type="button" class="btn btn--primary" data-tariff-save>Сохранить цены</button><button type="button" class="btn btn--ghost" data-tariff-cancel>Отменить изменения цен</button><span data-tariff-draft-count role="status"></span></div>');
    root.addEventListener('input',event=>{
      const input=event.target.closest('[data-tariff-price]');
      if(!input || !this.tariffs)return;
      const row=this.items.find(item=>item.id===input.dataset.tariffPrice);
      if(!row)return;
      const raw=input.value.trim(), parsed=Number(raw.replace(',','.'));
      if(raw && Number.isFinite(parsed) && parsed===row.priceValue) this.priceDrafts.delete(row.id);
      else this.priceDrafts.set(row.id,raw);
      input.removeAttribute('aria-invalid');
      this.updatePriceControls();
    },{signal});
    root.addEventListener('click',event=>{if(this.disabled)return;if(event.target.closest('[data-tariff-save]'))this.onSavePrices?.();if(event.target.closest('[data-tariff-cancel]')&&this.priceDrafts.size&&window.confirm('Отменить все несохранённые изменения цен?')){this.clearPriceDrafts();this.render();}},{signal});
  }
  clearPriceDrafts(){this.priceDrafts.clear();this.updatePriceControls();}
  updatePriceControls(){
    const panel=this.root.querySelector('[data-tariff-save-panel]');if(!panel)return;
    panel.hidden=!this.tariffs;
    panel.querySelector('[data-tariff-save]').disabled=this.disabled||!this.priceDrafts.size;
    panel.querySelector('[data-tariff-cancel]').disabled=this.disabled||!this.priceDrafts.size;
    panel.querySelector('[data-tariff-draft-count]').textContent=this.priceDrafts.size ? `Изменено цен: ${this.priceDrafts.size}` : 'Нет несохранённых цен';
  }
  busy(value){super.busy(value);this.updatePriceControls();}
  setTariffs(items, sources) {
    this.tariffs = true;
    this.setItems(tariffRows(items, sources));
  }
  renderCategoryCards(container) {
    if (container.tagName !== 'UL' || !container.classList.contains('admin-category-grid')) {
      container.outerHTML = '<ul class="admin-category-grid" data-record-items></ul>';
    }
    const items = this.filtered();
    this.pages = Math.max(1, Math.ceil(items.length / this.pageSize));
    this.page = Math.min(this.pages, Math.max(1, this.page));
    const start = (this.page - 1) * this.pageSize;
    const activeId = this.root.ownerDocument.activeElement?.dataset?.recordId;
    const grid = this.root.querySelector('[data-record-items]');
    grid.innerHTML = items.slice(start, start + this.pageSize).map(item => `<li>
      <button type="button" class="admin-category-card" data-record-id="${esc(item.id)}" aria-pressed="${item.id === this.selected}">
        <span class="admin-category-card__media"><span class="admin-category-card__placeholder" aria-hidden="true">Нет изображения</span>${item.image ? `<img src="${esc(item.image)}" alt="" loading="lazy">` : ''}</span>
        <span class="admin-category-card__info"><span class="admin-category-card__name">${esc(item.label)}</span>${item.detail ? `<span class="admin-category-card__status">${esc(item.detail)}</span>` : ''}</span>
      </button></li>`).join('') || `<li class="admin-record-list__empty">${this.query.trim() ? 'Ничего не найдено. Измените поисковый запрос.' : 'Разделов пока нет. Нажмите «Добавить», чтобы создать первый.'}</li>`;
    grid.querySelectorAll('img').forEach(img => img.addEventListener('error', () => img.hidden = true, {once:true}));
    this.root.querySelector('[data-record-count]').textContent = items.length ? `Показаны ${start + 1}–${Math.min(start + this.pageSize, items.length)} из ${items.length}${this.query.trim() ? ` (всего ${this.items.length})` : ''}` : 'Найдено: 0';
    this.root.querySelector('[data-record-page]').textContent = `Страница ${this.page} из ${this.pages}`;
    this.updateControls();
    if (activeId) [...grid.querySelectorAll('[data-record-id]')].find(row => row.dataset.recordId === activeId)?.focus({preventScroll:true});
  }
  render() {
    const container = this.root.querySelector('[data-record-items]');
    this.updatePriceControls();
    if (this.categoryCards) {
      this.renderCategoryCards(container);
      return;
    }
    if (!this.tariffs) {
      if (container.tagName !== 'UL') container.outerHTML = '<ul class="admin-record-list__items" data-record-items></ul>';
      super.render();
      return;
    }
    if (container.tagName !== 'DIV') container.outerHTML = '<div class="admin-tariffs" data-record-items></div>';
    const items = this.filtered();
    this.pages = Math.max(1, Math.ceil(items.length / this.pageSize));
    this.page = Math.min(this.pages, Math.max(1, this.page));
    const start = (this.page - 1) * this.pageSize;
    const groups = new Map();
    for (const row of items.slice(start, start + this.pageSize)) {
      if (!groups.has(row.group)) groups.set(row.group, []);
      groups.get(row.group).push(row);
    }
    const activeId = this.root.ownerDocument.activeElement?.dataset?.recordId;
    this.root.querySelector('[data-record-items]').innerHTML = [...groups.values()].map(rows => `<table class="admin-tariffs__table">
      <caption>${esc(rows[0].work)} <span>· ${esc(rows[0].material)}</span></caption>
      <thead><tr><th scope="col">Диаметр</th><th scope="col">Цена, €</th><th scope="col">Состояние</th><th scope="col">Запись</th></tr></thead>
      <tbody>${rows.map(row => `<tr class="${row.conflicts.length ? 'admin-tariffs__conflict' : ''}" data-selected="${row.id === this.selected}">
        <td data-label="Диаметр">${esc(row.range)}</td><td data-label="Цена, €"><input class="field__input admin-tariffs__price" type="text" inputmode="decimal" autocomplete="off" data-tariff-price="${esc(row.id)}" aria-label="Цена EUR: ${esc(row.work)}, ${esc(row.material)}, ${esc(row.range)}" value="${esc(this.priceDrafts.get(row.id) ?? row.priceValue)}"></td><td data-label="Состояние">${esc(row.status)}</td>
        <td><button type="button" class="btn btn--ghost" data-record-id="${esc(row.id)}" aria-pressed="${row.id === this.selected}" aria-label="Изменить тариф #${esc(row.id)}">Изменить #${esc(row.id)}</button></td></tr>`).join('')}</tbody></table>`).join('') || '<p>Тарифы не найдены.</p>';
    const conflicts = this.items.filter(row => row.conflicts.length).length;
    this.root.querySelector('[data-record-count]').textContent = `Найдено тарифов: ${items.length} из ${this.items.length}. Всего с пересечениями: ${conflicts}. Границы диапазонов включены.`;
    this.root.querySelector('[data-record-page]').textContent = `Страница ${this.page} из ${this.pages}`;
    this.updateControls();
    this.updatePriceControls();
    if (activeId) [...this.root.querySelectorAll('[data-record-id]')].find(row => row.dataset.recordId === activeId)?.focus({ preventScroll: true });
  }
}
