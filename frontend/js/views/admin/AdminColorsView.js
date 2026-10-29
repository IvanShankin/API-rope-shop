import { captureDisclosures, restoreDisclosures } from './disclosureState.js?v=20261027.10';
import { AdminNotificationView } from './AdminNotificationView.js?v=20261027.10';
import { AdminRecordList } from './AdminRecordList.js?v=20261027.10';
import { escapeHtml as esc, displayName } from '../../utils/text.js?v=20261027.10';
export class AdminColorsView {
  constructor(root) { this.root = root; this.events = new AbortController(); this.baseline = ''; this.recordList = new AdminRecordList(root.querySelector("[data-color-select]"), this.events.signal); }
  bind(actions) {
    const options = { signal: this.events.signal };
    this.recordList.onSelect = actions.select;
    this.root.querySelector('[data-color-new]').addEventListener('click', actions.create, options);
    this.root.querySelector('[data-colors-refresh]').addEventListener('click', actions.refresh, options);
    this.root.addEventListener('click',e=>{if(e.target.matches('[data-color-remove]'))actions.remove();},options);
    this.root.addEventListener('click',e=>{if(e.target.matches('[data-color-translation-remove]'))actions.removeTranslation(Number(e.target.dataset.colorTranslationRemove));},options);
    this.root.addEventListener('submit', e => { if (!e.target.matches('[data-color-form]')) return; e.preventDefault(); if (e.target.reportValidity()) actions.save(); }, options);
    const syncColor = e => {
      const form = e.target.closest('[data-color-form]');
      if (!form) return;
      if (e.target.matches('[data-color-picker]')) {
        form.elements.namedItem('hex').value = e.target.value.toUpperCase();
      } else if (e.target.matches('[name="hex"]') && /^#[0-9a-f]{6}$/i.test(e.target.value)) {
        form.querySelector('[data-color-picker]').value = e.target.value;
      }
    };
    this.root.addEventListener('input', syncColor, options);
    this.root.addEventListener('change', syncColor, options);
    window.addEventListener('beforeunload', e => { if (this.dirty()) { e.preventDefault(); e.returnValue = ''; } }, options);
  }
  destroy() { this.events.abort(); }
  values() { const form = this.root.querySelector('form'); return form ? Object.fromEntries([...form.elements].filter(e => e.name).map(e => [e.name, e.type === 'checkbox' ? e.checked : e.value])) : {}; }
  dirty() { return Boolean(this.baseline && this.baseline !== JSON.stringify(this.values())); }
  allowDiscard() { return !this.dirty() || window.confirm('Отбросить несохранённые изменения цвета?'); }
  busy(value) { this.root.querySelectorAll('input,select,button').forEach(e => { e.disabled = value; }); this.recordList.busy(value); }
  message(text, type = 'info') { AdminNotificationView.message(this.root.querySelector('[data-color-status]'), text, type); }
  selection(id) { this.recordList.select(id); }
  list(colors) { this.recordList.setItems(colors.map(c=>({id:c.id,label:displayName(c)||c.code,detail:c.is_active===false?'Неактивен':'',search:[c.code,c.hex,...(c.translations||[]).map(t=>t.name)].join(' ')}))); }
  clear() { this.root.querySelector('[data-color-editor]').replaceChildren(); this.baseline = ''; this.recordList.select(null); }
  render(color = {}, {preserveDisclosures=false}={}) {
    const disclosureState = captureDisclosures(this.root, preserveDisclosures);
    this.recordList.select(color.id);
    const name = locale => color.translations?.find(t => t.locale === locale)?.name || '';
    this.root.querySelector('[data-color-editor]').innerHTML = `<h2>${color.id ? 'Редактирование цвета' : 'Новый цвет'}</h2>
      <form data-color-form class="product-editor admin-card">
        <div class="admin-disclosures-group">
          <details class="admin-disclosure" data-editor-disclosure="parameters" open><summary>Параметры цвета</summary><div class="admin-fields">
            <div class="field"><label for="admin-color-hex">HEX (например #FF0000)</label><div class="admin-color-control"><input class="admin-color-picker" type="color" data-color-picker aria-label="Выбрать цвет в палитре" title="Выбрать цвет в палитре" value="${/^#[0-9a-f]{6}$/i.test(color.hex || '') ? esc(color.hex) : '#000000'}"><input class="field__input" id="admin-color-hex" name="hex" pattern="#[0-9a-fA-F]{6}" placeholder="#FF0000" value="${esc(color.hex || '')}" aria-describedby="admin-color-hint"></div><small class="field__hint" id="admin-color-hint">Нажмите на квадрат для выбора цвета или введите HEX вручную.</small></div>
            <label class="field">Порядок в общем списке<input class="field__input" name="index" type="number" min="0" step="1" required value="${Number(color.index??0)}"><small class="field__hint">Чем меньше число, тем выше цвет в списке.</small></label>
          </div></details>
          <details class="admin-disclosure" data-editor-disclosure="translations" open><summary>Названия на разных языках</summary><p class="admin-editor-hint">Заполните название хотя бы на одном языке.</p><div class="admin-fields">
            <label class="field">Название EN<input class="field__input" name="eng" maxlength="255" value="${esc(name('eng'))}"></label>
            <label class="field">Название RU<input class="field__input" name="rus" maxlength="255" value="${esc(name('rus'))}"></label>
            <label class="field">Название DE<input class="field__input" name="ger" maxlength="255" value="${esc(name('ger'))}"></label>
          </div></details>
        </div>
        <label class="admin-toggle"><input type="checkbox" name="is_active" ${color.is_active !== false ? 'checked' : ''}> <span>Активен</span></label>
        <div class="admin-form-actions">
          <button type="submit" class="btn btn--primary">Сохранить цвет</button>
          ${color.id?'<button class="btn btn--danger" type="button" data-color-remove>Удалить цвет</button>':''}
        </div>
      </form>`;
    restoreDisclosures(this.root, disclosureState);
    this.baseline = JSON.stringify(this.values());
    if(color.translations?.length>1)this.root.querySelector('[data-color-editor]').insertAdjacentHTML('beforeend',`<h3>Удалить отдельный перевод</h3><p>Последний перевод удалить нельзя. После удаления сервер может показывать название на другом языке.</p><div class="config-admin-toolbar">${color.translations.map(t=>`<button class="btn btn--danger" type="button" data-color-translation-remove="${Number(t.id)}">Удалить ${esc(t.locale.toUpperCase())}</button>`).join('')}</div>`);
  }
}
