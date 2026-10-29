import {siteContentApi as api} from '../api/siteContentApi.js?v=20261027.10';
import {contentPages,contentSlots,gallerySections,contentPayload,galleryPayload} from '../models/SiteContentModel.js?v=20261027.10';
import {AdminContentView} from '../views/admin/AdminContentView.js?v=20261028.16';
export class AdminContentController {
  constructor(root,gallery=false) {
    this.gallery=gallery;this.section=gallery?'work_photos':'home';this.ready=false;this.busy=false;this.item=null;
    this.view=new AdminContentView(root,gallery?gallerySections:contentPages,gallery);
    this.view.bind({load:key=>this.load(key),select:id=>this.select(id),save:()=>this.save(),remove:()=>this.remove(),create:()=>{
      if(!this.ready||this.busy||!this.view.allowDiscard())return;this.item=null;this.uncertain=false;this.view.select(null);this.view.render();this.view.message('Выберите фотографию и заполните подписи.');
    }});
  }
  lock(value){this.busy=value;this.view.busy(value);}
  async records(section=this.section) {
    if(this.gallery)return api.photos(section,'rus',true);
    const blocks=await api.blocks(section,'rus',true);
    return contentSlots.map((slot,i)=>({...blocks.find(b=>b.block_code===slot.code),id:i+1,slot,label:slot.label})).filter(b=>b.slot.page===section);
  }
  async load(section=this.section) {
    if(this.busy||!this.view.allowDiscard()){this.view.setSection(this.section);return;}
    this.lock(true);this.view.message('Загружаем…');
    try {const items=await this.records(section);this.section=section;this.view.setSection(section);this.items=items;this.item=null;this.uncertain=false;this.ready=true;this.view.clear();this.view.list(items);this.view.message('Выберите запись для редактирования.');}
    catch(e){this.view.setSection(this.section);this.view.message(`Не удалось загрузить: ${e.message}. Повторите обновление.`, 'error');}
    finally{this.lock(false);}
  }
  async select(id) {
    if(this.busy||!this.ready)return;
    if(!this.view.allowDiscard()){this.view.select(this.item?.id);return;}
    if(!id){this.item=null;this.view.clear();return;}
    this.lock(true);
    try {const item=this.gallery?await api.photo(this.section,id):this.items.find(b=>Number(b.id)===Number(id));if(!item)throw new Error('Запись не найдена');this.item=item;this.uncertain=false;this.view.render(item);this.view.message('Измените поля и сохраните.');}
    catch(e){this.view.select(this.item?.id);this.view.message(e.message, 'error');}
    finally{this.lock(false);}
  }
  async save() {
    if(this.busy)return;
    if(this.uncertain){this.view.message('Ответ на загрузку не получен. Обновите список перед повтором, чтобы проверить созданную фотографию.', 'warning');return;}
    let data;const file=this.view.file();
    try {data=this.gallery?galleryPayload(this.view.values()):contentPayload(this.item.slot,this.view.values());if(file?.size>10*1024*1024)throw new Error('Размер фотографии больше 10 МБ.');}
    catch(e){this.view.message(e.message, 'error');return;}
    const newPhoto=this.gallery&&!this.item;
    this.lock(true);this.view.message('Сохраняем…');let creating=newPhoto;
    try {
      if(this.gallery){this.item=await api.savePhoto(this.section,this.item?.id,data,file,saved=>{this.item=saved;creating=false;this.view.resetFile();});}
      else {const {slot,id,label}=this.item;const saved=await api.saveBlock(slot.code,data);this.item={...saved,slot,id,label};}
      this.view.render(this.item,{preserveDisclosures:true});this.view.message('Сохранено. Обновите публичную страницу, чтобы увидеть изменения.', 'success');
      this.items=await this.records();this.view.list(this.items);this.view.select(this.item.id);
      if(newPhoto){this.item=null;this.uncertain=false;this.view.select(null);this.view.render();}
    }catch(e){if(creating&&(!e.status||e.status>=500))this.uncertain=true;this.view.message(`Сохранение не завершено: ${e.message}. Часть изменений могла сохраниться. Проверьте запись перед повтором.`, 'error');}
    finally{this.lock(false);}
  }
  async remove() {
    if(!this.gallery||this.busy||!this.item?.id||!this.view.allowDiscard()||!window.confirm('Удалить эту фотографию из галереи?'))return;
    this.lock(true);
    try{await api.removePhoto(this.section,this.item.id);this.item=null;this.view.clear();this.items=await this.records();this.view.list(this.items);this.view.message('Фотография удалена.', 'success');}
    catch(e){this.view.message(`Не удалось подтвердить удаление: ${e.message}. Обновите список.`, 'error');}
    finally{this.lock(false);}
  }
  destroy(){this.view.destroy();}
}
