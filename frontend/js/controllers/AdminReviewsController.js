import {reviewsApi as api} from '../api/reviewsApi.js?v=20261027.10';
import {AdminReviewsView} from '../views/admin/AdminReviewsView.js?v=20261028.16';
export class AdminReviewsController {
  constructor(root){
    this.view=new AdminReviewsView(root);this.section='all';this.ready=false;this.busy=false;this.item=null;
    this.view.bind({load:()=>this.load(),select:id=>this.select(id),save:()=>this.save(),remove:()=>this.remove(),create:()=>{
      if(!this.ready||this.busy||!this.view.allowDiscard())return;
      this.item=null;this.uncertain=false;this.view.select(null);this.view.render();this.view.message('Заполните автора и хотя бы один текст.');
    }});
  }
  lock(value){this.busy=value;this.view.busy(value);}
  async load(){
    if(this.busy||!this.view.allowDiscard())return;
    this.lock(true);this.view.message('Загружаем…');
    try{this.items=(await api.list('rus',true)).items;this.ready=true;this.item=null;this.uncertain=false;this.view.clear();this.view.list(this.items);this.view.message(this.items.length?'Выберите отзыв.':'Отзывов пока нет.');}
    catch(e){this.view.message(`Не удалось загрузить отзывы: ${e.message}. Нажмите «Обновить».`, 'error');}finally{this.lock(false);}
  }
  async select(id){
    if(this.busy||!this.ready)return;
    if(!this.view.allowDiscard()){this.view.select(this.item?.id);return;}
    if(!id){this.item=null;this.view.clear();return;}
    this.lock(true);
    try{this.item=await api.get(id);this.uncertain=false;this.view.render(this.item);this.view.message('Измените поля и сохраните.');}
    catch(e){this.view.select(this.item?.id);this.view.message(e.message, 'error');}finally{this.lock(false);}
  }
  async save(){
    if(this.busy)return;
    if(this.uncertain){this.view.message('Ответ на создание не получен. Обновите список и проверьте отзыв перед повтором.', 'warning');return;}
    const v=this.view.values();const data={author_name:v.author_name.trim(),rating:v.rating?Number(v.rating):null,status:v.status,is_published:v.is_published,index:Number(v.index),translations:['rus','eng','ger'].map(locale=>({locale,text:v[`text_${locale}`].trim()}))};
    if(!data.author_name||!data.translations.some(t=>t.text)||!Number.isSafeInteger(data.index)||data.index<0){this.view.message('Укажите автора, хотя бы один текст и целый неотрицательный порядок.', 'warning');return;}
    const newReview=!this.item?.id;
    this.lock(true);this.view.message('Сохраняем…');let creating=newReview;
    try{
      this.item=await api.save(this.item?.id,data,created=>{this.item=created;creating=false;});
      this.view.render(this.item,{preserveDisclosures:true});this.items=(await api.list('rus',true)).items;this.view.list(this.items);this.view.select(this.item.id);
      this.view.message('Сохранено. Обновите главную страницу, чтобы увидеть изменения.', 'success');
      if(newReview){this.item=null;this.uncertain=false;this.view.select(null);this.view.render();}
    }catch(e){if(creating&&(!e.status||e.status>=500))this.uncertain=true;this.view.message(`Сохранение не завершено: ${e.message}. Часть данных могла сохраниться; введённые поля сохранены в форме.`, 'error');}finally{this.lock(false);}
  }
  async remove(){
    if(this.busy||!this.item?.id||!this.view.allowDiscard()||!window.confirm('Удалить отзыв и все его переводы?'))return;
    this.lock(true);
    try{await api.remove(this.item.id);this.item=null;this.view.clear();this.items=(await api.list('rus',true)).items;this.view.list(this.items);this.view.message('Отзыв удалён.', 'success');}
    catch(e){this.view.message(`Удаление не подтверждено: ${e.message}. Обновите список.`, 'error');}finally{this.lock(false);}
  }
  destroy(){this.view.destroy();}
}
