import { captureDisclosures, restoreDisclosures } from './disclosureState.js?v=20261027.10';
import { AdminNotificationView } from './AdminNotificationView.js?v=20261027.10';
import { AdminRecordList } from './AdminRecordList.js?v=20261027.10';
import {escapeHtml as esc} from '../../utils/text.js?v=20261027.10';
import {mediaUrl} from '../../utils/media.js?v=20261027.10';
export class AdminContentView {
  constructor(root,sections,gallery) {
    this.root=root;this.gallery=gallery;this.events=new AbortController();this.baseline='';
    this.sectionCards = root.id === 'panel-content' || root.id === 'panel-gallery';
    root.innerHTML=`<header class="panel__head"><h1>${gallery?'Галереи':'Тексты страниц'}</h1></header>
      <p>${gallery?'Фотографии работ показываются в каталоге, фотографии благотворительности — на главной.':'Выберите страницу и блок существующего макета. Сохраняются обычный текст и переносы строк; HTML-код показывается как текст.'}</p>
      ${this.sectionCards?`<nav class="config-section-menu" aria-label="${gallery?'Выбор галереи':'Выбор страницы'}">${Object.entries(sections).map(([code,title],index)=>`<button type="button" class="config-section-card" data-content-section-choice="${esc(code)}" aria-pressed="${index===0}"><span class="config-section-card__name">${esc(title)}</span></button>`).join('')}</nav>`:''}
      <div class="config-admin-toolbar"><label class="field" ${this.sectionCards?'hidden':''}>${gallery?'Галерея':'Страница'}<select class="field__input" data-config-section ${this.sectionCards?'data-native-select':''}>${Object.entries(sections).map(([code,title])=>`<option value="${code}">${esc(title)}</option>`).join('')}</select></label>
      ${gallery?'<button class="btn" type="button" data-config-new>Добавить фотографию</button>':''}<button class="btn" type="button" data-content-refresh>Обновить</button></div>
      <div data-config-record></div><p role="status" data-content-status></p><div data-content-editor></div>`;
    this.recordList = new AdminRecordList(root.querySelector("[data-config-record]"), this.events.signal);
  }
  bind(actions) {
    const opts={signal:this.events.signal};
    this.root.querySelector('[data-config-section]').addEventListener('change',e=>actions.load(e.target.value),opts);
    this.recordList.onSelect = actions.select;
    this.root.querySelector('[data-content-refresh]').addEventListener('click',()=>actions.load(),opts);
    this.root.querySelector('[data-config-new]')?.addEventListener('click',actions.create,opts);
    this.root.addEventListener('submit',e=>{e.preventDefault();if(e.target.reportValidity())actions.save();},opts);
    this.root.addEventListener('click',e=>{const card=e.target.closest('[data-content-section-choice]');if(card&&!card.disabled){actions.load(card.dataset.contentSectionChoice);return;}if(e.target.closest('[data-content-remove]'))actions.remove();},opts);
    window.addEventListener('beforeunload',e=>{if(this.dirty()){e.preventDefault();e.returnValue='';}},opts);
  }
  setSection(section){this.root.querySelector('[data-config-section]').value=section;this.root.querySelectorAll('[data-content-section-choice]').forEach(card=>card.setAttribute('aria-pressed',String(card.dataset.contentSectionChoice===section)));}
  message(text, type = 'info') { AdminNotificationView.message(this.root.querySelector('[data-content-status]'), text, type); }
  busy(value){this.root.querySelectorAll('input,textarea,select,button').forEach(el=>el.disabled=value);this.recordList.busy(value);}
  select(id){this.recordList.select(id);}
  list(items){
    const section=this.root.querySelector('[data-config-section]').value;
    if(this.listSection!==section){this.recordList.reset();this.listSection=section;}
    this.recordList.setItems(items.map(item=>({id:item.id,label:item.label||item.title||('Фото #'+item.id),detail:[item.is_active===false?'Отключено':'',item.text||item.description||''].filter(Boolean).join(' · '),search:(item.translations||[]).map(t=>[t.title,t.text,t.description].join(' ')).join(' ')})));
  }
  values(){return Object.fromEntries([...this.root.querySelector('form')?.elements||[]].filter(e=>e.name).map(e=>[e.name,e.type==='checkbox'?e.checked:e.value]));}
  file(){return this.root.querySelector('[type=file]')?.files[0];}
  resetFile(){const input=this.root.querySelector('[type=file]');if(input){input.value='';input.required=false;}}
  remember(){this.baseline=JSON.stringify(this.values());}
  dirty(){return this.baseline!==''&&this.baseline!==JSON.stringify(this.values());}
  allowDiscard(){return !this.dirty()||window.confirm('Отбросить несохранённые изменения контента?');}
  clear(){this.root.querySelector('[data-content-editor]').replaceChildren();this.baseline='';this.recordList.select(null);}
  render(item={}, {preserveDisclosures=false}={}) {
    const disclosureState = captureDisclosures(this.root, preserveDisclosures);
    this.recordList.select(item.id);
    const slot=item.slot;const titleEnabled=this.gallery||slot?.title;const textEnabled=this.gallery||slot?.content;
    const translationFields=['rus','eng','ger'].map(locale=>{
      const t=item.translations?.find(t=>t.locale===locale)||{};
      return `<details class="admin-disclosure" data-editor-disclosure="${locale}" open><summary>${({rus:'Русский',eng:'English',ger:'Deutsch'})[locale]}</summary><div class="admin-fields">
        ${titleEnabled?`<label class="field">${this.gallery?'Подпись':'Заголовок'} ${locale.toUpperCase()}<textarea class="field__input" name="title_${locale}" maxlength="${this.gallery?255:500}">${esc(t.title||'')}</textarea></label>`:''}
        ${textEnabled?`<label class="field">Текст ${locale.toUpperCase()}<textarea class="field__input" name="content_${locale}" rows="5">${esc(t.content??t.description??'')}</textarea></label>`:''}</div></details>`;
    }).join('');
    this.root.querySelector('[data-content-editor]').innerHTML=`<h2>${esc(item.label||(item.id?`Фотография #${item.id}`:'Новая фотография'))}</h2>
      ${this.gallery&&item.image_url?`<img class="admin-image-preview" src="${esc(mediaUrl(item.image_url))}" alt="Фото галереи">`:''}
      <form class="product-editor admin-card">
      <div class="admin-form-row">
        <label class="admin-toggle"><input type="checkbox" name="is_active" ${item.is_active!==false?'checked':''}> <span>${this.gallery?'Показывать в галерее':'Использовать тексты из API'}</span></label>
        ${this.gallery?`<label class="field">Порядок фотографии<input class="field__input" name="index" type="number" min="0" step="1" value="${Number(item.index||0)}" required><small class="field__hint">Чем меньше число, тем раньше фотография в галерее.</small></label>`:''}
      </div>
      ${this.gallery?`<label class="field admin-file-upload"><span class="field__label">${item.id?'Заменить фотографию (необязательно)':'Фотография'}</span><input type="file" name="photo_file" accept="image/jpeg,image/png,image/webp" ${item.id?'':'required'}><span class="field__hint">До 10 МБ.</span></label>`:'<p class="admin-form-hint">При отключении блока сайт показывает исходный текст макета. Пустые поля активного блока очищают соответствующий текст на сайте.</p>'}
      <div class="admin-disclosures-group">${translationFields}</div>
      <div class="admin-form-actions">
        <button class="btn btn--primary" type="submit">Сохранить</button>
        ${this.gallery&&item.id?'<button type="button" class="btn btn--danger" data-content-remove>Удалить фотографию</button>':''}
      </div></form>`;
    restoreDisclosures(this.root, disclosureState);
    this.remember();
  }
  destroy(){this.events.abort();}
}
