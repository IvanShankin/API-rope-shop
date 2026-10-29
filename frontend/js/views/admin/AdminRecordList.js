import { escapeHtml as esc } from '../../utils/text.js?v=20261027.10';

// Shared record picker. Editing and unsaved-change checks stay in the controllers.
export class AdminRecordList {
  constructor(root, signal) {
    this.root = root;
    this.items = [];
    this.page = 1;
    this.pageSize = 20;
    this.selected = '';
    this.query = '';
    this.disabled = false;
    root.classList.add('admin-record-list');
    root.innerHTML = `<label class="field">Поиск записей<input class="field__input" type="search" placeholder="Название, текст или номер…" data-record-search></label>
      <p data-record-count role="status"></p><ul class="admin-record-list__items" data-record-items></ul>
      <nav class="admin-record-list__pages" aria-label="Страницы списка"><button class="btn btn--ghost" type="button" data-record-prev>Назад</button><span data-record-page></span><button class="btn btn--ghost" type="button" data-record-next>Далее</button></nav>`;
    root.querySelector('[data-record-search]').addEventListener('input', e => {
      this.query = e.target.value;
      this.page = 1;
      this.render();
      this.root.querySelector('[data-record-items]').scrollTop = 0;
    }, { signal });
    root.addEventListener('click', e => {
      if (this.disabled) return;
      const row = e.target.closest('[data-record-id]');
      if (row) {
        this.select(row.dataset.recordId, false);
        this.onSelect?.(row.dataset.recordId);
      } else if (e.target.closest('[data-record-prev]')) {
        this.page = Math.max(1, this.page - 1); this.render();
        this.root.querySelector('[data-record-items]').scrollTop = 0;
      } else if (e.target.closest('[data-record-next]')) {
        this.page++; this.render();
        this.root.querySelector('[data-record-items]').scrollTop = 0;
      }
    }, { signal });
    this.render();
  }
  filtered() {
    const query = this.query.trim().toLocaleLowerCase('ru');
    return this.items.filter(item => `${item.id} ${item.label} ${item.detail || ''} ${item.search || ''}`.toLocaleLowerCase('ru').includes(query));
  }
  setItems(items) {
    this.items = items.map(item => ({ ...item, id: String(item.id) }));
    if (!this.items.some(item => item.id === this.selected)) this.selected = '';
    this.render();
  }
  reset() {
    this.query = ''; this.page = 1; this.selected = '';
    this.root.querySelector('[data-record-search]').value = '';
    this.render();
  }
  select(id, reveal = true) {
    this.selected = id == null ? '' : String(id);
    if (reveal && this.selected) {
      if (!this.filtered().some(item => item.id === this.selected)) {
        this.query = ''; this.root.querySelector('[data-record-search]').value = '';
      }
      const index = this.filtered().findIndex(item => item.id === this.selected);
      if (index >= 0) this.page = Math.floor(index / this.pageSize) + 1;
    }
    this.render();
  }
  busy(value) { this.disabled = value; this.updateControls(); }
  updateControls() {
    this.root.querySelectorAll('input,button').forEach(el => { el.disabled = this.disabled; });
    this.root.querySelector('[data-record-prev]').disabled = this.disabled || this.page <= 1;
    this.root.querySelector('[data-record-next]').disabled = this.disabled || this.page >= this.pages;
    this.root.setAttribute('aria-busy', String(this.disabled));
  }
  render() {
    const items = this.filtered();
    this.pages = Math.max(1, Math.ceil(items.length / this.pageSize));
    this.page = Math.min(this.pages, Math.max(1, this.page));
    const start = (this.page - 1) * this.pageSize;
    const activeId = this.root.ownerDocument.activeElement?.dataset?.recordId;
    this.root.querySelector('[data-record-items]').innerHTML = items.slice(start, start + this.pageSize).map(item =>
      `<li><button type="button" class="admin-record-list__row" data-record-id="${esc(item.id)}" aria-pressed="${item.id === this.selected}"><span class="admin-record-list__name">${esc(item.label)}</span><span class="admin-record-list__detail">#${esc(item.id)}${item.detail ? ` · ${esc(item.detail)}` : ''}</span></button></li>`
    ).join('') || `<li class="admin-record-list__empty">${this.query.trim() ? 'Ничего не найдено. Измените поисковый запрос.' : 'Записей пока нет.'}</li>`;
    this.root.querySelector('[data-record-count]').textContent = items.length ? `Показаны ${start + 1}–${Math.min(start + this.pageSize, items.length)} из ${items.length}${this.query.trim() ? ` (всего ${this.items.length})` : ''}` : 'Найдено: 0';
    this.root.querySelector('[data-record-page]').textContent = `Страница ${this.page} из ${this.pages}`;
    this.updateControls();
    if (activeId) [...this.root.querySelectorAll('[data-record-id]')].find(row => row.dataset.recordId === activeId)?.focus({ preventScroll: true });
  }
}
