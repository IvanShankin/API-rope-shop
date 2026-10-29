import { adminConfigApi as api } from '../api/adminConfigApi.js?v=20261027.10';
import { configSections, configPayload, automaticConfigCode } from '../models/AdminConfigModel.js?v=20261028.8';
import { AdminConfigView } from '../views/admin/AdminConfigView.js?v=20261028.16';
import { API_CONFIG } from '../api/config.js?v=20261027.10';
export class AdminConfigController {
  constructor(root, options = {}){
    this.onCatalogChanged = options.onCatalogChanged;
    this.view=new AdminConfigView(root, options);this.section=this.view.root.querySelector('[data-config-section]').value;this.sources={};this.ready=false;
    this.view.bind({section:key=>this.load(key),refresh:()=>this.load(),select:id=>this.select(id),create:()=>{
      if(this.busy||!this.ready||!this.view.allowDiscard(false))return;this.view.clearPendingImage();this.item=null;this.uncertain=false;this.view.select(null);this.view.render(this.section,{},this.sources);this.view.message('Новая запись. Заполните поля и сохраните.');
    },save:()=>this.save(),savePrices:()=>this.savePrices(),upload:file=>this.upload(file),retryImage:()=>this.upload(this.view.pendingImage),discardImage:()=>this.discardImage(),remove:()=>this.remove(),removeImage:()=>this.removeImage(),removeTranslation:id=>this.removeTranslation(id)});
  }
  lock(value){this.busy=value;this.view.busy(value);}
  async load(section=this.section){
    if(this.busy||!this.view.allowDiscard()){this.view.setSection(this.section);return;}
    this.lock(true);this.view.message('Загружаем…');
    try{
      const listSection=section==='links'?'rope_products':section;
      const dependencies=section==='links'?['splice_types']:(configSections[section]?.fields||[]).map(f=>f.source).filter(Boolean);
      const names=[...new Set([listSection,...dependencies])];
      const results=await Promise.all(names.map(name=>api.list(name)));
      const loaded=Object.fromEntries(names.map((name,index)=>[name,results[index]]));
      const items=loaded[listSection];
      this.section=section;this.sources=loaded;this.items=Array.isArray(items)?items:[];
      this.view.clearPendingImage();this.view.recordList.clearPriceDrafts();this.item=null;this.uncertain=false;this.view.clear();this.view.list(this.items,section,this.sources);this.ready=true;
      if(configSections[section]?.singleton){this.item=items;this.view.render(section,items,this.sources);}
      this.view.message(configSections[section]?.singleton ? 'Измените настройки и нажмите «Сохранить».' : 'Выберите запись для изменения или добавьте новую.');
    }catch(e){this.view.message(`Не удалось загрузить: ${e.message}. Повторите обновление.`, 'error');this.view.setSection(this.section);}
    finally{this.lock(false);}
  }
  async select(id){
    if(this.busy)return;
    if(!this.view.allowDiscard(false)){this.view.select(this.item?.product_id??this.item?.id);return;}
    if(!id){this.view.clearPendingImage();this.item=null;this.view.clear();return;}
    this.view.clearPendingImage();
    this.lock(true);
    try{
      let item;
      if(this.section==='links'){
        const links=await api.links(id);item=this.items.find(i=>Number(i.product_id)===Number(id));this.view.renderLinks(this.sources.splice_types,links);
      }else if(this.section==='splice_types' && !API_CONFIG.SPLICE_DETAIL){
        const lists=await Promise.all(['rus','eng','ger'].map(locale=>api.list('splice_types',{locale})));
        item={...this.items.find(i=>Number(i.id)===Number(id)),translations:lists.map((list,index)=>{const localized=list.find(i=>Number(i.id)===Number(id));return {name:localized?.name,description:localized?.description,locale:['rus','eng','ger'][index],fallback:true};})};
        this.view.render(this.section,item,this.sources);
      }else{item=await api.detail(this.section,id);this.view.render(this.section,item,this.sources);}
      this.item=item;this.originalTranslations=structuredClone(item?.translations || []);this.uncertain=false;this.view.message('Изменения сохраняются кнопкой формы.');
    }catch(e){this.view.select(this.item?.product_id??this.item?.id);this.view.message(e.message, 'error');}
    finally{this.lock(false);}
  }
  async save(){
    if(this.busy||this.uncertain)return;
    if(this.section==='splice_prices' && this.view.recordList.priceDrafts.has(String(this.item?.id))){this.view.message('Сначала сохраните цену в таблице или отмените её изменение.', 'warning');return;}
    const values=this.view.values();const schema=configSections[this.section];let data;
    if(!this.item && schema?.fields.some(field=>field.name==='code') && !values.code){
      values.code=automaticConfigCode(this.section,values,this.items);
    }
    try{if(this.section!=='links')data=configPayload(this.section,values,this.items,this.item?.id);}catch(e){this.view.message(e.message, 'error');return;}
    if(!this.item && data?.code)this.view.root.querySelector('input[name="code"]').value=data.code;
    const creatingRecord = !this.item && this.section !== 'links' && !schema.singleton;
    this.lock(true);let committed=false;let imageError='';
    try{
      if(this.section==='links')await api.saveLinks(this.item.product_id,Object.keys(values).filter(k=>k.startsWith('splice_')&&values[k]).map(k=>Number(k.slice(7))));
      else{
        if(this.section==='splice_prices')configPayload(this.section,values,await api.list('splice_prices'),this.item?.id);
        const {translations,...fields}=data;const creating=!this.item&&!schema.singleton;
        if(!creating)delete fields.code;
        const index=fields.index;
        if(!creating && schema.separateIndex)delete fields.index;
        if(!creating && translations && this.originalTranslations?.some(t=>t.name&&!translations.some(next=>next.locale===t.locale))) {
          throw new Error('Пустое название не удаляет существующий перевод. Верните название или обновите запись.');
        }
        const saved=await api.save(this.section,this.item?.id,creating?data:fields,schema.singleton);
        this.item=saved;committed=true;
        if(!creating && schema.separateIndex && Number(saved.index)!==index){await api.order(this.section,saved.id,index);this.item.index=index;}
        if(translations&&!creating){
          for(const t of translations){
            const original=this.originalTranslations?.find(x=>x.locale===t.locale);
            if(original && original.name===t.name && (original.description || null)===(t.description || null)) continue;
            const existing=saved.translations?.find(x=>x.locale===t.locale);
            const savedTranslation=await api.translation(this.section,saved.id,{...t,...(existing?{id:existing.id}:{})});
            // Keep the server ID so this form can update or delete the new translation.
            this.item.translations=[...(this.item.translations||[]).filter(x=>x.locale!==t.locale),{...existing,...t,...savedTranslation,fallback:false}];
          }
        }
        this.originalTranslations=structuredClone(this.item.translations || []);
        if(creating && this.section==='categories' && this.view.pendingImage){
          try {
            const uploaded=await api.upload(this.item.id,this.view.pendingImage,this.section);
            if(!uploaded?.image_url)throw new Error('Сервер не вернул адрес изображения.');
            this.item.image_url=uploaded.image_url;this.view.clearPendingImage();
          } catch(error) { imageError=error.message || 'Ошибка загрузки.'; }
        }
      }
      if(this.section!=='links')this.view.render(this.section,this.item,this.sources,{preserveDisclosures:true});
      this.view.remember();if(!imageError)this.view.message('Сохранено в базе. Обновите конфигуратор, чтобы увидеть изменения.', ['categories', 'material_groups', 'materials'].includes(this.section) ? 'info' : 'success');
      if(this.section!=='links'&&!schema.singleton){
        const entry={...this.item,name:data.translations?.[0]?.name || this.item.name};
        this.items=[...this.items.filter(i=>Number(i.id)!==Number(entry.id)),entry];
        this.view.list(this.items,this.section);this.view.select(entry.id);
      }
      if (['categories', 'material_groups', 'materials'].includes(this.section)) {
        this.view.message('Сохранено. Обновляем списки каталога…');
        try {
          await this.onCatalogChanged?.();
          if(!imageError)this.view.message('Сохранено. Списки каталога обновлены.', 'success');
        } catch {
          this.view.message('Сохранено, но список товаров не удалось обновить. Нажмите «Обновить» в товарах.', 'warning');
        }
      }
      if(imageError)this.view.message(`Категория сохранена, но фото не загрузилось: ${imageError} Нажмите «Повторить загрузку».`, 'warning');
      if(creatingRecord && !imageError){
        this.item=null;this.uncertain=false;this.view.select(null);this.view.render(this.section,{},this.sources);
      }
    }catch(e){
      if(!this.item&&!e.status)this.uncertain=true;
      this.view.message(`${committed?'Основная запись сохранена, но дополнительные изменения завершены не полностью.':'Не удалось подтвердить сохранение.'} ${e.message}. Обновите список перед повтором при потере связи.`, 'error');
    }finally{this.lock(false);}
  }
  async savePrices(){
    if(this.busy || this.section!=='splice_prices')return;
    if(this.view.editorDirty()){this.view.message('Сначала сохраните или отмените изменения в открытой форме тарифа.', 'warning');return;}
    const drafts=[...this.view.recordList.priceDrafts];
    if(!drafts.length)return;
    const prepared=[];
    for(const [id,raw] of drafts){
      const text=String(raw).trim().replace(',','.');
      if(!/^(?:0|[1-9]\d{0,7})(?:\.\d{1,2})?$/.test(text)){
        this.view.message(`Проверьте цену тарифа #${id}: число от 0 до 99999999,99, не более двух знаков после запятой.`, 'error');
        this.view.recordList.root.querySelector(`[data-tariff-price="${id}"]`)?.setAttribute('aria-invalid','true');return;
      }
      const original=this.items.find(item=>String(item.id)===id);
      if(!original){this.view.message(`Тариф #${id} не найден. Обновите список.`, 'error');return;}
      prepared.push({id,price:Number(text),original});
    }
    this.lock(true);this.view.message('Сохраняем цены…');
    const failed=[];let savedCount=0;let selectedUpdated=false;
    try {
      for(const draft of prepared){
        try {
          const current=await api.detail('splice_prices',draft.id);
          if(Number(current.price)!==Number(draft.original.price) && Number(current.price)!==draft.price) throw new Error('цена изменилась на сервере; обновите список и проверьте');
          const result=Number(current.price)===draft.price ? current : await api.save('splice_prices',draft.id,{price:draft.price});
          if(!result || Number(result.price)!==draft.price)throw new Error('сервер не подтвердил новую цену');
          this.items=this.items.map(item=>String(item.id)===draft.id ? {...item,...result} : item);
          this.view.recordList.priceDrafts.delete(draft.id);savedCount++;
          if(String(this.item?.id)===draft.id){this.item={...this.item,...result};selectedUpdated=true;}
        }catch(error){failed.push(`#${draft.id}: ${error.message || 'ошибка сохранения'}`);}
      }
      this.view.list(this.items,this.section,this.sources);
      if(selectedUpdated)this.view.render(this.section,this.item,this.sources,{preserveDisclosures:true});
      if(failed.length)this.view.message(`Сохранено цен: ${savedCount}; не сохранено: ${failed.length}. ${failed.join('; ')}. Несохранённые значения остались в таблице.`, 'warning');
      else this.view.message(`Сохранено цен: ${savedCount}.`, 'success');
    }finally{this.lock(false);}
  }
  async upload(file){
    if(this.busy||!file)return;
    if(!this.item?.id && this.section!=='categories')return;
    if(!/\.(jpe?g|png|webp|heic|heif)$/i.test(file.name)){
      this.view.uploadState('error',file.name);this.view.message('Выберите изображение JPG, PNG, WebP, HEIC или HEIF.', 'warning');return;
    }
    if(!file.size||file.size>10*1024*1024){
      this.view.uploadState('error',file.name);this.view.message(file.size?'Выберите изображение размером до 10 МБ.':'Выбранный файл пустой. Выберите другое изображение.', 'warning');return;
    }
    if(!this.item?.id){this.view.setPendingImage(file);this.view.message('Фото выбрано и загрузится после сохранения категории.');return;}
    this.lock(true);this.view.uploadState('loading',file.name);
    try{
      const saved=await api.upload(this.item.id,file,this.section);
      if(!saved?.image_url)throw new Error('Сервер не вернул адрес изображения. Обновите запись, чтобы проверить результат.');
      this.item.image_url=saved.image_url;this.view.clearPendingImage();this.view.image(saved.image_url);this.syncCategoryImage(saved.image_url);this.view.uploadState('success',file.name);
      this.view.message('Изображение загружено.', 'success');
    }catch(e){this.view.uploadState('error',file.name);this.view.message(`Загрузка не завершена: ${e.message}`, 'error');}
    finally{this.lock(false);}
  }
  discardImage(){this.view.clearPendingImage();this.view.image(this.item?.image_url);this.view.message('Выбранное фото убрано.');}
  async removeImage(){
    if(this.busy||!['splice_types','categories'].includes(this.section)||!this.item?.id||!window.confirm('Удалить изображение этой заделки?'))return;
    this.lock(true);
    try{const saved=await api.removeImage(this.item.id,this.section);this.item.image_url=saved.image_url;this.view.image(saved.image_url);this.syncCategoryImage(saved.image_url);this.view.uploadState('idle');this.view.message('Изображение удалено.', 'success');}
    catch(e){this.view.message(`Не удалось подтвердить удаление изображения: ${e.message}. Обновите запись перед повтором.`, 'error');}
    finally{this.lock(false);}
  }
  syncCategoryImage(imageUrl){
    if(this.section!=='categories')return;
    this.items=this.items.map(item=>Number(item.id)===Number(this.item.id)?{...item,image_url:imageUrl}:item);
    this.view.list(this.items,this.section,this.sources);
    this.view.select(this.item.id);
  }
  async removeTranslation(id){
    const known=this.item?.translations?.filter(t=>t.id&&!t.fallback)||[];
    const translation=known.find(t=>Number(t.id)===Number(id));
    if(this.busy||known.length<=1||!translation||!this.view.allowDiscard()||!window.confirm(`Удалить перевод ${translation.locale.toUpperCase()} этой записи? Это действие нельзя отменить.`))return;
    this.lock(true);let committed=false;
    try{
      await api.removeTranslation(this.section,id);committed=true;
      if(this.section==='splice_types')this.item.translations=this.item.translations.filter(t=>t.locale!==translation.locale);
      else this.item=await api.detail(this.section,this.item.id);
      this.originalTranslations=structuredClone(this.item.translations||[]);this.view.render(this.section,this.item,this.sources,{preserveDisclosures:true});
      this.view.message('Перевод удалён. Последний перевод записи сохраняется. Обновите список, чтобы увидеть новое название.', 'success');
    }catch(e){this.view.message(`${committed?'Перевод удалён, но не удалось обновить форму.':'Не удалось подтвердить удаление перевода.'} ${e.message}. Обновите запись перед повтором.`, 'error');}
    finally{this.lock(false);}
  }
  async remove(){
    const id=this.item?.id;
    if(this.section==='splice_prices'&&this.view.recordList.priceDrafts.size){this.view.message('Сначала сохраните или отмените изменения цен в таблице.', 'warning');return;}
    if(this.busy||!id||configSections[this.section]?.singleton||!this.view.allowDiscard())return;
    if(!window.confirm(`Удалить запись #${id}? Это действие нельзя отменить. Связанные записи могут препятствовать удалению.`))return;
    this.lock(true);
    try{await api.remove(this.section,id);this.items=this.items.filter(item=>Number(item.id)!==Number(id));this.item=null;this.view.clear();this.view.list(this.items,this.section);this.view.message('Запись удалена.', 'success');}
    catch(e){this.view.message(`Не удалось подтвердить удаление: ${e.message}. Если запись используется, отключите её вместо удаления. При потере связи обновите список.`, 'error');}
    finally{this.lock(false);}
  }
  destroy(){this.view.destroy();}
}
