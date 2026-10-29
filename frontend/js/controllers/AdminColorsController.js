import { adminColorsApi as api } from '../api/adminColorsApi.js?v=20261027.10';
import { AdminColorModel } from '../models/AdminColorModel.js?v=20261027.10';
import { AdminColorsView } from '../views/admin/AdminColorsView.js?v=20261028.16';
import { automaticConfigCode } from '../models/AdminConfigModel.js?v=20261028.8';
export class AdminColorsController {
  constructor(root) {
    this.view = new AdminColorsView(root); this.color = null; this.ready = false; this.busy = false;
    this.view.bind({ select: id => this.select(id), refresh: () => this.load(), save: () => this.save(), create: () => {
      if (this.busy || !this.ready || !this.view.allowDiscard()) return;
      this.color = null; this.view.selection(null); this.view.render(); this.view.message('Создайте цвет и затем назначьте его канатам в «Каталоге».');
    }, remove: () => this.remove(), removeTranslation:id=>this.removeTranslation(id) });
  }
  destroy() { this.view.destroy(); }
  lock(value) { this.busy = value; this.view.busy(value); }
  async load() {
    if (this.busy || !this.view.allowDiscard()) return;
    this.lock(true);
    try { this.colors = await api.list({refresh:true}); this.view.list(this.colors); this.view.clear(); this.color = null; this.ready = true; this.view.message('Выберите цвет или добавьте новый.'); }
    catch (e) { this.view.message(`Не удалось загрузить цвета: ${e.message}`, 'error'); }
    finally { this.lock(false); }
  }
  async select(id) {
    if (this.busy) return;
    if (!this.view.allowDiscard()) { this.view.selection(this.color?.id); return; }
    if (!id) { this.color = null; this.view.clear(); return; }
    this.lock(true);
    try { this.color = await api.detail(id); this.view.render(this.color); this.view.message('Изменения цвета действуют для всех связанных канатов.'); }
    catch (e) { this.view.selection(this.color?.id); this.view.message(e.message, 'error'); }
    finally { this.lock(false); }
  }
  async save() {
    if (this.busy) return;
    let data;
    let index;
    try { const values = this.view.values();
      values.code = this.color ? this.color.code : automaticConfigCode('colors', {name_eng:values.eng, name_ger:values.ger, name_rus:values.rus}, this.colors);
      data = AdminColorModel.payload(values); index=AdminColorModel.index(values);
      if(this.color?.translations.some(t=>!data.translations.some(next=>next.locale===t.locale)))throw new Error('Пустое поле не удаляет перевод. Верните название перед сохранением.');
    } catch (e) { this.view.message(e.message, 'error'); return; }
    const creating = !this.color;
    this.lock(true);
    try {
      const { translations, ...fields } = data;
      if (!this.color) {
        this.color = await api.create({ ...fields, index, translations });
      } else {
        // Refresh translations before a retry after a partially successful save.
        this.color = await api.detail(this.color.id);
        await api.update(this.color.id, fields);
        if(Number(this.color.index)!==index)await api.order(this.color.id,index);
        for (const translation of translations) {
          const existing = this.color.translations.find(t => t.locale === translation.locale);
          if (existing) { if (existing.name !== translation.name) await api.updateTranslation(existing.id, { name: translation.name }); }
          else await api.addTranslation(this.color.id, translation);
        }
      }
      this.colors = await api.list(); this.color = await api.detail(this.color.id);
      this.view.list(this.colors); this.view.selection(this.color.id); this.view.render(this.color,{preserveDisclosures:true});
      this.view.message('Цвет сохранён. В каталоге откройте канат, чтобы назначить ему этот цвет.', 'success');
      if (creating) { this.color = null; this.view.selection(null); this.view.render(); }
    } catch (e) { this.view.message(`Сохранение не завершено: ${e.message}. Часть изменений могла сохраниться; значения формы оставлены для проверки и повтора.`, 'error'); }
    finally { this.lock(false); }
  }
  async remove(){
    if(this.busy||!this.color||!this.view.allowDiscard()||!window.confirm(`Удалить цвет #${this.color.id}? Это действие нельзя отменить. Если он используется, можно отключить его.`))return;
    this.lock(true);let committed=false;
    try{await api.remove(this.color.id);committed=true;this.color=null;this.view.clear();this.colors=await api.list();this.view.list(this.colors);this.view.message('Цвет удалён.', 'success');}
    catch(e){this.view.message(`${committed?'Удалено, но не удалось обновить список.':'Не удалось подтвердить удаление.'} ${e.message}. Обновите список перед повтором.`, 'error');}
    finally{this.lock(false);}
  }
  async removeTranslation(id){
    const translation=this.color?.translations?.find(t=>Number(t.id)===Number(id));
    if(this.busy||!translation||this.color.translations.length<=1||!this.view.allowDiscard()||!window.confirm(`Удалить перевод цвета ${translation.locale.toUpperCase()}? Это действие нельзя отменить.`))return;
    this.lock(true);let committed=false;
    try{await api.removeTranslation(id);committed=true;this.color=await api.detail(this.color.id);this.colors=await api.list();this.view.list(this.colors);this.view.selection(this.color.id);this.view.render(this.color,{preserveDisclosures:true});this.view.message('Перевод удалён. Последний перевод цвета сохраняется.', 'success');}
    catch(e){this.view.message(`${committed?'Перевод удалён, но не удалось обновить форму.':'Не удалось подтвердить удаление перевода.'} ${e.message}. Обновите цвет перед повтором.`, 'error');}
    finally{this.lock(false);}
  }
}
