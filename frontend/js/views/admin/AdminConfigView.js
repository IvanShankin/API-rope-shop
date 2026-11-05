import { captureDisclosures, restoreDisclosures } from './disclosureState.js?v=20261027.10';
import { AdminNotificationView } from './AdminNotificationView.js?v=20261027.10';
import { AdminTariffTable } from './AdminTariffTable.js?v=20261028.5';
import { escapeHtml as esc, displayName } from '../../utils/text.js?v=20261027.10';
import { configSections } from '../../models/AdminConfigModel.js?v=20261105.1';
import { mediaUrl } from '../../utils/media.js?v=20261027.10';
import { API_CONFIG } from '../../api/config.js?v=20261027.10';
function categorySlug(value) {
  const chars = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya','ä':'ae','ö':'oe','ü':'ue','ß':'ss'};
  return [...String(value).toLowerCase()].map(char=>chars[char] ?? char).join('').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,100).replace(/-+$/,'');
}
const sectionMenu = {
  splice_types: ['Заделки', 'Какие концы можно заказать'],
  splice_materials: ['Тарифные материалы', 'Из чего считается цена заделки'],
  splice_prices: ['Тарифы работ', 'Цены по работе, группе троса и диаметру'],
  configurator_extras: ['Дополнительные опции', 'Доплаты и дополнительные услуги'],
  material_groups: ['Группы материалов каталога', 'Группы для характеристик каната'],
  materials: ['Материалы каталога', 'Материалы внутри групп'],
  configurator_settings: ['Настройки расчёта', 'Длина, запас, сроки и срочность'],
};
const sectionOrder = ['material_groups', 'materials', 'splice_types', 'splice_materials', 'splice_prices', 'configurator_extras', 'configurator_settings'];
const settingsGroups = [
  ['length', 'Длина каната', ['min_length_m','max_length_m']],
  ['allowance', 'Запас на концы', ['splice_allowance_until_mm','splice_allowance_until_m','splice_allowance_over_m']],
  ['urgency', 'Сроки и срочность', ['standard_turnaround_hours','urgent_turnaround_hours','urgent_surcharge_per_splice','urgent_max_splices']],
  ['vat', 'НДС', ['vat_rate','vat_note']],
];
const settingsHints = {
  min_length_m:'Самая короткая длина изделия.',
  max_length_m:'Самая длинная длина изделия.',
  splice_allowance_until_mm:'До какого диаметра действует запас ниже.',
  splice_allowance_until_m:'Запас на каждый конец до этого диаметра.',
  splice_allowance_over_m:'Запас на каждый конец больше этого диаметра.',
  standard_turnaround_hours:'Срок обычного заказа, часов.',
  urgent_turnaround_hours:'Срок срочного заказа, часов.',
  urgent_surcharge_per_splice:'Доплата за работу при срочном заказе.',
  urgent_max_splices:'Больше этого числа срочно заказать нельзя.',
  vat_rate:'Ваша ставка НДС.',
  vat_note:'Пометка о НДС.',
};
const sectionHints = {
  categories:{slug:'Заполнится из названия.',index:'Место в списке: меньше — выше.'},
  material_groups:{index:'Место в списке: меньше — выше.'},
  materials:{material_group_id:'Группа материала; в карточке товара выбирается она.',index:'Место материала в группе.'},
  splice_types:{category:'Где покупатель ищет работу.',visual_type:'Вид на схеме в конфигураторе.',index:'Место в списке: меньше — выше.'},
  splice_materials:{name:'Из чего считается цена.'},
  splice_prices:{splice_type_id:'Для какой работы цена.',splice_material_id:'Для какой группы троса.',diameter_from_mm:'С какого диаметра. Пусто — без ограничения.',diameter_to_mm:'До какого диаметра. Пусто — без ограничения.',price:'Цена работы для этой группы и диаметра.'},
  configurator_extras:{price:'Стоимость опции; итог зависит от начисления.',billing_type:'За заказ, за изделие или за метр.',index:'Место в списке: меньше — выше.'},
};
export class AdminConfigView {
  constructor(root, { sections = sectionOrder.filter(key => API_CONFIG.CATALOG_V2 || !['material_groups', 'materials'].includes(key)), title = 'Конфигуратор и цены' } = {}) {
    this.root=root;this.events=new AbortController();this.baseline='';
    this.pendingImage = null; this.pendingImageUrl = '';
    this.sectionCards = root.id === 'panel-configurator' && sections.length > 1;
    root.removeAttribute('data-savable');
    root.innerHTML=`<header class="panel__head"><h1 class="panel__title">${esc(title)}</h1></header>
      <p>${this.sectionCards ? 'Заполняйте разделы по порядку. Цены — в евро.' : (sections.includes('material_groups') || sections.includes('categories')) ? 'Разделы каталога. Выберите запись, чтобы изменить название, переводы или место.' : 'Выберите вид настройки, затем запись. Цены — в евро.'}</p>
      ${this.sectionCards ? `<nav class="config-section-menu" aria-label="Разделы конфигуратора и цен">${sections.map(key=>{const [name,description]=sectionMenu[key]||[configSections[key]?.title||key,''];return `<button type="button" class="config-section-card" data-config-section-choice="${esc(key)}" aria-pressed="false"><span class="config-section-card__name">${esc(name)}</span><span class="config-section-card__hint">${esc(description)}</span></button>`;}).join('')}</nav>` : ''}
      <div class="config-admin-toolbar"><label class="field"${sections.length === 1 || this.sectionCards ? ' hidden' : ''}>Что редактируем<select class="field__input" data-config-section${this.sectionCards ? ' data-native-select' : ''}>${sections.map(key=>`<option value="${key}">${esc(key === 'material_groups' ? 'Разделы каталога' : configSections[key]?.title || 'Заделки')}</option>`).join('')}</select></label>
      <button class="btn" data-config-new type="button">Добавить</button><button class="btn" data-config-refresh type="button">Обновить</button></div>
      <div data-config-record></div><p data-config-status role="status"></p><div data-config-editor></div>`;
    this.recordList = new AdminTariffTable(root.querySelector('[data-config-record]'), this.events.signal);
    this.recordList.categoryCards = sections.length === 1 && ['categories', 'material_groups'].includes(sections[0]);
  }
  bind(actions) {
    const opts={signal:this.events.signal};
    this.root.querySelector('[data-config-section]').addEventListener('change',e=>actions.section(e.target.value),opts);
    this.recordList.onSelect = actions.select;
    this.recordList.onSavePrices = actions.savePrices;
    this.root.querySelector('[data-config-new]').addEventListener('click',actions.create,opts);
    this.root.querySelector('[data-config-refresh]').addEventListener('click',actions.refresh,opts);
    this.root.addEventListener('submit',e=>{e.preventDefault();if(e.target.reportValidity()) actions.save();},opts);
    this.root.addEventListener('click',e=>{
      const sectionButton=e.target.closest('[data-config-section-choice]');
      if(sectionButton && !sectionButton.disabled){actions.section(sectionButton.dataset.configSectionChoice);return;}
      const choose = e.target.closest('[data-image-choose]');
      if (choose && !choose.disabled) this.root.querySelector('[data-image-file]').click();
      if(e.target.matches('[data-config-remove]'))actions.remove();
      if(e.target.matches('[data-image-remove]'))actions.removeImage();
      if(e.target.matches('[data-image-retry]'))actions.retryImage();
      if(e.target.matches('[data-image-discard]'))actions.discardImage();
      if(e.target.matches('[data-config-translation-remove]'))actions.removeTranslation(Number(e.target.dataset.configTranslationRemove));
    },opts);
    this.root.addEventListener('change',e=>{
      if (!e.target.matches('[data-image-file]')) return;
      const file = e.target.files?.[0];
      // Keep the File object for this request, but allow selecting the same file again after an error.
      e.target.value = '';
      if (file) actions.upload(file);
    },opts);
    this.root.addEventListener('input', e => {
      if (e.target.closest('[data-settings-form]')) this.updateSettingsExamples();
      if (e.target.name === 'slug' && this.isNewCategory) { this.autoCategorySlug = !e.target.value.trim(); return; }
      if (!this.autoCategorySlug) return;
      if (!['name_rus','name_eng','name_ger'].includes(e.target.name)) return;
      const form = e.target.form;
      const value = ['name_ger','name_eng','name_rus'].map(key => form.elements[key]?.value.trim()).find(Boolean) || '';
      const base = categorySlug(value);
      const taken = new Set((this.categoryItems || []).map(item => String(item.slug || '').toLowerCase()));
      let candidate = base, number = 2;
      while (candidate && taken.has(candidate)) { const suffix = `-${number++}`; candidate = base.slice(0, 100 - suffix.length).replace(/-+$/, '') + suffix; }
      form.elements.slug.value = candidate;
    }, opts);
    window.addEventListener('beforeunload',e=>{if(this.dirty()){e.preventDefault();e.returnValue='';}},opts);
  }
  values(){return Object.fromEntries(Array.from(this.root.querySelector('form')?.elements || []).filter(e=>e.name).map(e=>[e.name,e.type==='checkbox'?e.checked:e.value]));}
  remember(){this.baseline=JSON.stringify(this.values());}
  editorDirty(){return Boolean(this.pendingImage || (this.baseline && this.baseline!==JSON.stringify(this.values())));}
  dirty(){return this.editorDirty() || Boolean(this.recordList.priceDrafts?.size);}
  allowDiscard(includePrices=true){return !(includePrices ? this.dirty() : this.editorDirty()) || window.confirm('Отменить несохранённые изменения?');}
  message(text, type = 'info') { AdminNotificationView.message(this.root.querySelector('[data-config-status]'), text, type); }
  busy(value){this.root.querySelectorAll('input,select,button,textarea').forEach(e=>e.disabled=value);this.recordList.busy(value);}
  clear(){this.root.querySelector('[data-config-editor]').replaceChildren();this.baseline='';this.recordList.select(null);}
  list(items,section,sources=this.listSources||{}){
    this.listSources=sources;
    if(section==='categories')this.categoryItems=items;
    if(this.listSection!==section){this.recordList.reset();this.listSection=section;}
    this.recordList.tariffs=section==='splice_prices';
    if(section==='splice_prices')this.recordList.setTariffs(items,sources);
    else this.recordList.setItems(items.map(item=>{
      const work=sources.splice_types?.find(type=>Number(type.id)===Number(item.splice_type_id));
      const material=sources.splice_materials?.find(type=>Number(type.id)===Number(item.splice_material_id));
      return {id:item.product_id??item.id,
        label:section==='splice_prices'?`${displayName(work)||`Работа #${item.splice_type_id}`} · ${displayName(material)||`Материал #${item.splice_material_id}`}`:displayName(item)||item.construction||`Запись #${item.id}`,
        detail:[section==='splice_prices'?String(item.price)+' € · '+String(item.diameter_from_mm??'−∞')+'–'+String(item.diameter_to_mm??'∞')+' мм':'',item.is_active===false?'Скрыт с сайта':''].filter(Boolean).join(' · '),
        search:(item.translations||[]).map(t=>t.name).join(' '), image:mediaUrl(item.image_url)};
    }));
    this.recordList.root.hidden=Boolean(configSections[section]?.singleton);
    this.root.querySelector('[data-config-new]').hidden=section==='links'||Boolean(configSections[section]?.singleton);
    this.setSection(section);
  }
  setSection(section){
    this.root.querySelector('[data-config-section]').value=section;
    this.root.querySelectorAll('[data-config-section-choice]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.configSectionChoice===section)));
  }
  updateSettingsExamples(){
    const form=this.root.querySelector('[data-settings-form]');if(!form)return;
    const value=name=>form.elements.namedItem(name)?.value.trim() || '';
    const [limit,under,over]=['splice_allowance_until_mm','splice_allowance_until_m','splice_allowance_over_m'].map(value);
    const allowance=form.querySelector('[data-settings-allowance-example]');
    allowance.textContent=limit && under!=='' && over!=='' ? `На каждый конец: до ${limit} мм включительно — ${under} м; больше — ${over} м. Прибавляется к длине каната.` : 'Заполните границу и оба запаса, чтобы увидеть правило.';
    for(const name of ['standard_turnaround_hours','urgent_turnaround_hours']){
      const output=form.querySelector(`[data-settings-days="${name}"]`), raw=value(name), hours=Number(raw);
      output.textContent=raw!=='' && Number.isFinite(hours) && hours>=0 ? `Это ${new Intl.NumberFormat('ru-RU',{maximumFractionDigits:2}).format(hours/24)} суток (по 24 часа).` : '';
    }
  }
  select(id){this.recordList.select(id);}
  render(section,item={},sources={}, {preserveDisclosures=false}={}) {
    const disclosureState = captureDisclosures(this.root, preserveDisclosures);
    this.recordList.select(item.id);
    const schema=configSections[section];
    this.isNewCategory = section==='categories' && !item.id;
    this.autoCategorySlug = this.isNewCategory;
    const renderField=f=>{
      const value=item[f.name] ?? f.default ?? (f.type==='checkbox'?true:'');
      if(f.name==='code')return `<input type="hidden" name="code" value="${esc(value)}">`;
      if(f.type==='checkbox')return `<label><input type="checkbox" name="${f.name}" ${value?'checked':''}> ${esc(f.label)}</label>`;
      const attrs=`name="${f.name}" class="field__input" ${f.required?'required':''}`;
      const options=f.source?Object.fromEntries((sources[f.source]||[]).map(o=>[o.id,displayName(o)||`#${o.id}`])):f.options;
      const input=options?`<select ${attrs} required>${Object.entries(options).map(([key,label])=>`<option value="${esc(key)}" ${String(value)===key?'selected':''}>${esc(label)}</option>`).join('')}</select>`
        :`<input ${attrs} type="${f.type}" value="${esc(value)}" ${f.type==='number'?`min="${f.min??0}" step="${f.integer?'1':'0.01'}"`: 'maxlength="255"'}>`;
      const hint=section==='configurator_settings' ? settingsHints[f.name] : sectionHints[section]?.[f.name];
      return `<label class="field">${esc(f.label)}${input}${hint?`<small class="field__hint">${esc(hint)}</small>`:''}${['standard_turnaround_hours','urgent_turnaround_hours'].includes(f.name)?`<small class="field__hint" data-settings-days="${f.name}"></small>`:''}</label>`;
    };
    const fields=schema.fields.map(renderField).join('');
    const settingsFields=section==='configurator_settings' ? settingsGroups.map(([key,title,names])=>`<details class="admin-disclosure" data-editor-disclosure="settings-${key}" open><summary>${title}</summary>${key==='allowance'?'<p class="admin-settings-example" data-settings-allowance-example></p>':''}<div class="admin-fields">${names.map(name=>renderField(schema.fields.find(field=>field.name===name))).join('')}</div></details>`).join('') : '';
    const translations=schema.translated?['rus','eng','ger'].map(locale=>{const t=item.translations?.find(t=>t.locale===locale)||{};return `<div class="admin-language-heading">${{rus:'Русский',eng:'Английский',ger:'Немецкий'}[locale]}</div><label class="field">Название ${{rus:'(рус.)',eng:'(англ.)',ger:'(нем.)'}[locale]}<input class="field__input" name="name_${locale}" maxlength="255" value="${esc(t.name||'')}"></label>${schema.description?`<label class="field">Описание ${{rus:'(рус.)',eng:'(англ.)',ger:'(нем.)'}[locale]}<textarea class="field__input" name="description_${locale}" rows="3">${esc(t.description||'')}</textarea></label>`:''}`;}).join(''):'';
    this.root.querySelector('[data-config-editor]').innerHTML=`<h2>${esc(schema.title)}${item.id?` #${item.id}`:''}</h2><form class="product-editor admin-card" ${section==='configurator_settings'?'data-settings-form':''}><div class="admin-disclosures-group">${section==='configurator_settings'?settingsFields:`<details class="admin-disclosure" data-editor-disclosure="parameters" open><summary>Основные параметры</summary><div class="admin-fields">${fields}</div></details>`}${translations ? `<details class="admin-disclosure" data-editor-disclosure="translations" open><summary>Названия и переводы</summary><p class="admin-editor-hint">Заполните название хотя бы на одном языке.</p><div class="admin-fields">${translations}</div></details>` : ''}</div><div class="admin-form-actions"><button class="btn btn--primary" type="submit">Сохранить</button>${item.id&&!schema.singleton?'<button class="btn btn--danger" type="button" data-config-remove>Удалить запись</button>':''}</div></form>${((section==='categories') || (section==='splice_types'&&item.id))?`<div class="config-admin-upload admin-card">
      <span class="field__label">Изображение записи</span>
      <input type="file" accept=".jpg,.jpeg,.png,.webp,.heic,.heif" data-image-file hidden>
      <button class="btn btn--primary" type="button" data-image-choose aria-describedby="${this.root.id}-image-hint">Выбрать изображение</button>
      <p class="field__hint" id="${this.root.id}-image-hint">${section==='categories'&&!item.id?'Будет загружено после сохранения категории.':'Загрузится сразу после выбора.'} JPG, PNG, WebP, HEIC/HEIF — до 10 МБ.</p>
      <p class="config-admin-upload__status" data-image-upload-status role="status"></p>
    </div>`:''}`;
    restoreDisclosures(this.root, disclosureState);
    if(section==='configurator_settings')this.updateSettingsExamples();
    this.remember();
    if(section==='categories'||(section==='splice_types'&&item.id)){this.root.querySelector('.config-admin-upload').insertAdjacentHTML('beforebegin','<div data-image-preview></div>');if(this.pendingImage)this.showPendingImage(this.pendingImage);else this.image(item.image_url);}
    const known=(item.translations||[]).filter(t=>t.id&&!t.fallback);
    if(schema.translated&&item.id&&known.length>1)this.root.querySelector('[data-config-editor]').insertAdjacentHTML('beforeend',`<h3>Удалить перевод</h3><p>Один язык должен остаться, иначе покажется другой.</p><div class="config-admin-toolbar">${known.map(t=>`<button class="btn btn--danger" type="button" data-config-translation-remove="${Number(t.id)}">Удалить ${{rus:'(рус.)',eng:'(англ.)',ger:'(нем.)'}[t.locale] || t.locale.toUpperCase()}</button>`).join('')}</div>`);
    if(['splice_types','categories'].includes(section)&&item.id&&!known.length)this.root.querySelector('[data-config-editor]').insertAdjacentHTML('beforeend','<p>Переводы появятся после сохранения записи.</p>');
  }
  setPendingImage(file){
    this.clearPendingImage(); this.pendingImage=file;
    this.pendingImageUrl=URL.createObjectURL(file); this.showPendingImage(file);
  }
  clearPendingImage(){
    if(this.pendingImageUrl)URL.revokeObjectURL(this.pendingImageUrl);
    this.pendingImage=null; this.pendingImageUrl='';
  }
  showPendingImage(file){
    const preview=this.root.querySelector('[data-image-preview]');if(!preview)return;
    preview.innerHTML=`<img class="admin-image-preview" src="${esc(this.pendingImageUrl)}" alt="Предпросмотр выбранного изображения"><p>${esc(file.name)} — ещё не загружено</p><p><button type="button" class="btn btn--ghost" data-image-discard>Убрать выбранное фото</button>${this.autoCategorySlug?'':' <button type="button" class="btn btn--primary" data-image-retry>Повторить загрузку</button>'}</p>`;
    const choose=this.root.querySelector('[data-image-choose]');if(choose)choose.textContent='Выбрать другое изображение';
  }
  image(value){
    const preview=this.root.querySelector('[data-image-preview]');if(!preview)return;
    const url=mediaUrl(value);
    const choose=this.root.querySelector('[data-image-choose]');
    if(choose){choose.dataset.idleLabel=url?'Выбрать другое изображение':'Выбрать изображение';choose.textContent=choose.dataset.idleLabel;}
    preview.innerHTML=url?`<img class="admin-image-preview" src="${esc(url)}" alt="Изображение записи"><p><button class="btn btn--danger" type="button" data-image-remove>Удалить изображение</button></p>`:'<p>Изображение не загружено.</p>';
  }
  uploadState(state, filename = '') {
    const box = this.root.querySelector('.config-admin-upload');
    if (!box) return;
    box.setAttribute('aria-busy', String(state === 'loading'));
    const button = box.querySelector('[data-image-choose]');
    button.textContent = state === 'loading' ? 'Загружаем…' : button.dataset.idleLabel || 'Выбрать изображение';
    const status = box.querySelector('[data-image-upload-status]');
    status.textContent = state === 'loading' ? `Загружаем: ${filename}`
      : state === 'success' ? `Загружено: ${filename}`
      : state === 'error' ? `Не удалось загрузить: ${filename}. Для повтора выберите файл ещё раз.`
      : '';
  }
  renderLinks(types,links){const ids=links.map(l=>Number(l.splice_type_id));this.root.querySelector('[data-config-editor]').innerHTML=`<p>Отметьте доступные концы. Пусто — доступны все варианты.</p><form class="product-editor admin-card"><div class="admin-checkbox-grid">${types.map(t=>`<label class="admin-toggle"><input type="checkbox" name="splice_${Number(t.id)}" ${ids.includes(Number(t.id))?'checked':''}><span>${esc(displayName(t))}${t.is_active===false?' (отключена)':''}</span></label>`).join('')}</div><div class="admin-form-actions"><button class="btn btn--primary" type="submit">Сохранить заделки</button></div></form>`;this.remember();}
  destroy(){this.clearPendingImage();this.events.abort();}
}
