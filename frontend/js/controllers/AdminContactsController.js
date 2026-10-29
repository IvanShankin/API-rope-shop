import {contactsApi as api} from '../api/contactsApi.js?v=20261027.10';
import {contactPayload} from '../models/ContactsModel.js?v=20261027.10';
import {AdminContentView} from '../views/admin/AdminContentView.js?v=20261027.10';
import {escapeHtml as esc} from '../utils/text.js?v=20261027.10';
class ContactsView extends AdminContentView {
  constructor(root){
    super(root,{all:'Контакты'},false);
    root.querySelector('h1').textContent='Контакты';
    root.querySelector('header + p').textContent='Реквизиты компании из настроек. Публичное отображение на сайте пока не подключено. Входящие обращения не являются реквизитами компании.';
    root.querySelectorAll('.config-admin-toolbar label').forEach(el=>el.hidden=true);
    this.recordList.root.hidden=true;
  }
  render(item){
    this.root.querySelector('[data-content-editor]').innerHTML=`<form class="contacts-card" data-contacts-form>
      <div class="contacts-card__grid">
        <label class="field">
          <span class="field__label">Название / контактное лицо</span>
          <input class="field__input" name="name" maxlength="255" required value="${esc(item.name||'')}">
        </label>
        <label class="field">
          <span class="field__label">Телефон</span>
          <input class="field__input" name="phone" type="tel" maxlength="100" value="${esc(item.phone||'')}">
          <span class="field__hint">Например, +49 30 123456. Оставьте пустым, чтобы скрыть.</span>
        </label>
        <label class="field">
          <span class="field__label">Email</span>
          <input class="field__input" name="email" type="email" maxlength="255" required value="${esc(item.email||'')}">
        </label>
      </div>
      <div class="contacts-card__actions">
        <button class="btn btn--primary" type="submit">Сохранить</button>
      </div></form>`;this.remember();
  }
}
export class AdminContactsController {
  constructor(root){
    this.view=new ContactsView(root);this.ready=false;this.busy=false;this.section='all';this.view.bind({load:()=>this.load(),select:()=>{},save:()=>this.save()});
    window.addEventListener('company-settings-changed',event=>{if(event.detail!=='contacts')this.ready=false;},{signal:this.view.events.signal});
    this.offset=0;
    root.insertAdjacentHTML('beforeend','<details class="admin-disclosure" data-inquiries><summary>Входящие обращения B2B / B2C</summary><div data-inquiries-list></div><div class="admin-form-actions"><button type="button" class="btn" data-inquiries-prev>Назад</button><button type="button" class="btn" data-inquiries-refresh>Обновить обращения</button><button type="button" class="btn" data-inquiries-next>Далее</button></div><p role="status" data-inquiries-status></p></details>');
    const inbox=root.querySelector('[data-inquiries]');
    inbox.addEventListener('toggle',()=>{if(inbox.open&&!this.inquiriesLoaded)this.loadInquiries(0);},{signal:this.view.events.signal});
    inbox.addEventListener('click',event=>{
      if(event.target.closest('[data-inquiries-refresh]'))this.loadInquiries(this.offset);
      if(event.target.closest('[data-inquiries-prev]'))this.loadInquiries(Math.max(0,this.offset-25));
      if(event.target.closest('[data-inquiries-next]'))this.loadInquiries(this.offset+25);
    },{signal:this.view.events.signal});
  }
  async loadInquiries(offset){
    if(this.inquiriesBusy)return;
    this.inquiriesBusy=true;
    const root=this.view.root.querySelector('[data-inquiries]'),status=root.querySelector('[data-inquiries-status]');
    root.querySelectorAll('button').forEach(button=>button.disabled=true);status.textContent='Загружаем обращения…';
    try{
      const items=await api.listRequests(offset);
      if(!Array.isArray(items))throw Error('Некорректный список обращений');
      root.querySelector('[data-inquiries-list]').innerHTML=items.length?items.map(item=>`<article class="admin-card"><h2>${esc(item.name)}</h2><p>${esc(item.email)} ${esc(item.phone||'')}</p><p style="white-space:pre-wrap;overflow-wrap:anywhere">${esc(item.message||'')}</p></article>`).join(''):'<p>Обращений пока нет.</p>';
      this.offset=offset;this.inquiriesLoaded=true;this.inquiriesHasNext=items.length===25;status.textContent=`Страница ${offset/25+1}`;
    }catch(error){status.textContent=`Не удалось загрузить обращения: ${error.message}. Нажмите «Обновить обращения».`;}
    finally{this.inquiriesBusy=false;root.querySelectorAll('button').forEach(button=>button.disabled=false);root.querySelector('[data-inquiries-prev]').disabled=!this.offset;root.querySelector('[data-inquiries-next]').disabled=!this.inquiriesHasNext;}
  }
  lock(value){this.busy=value;this.view.busy(value);}
  async load(){
    if(this.busy||!this.view.allowDiscard())return;this.lock(true);this.view.message('Загружаем…');
    try{this.contact=await api.getAdmin();this.view.render(this.contact);this.ready=true;this.view.message('Измените реквизиты и сохраните.');}
    catch(e){this.view.message(`Не удалось загрузить контакты: ${e.message}. Нажмите «Обновить».`, 'error');}finally{this.lock(false);}
  }
  async save(){
    if(this.busy||!this.ready)return;let data;
    try{data=contactPayload(this.view.values());}catch(e){this.view.message(e.message, 'error');return;}
    this.lock(true);this.view.message('Сохраняем…');
    try{this.contact=await api.save(data);window.dispatchEvent(new CustomEvent('company-settings-changed',{detail:'contacts'}));this.view.render(this.contact);this.view.message('Реквизиты сохранены в настройках компании. Публичное отображение пока не подключено.', 'success');}
    catch(e){this.view.message(`Сохранение не подтверждено: ${e.message}. Введённые данные сохранены в форме. Можно повторить сохранение.`, 'error');}finally{this.lock(false);}
  }
  async select(){} // Singleton: no record selector or deletion.
  async remove(){}
  destroy(){this.view.destroy();}
}
