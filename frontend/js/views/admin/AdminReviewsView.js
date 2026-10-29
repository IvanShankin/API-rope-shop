import { captureDisclosures, restoreDisclosures } from './disclosureState.js?v=20261027.10';
import {AdminContentView} from './AdminContentView.js?v=20261028.16';
import {escapeHtml as esc} from '../../utils/text.js?v=20261027.10';
import {reviewFilters, reviewCounts, reviewRecords, reviewPublication} from '../../models/AdminReviewModel.js?v=20261027.10';
export class AdminReviewsView extends AdminContentView {
  constructor(root){
    super(root,{all:'Все отзывы'},true);
    root.querySelector('h1').textContent='Отзывы';
    root.querySelector('header + p').textContent='Новые отзывы проходят модерацию. На главной видны только одобренные отзывы с включённой публикацией. Пустое поле перевода удаляет этот перевод; хотя бы один текст обязателен.';
    root.querySelector('[data-config-section]').closest('label').hidden=true;
    root.querySelector('[data-config-new]').textContent='Добавить отзыв';
    this.items=[];this.filter='all';
    root.querySelector('[data-config-record]').insertAdjacentHTML('beforebegin',`<div class="admin-review-filters" role="group" aria-label="Фильтр модерации">${Object.entries(reviewFilters).map(([key,label])=>`<button type="button" class="btn btn--ghost" data-review-filter="${key}" aria-pressed="${key==='all'}">${label} <span data-review-count="${key}">0</span></button>`).join('')}</div><p role="status" data-review-summary>Отзывы ещё не загружены.</p><p data-review-selection hidden>Открытый отзыв не входит в выбранный фильтр. Его форма и несохранённые изменения остаются ниже.</p>`);
    root.addEventListener('click',event=>{
      const button=event.target.closest('[data-review-filter]');
      if(!button||button.disabled)return;
      this.filter=button.dataset.reviewFilter;this.recordList.page=1;this.list(this.items);
    },{signal:this.events.signal});
    root.addEventListener('change',event=>{
      if(event.target.matches('[name=status], [name=is_published]'))this.publicationHint();
    },{signal:this.events.signal});
  }
  list(items){
    this.items=items;
    const counts=reviewCounts(items);
    this.root.querySelector('[data-review-summary]').textContent=`Ожидают проверки: ${counts.new}. Всего отзывов: ${counts.all}.`;
    this.root.querySelectorAll('[data-review-filter]').forEach(button=>{
      button.setAttribute('aria-pressed',String(button.dataset.reviewFilter===this.filter));
      button.querySelector('[data-review-count]').textContent=counts[button.dataset.reviewFilter];
    });
    const selected=this.recordList.selected;
    this.recordList.setItems(reviewRecords(items,this.filter));
    // Filtering the list must never discard the open editor or its draft.
    this.recordList.selected=selected;this.recordList.render();
    this.selectionHint();
  }
  selectionHint(){this.root.querySelector('[data-review-selection]').hidden=!this.recordList.selected||this.recordList.items.some(item=>item.id===this.recordList.selected);}
  select(id){
    const item=this.items.find(item=>String(item.id)===String(id));
    if(item&&this.filter!=='all'&&item.status!==this.filter){this.filter='all';this.list(this.items);}
    super.select(id);this.selectionHint();
  }
  clear(){super.clear();this.selectionHint();}
  publicationHint(){
    const values=this.values();
    this.root.querySelector('[data-review-publication]').textContent=`После сохранения: ${reviewPublication(values)}.`;
  }
  render(item={}, {preserveDisclosures=false}={}) {
    const disclosureState = captureDisclosures(this.root, preserveDisclosures);
    this.select(item.id);
    this.root.querySelector('[data-content-editor]').innerHTML=`<h2>${item.id?`Отзыв #${Number(item.id)}`:'Новый отзыв'}</h2><form class="product-editor admin-card">
      <div class="admin-fields" style="padding: 0;">
        <label class="field">Автор<input class="field__input" name="author_name" maxlength="255" required value="${esc(item.author_name||'')}"></label>
        <label class="field">Оценка<select class="field__input" name="rating"><option value="">Без оценки</option>${[1,2,3,4,5].map(n=>`<option value="${n}" ${item.rating===n?'selected':''}>${n} / 5</option>`).join('')}</select></label>
        <label class="field">Модерация<select class="field__input" name="status">${Object.entries({new:'На проверке',confirmed:'Одобрен',rejected:'Отклонён'}).map(([value,label])=>`<option value="${value}" ${(item.status||'new')===value?'selected':''}>${label}</option>`).join('')}</select></label>
        <label class="field">Порядок (меньше — выше)<input class="field__input" type="number" name="index" min="0" step="1" required value="${Number(item.index||0)}"></label>
      </div>
      <label class="admin-toggle"><input type="checkbox" name="is_published" ${item.is_published?'checked':''}> <span>Опубликовать после одобрения</span></label>
      <p class="admin-review-publication" role="status" data-review-publication></p>
      <div class="admin-disclosures-group">
        ${['rus','eng','ger'].map(locale=>`<details class="admin-disclosure" data-editor-disclosure="${locale}" open><summary>${{rus:'Русский',eng:'English',ger:'Deutsch'}[locale]}</summary><div class="admin-fields"><label class="field" style="grid-column: 1 / -1;">Текст ${locale.toUpperCase()}<textarea class="field__input" name="text_${locale}" rows="5">${esc(item.translations?.find(t=>t.locale===locale)?.text||'')}</textarea></label></div></details>`).join('')}
      </div>
      <div class="admin-form-actions">
        <button class="btn btn--primary" type="submit">Сохранить</button>
        ${item.id?'<button class="btn btn--danger" type="button" data-content-remove>Удалить отзыв</button>':''}
      </div></form>`;
    restoreDisclosures(this.root, disclosureState);
    this.publicationHint();this.remember();
  }
}
