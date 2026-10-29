import { adminProductsApi as api } from '../api/adminProductsApi.js?v=20261027.10';
import { AdminProductsView } from '../views/admin/AdminProductsView.js?v=20261028.18';
import { AdminProductModel } from '../models/AdminProductModel.js?v=20261027.10';
import { adminColorsApi as colorsApi } from '../api/adminColorsApi.js?v=20261027.10';
import { AdminColorModel } from '../models/AdminColorModel.js?v=20261027.10';
import { API_CONFIG } from '../api/config.js?v=20261027.10';
import { adminConfigApi as spliceApi } from '../api/adminConfigApi.js?v=20261027.10';

export class AdminProductsController {
  constructor(root) {
    this.root = root;
    this.view = new AdminProductsView(root);
    this.busy = false;
    this.ready = false;
    this.product = null;
    this.view.bind({
      refresh: () => this.load(), select: id => this.select(id), save: () => this.save(), create: async () => {
        if (!this.ready || this.busy || !this.view.allowDiscard()) return;
        this.lock(true);
        try {
          await this.refreshReferences();
          this.product = null;
          this.uncertain = false;
          this.view.spliceLinks = [];
          this.view.setSelection(null);
          this.view.renderProduct(null, this.groups, this.materials);
          this.view.message('Заполните данные нового каната.');
          this.root.dispatchEvent(new CustomEvent('admin:product-new', { bubbles:true }));
        } catch (error) { this.view.message(`Не удалось обновить справочники: ${error.message}`, 'error'); }
        finally { this.lock(false); }
      }, remove: id => this.remove(id), image: (action, id, file) => this.image(action, id, file)
    });
  }
  destroy() { this.view.destroy(); }
  async refreshReferences() {
    const [groups, materials, colors, categories, splices] = await Promise.all([api.groups(), api.materials(), colorsApi.list({refresh:true}), API_CONFIG.CATALOG_V2 ? api.categories() : [], spliceApi.list('splice_types',{locale:'rus'})]);
    if (![groups, materials, colors, categories, splices].every(Array.isArray)) throw new Error('Некорректные справочники');
    this.groups = groups; this.materials = materials; this.view.colors = colors;
    if (API_CONFIG.CATALOG_V2) this.view.categories = categories;
    this.view.spliceTypes = splices;
  }
  async refreshGroups() {
    if (API_CONFIG.CATALOG_V2) {
      this.view.categories = await api.categories();
      const select = this.root.querySelector('[name=category_id]');
      if (select) { const value = select.value; select.replaceChildren(new Option('Выберите категорию', ''), ...this.view.categories.map(c => new Option(c.name || c.slug, String(c.id)))); select.value = value; }
    }
    const groups = await api.groups();
    if (!Array.isArray(groups)) throw new Error('Не удалось загрузить разделы');
    this.groups = groups;
    const select = this.root.querySelector('[name=material_group_id]');
    if (select) {
      const selected = select.value;
      select.replaceChildren(new Option('Выберите раздел', ''), ...groups.map(group =>
        new Option(group.name || group.code || `#${group.id}`, String(group.id))));
      select.value = selected;
    }
  }
  lock(value) {
    this.busy = value;
    this.view.setBusy(value);
  }
  async load() {
    if (this.busy || !this.view.allowDiscard()) return;
    this.lock(true);
    this.view.message('Загружаем каталог…');
    try {
      const [products, groups, materials, colors, categories, splices] = await Promise.all([api.list(), api.groups(), api.materials(), colorsApi.list({refresh:true}), API_CONFIG.CATALOG_V2 ? api.categories() : [], spliceApi.list('splice_types',{locale:'rus'})]);
      if(!Array.isArray(splices))throw new Error('Некорректный список заделок');
      this.view.spliceTypes = splices;this.view.spliceLinks = [];
      if (![products, groups, materials, colors].every(Array.isArray)) throw new Error('Некорректные справочники');
      this.view.colors = colors;
      if (API_CONFIG.CATALOG_V2) this.view.categories = categories;
      this.groups = groups;
      this.materials = materials;
      this.ready = true;
      this.product = null;
      this.uncertain = false;
      this.view.renderList(products);
      this.view.clear();
      this.view.message(products.length ? 'Выберите канат или добавьте новый.' : 'Канатов пока нет. Добавьте первый.');
    } catch (error) { this.view.message(`Ошибка загрузки: ${error.message}. Нажмите «Обновить».`, 'error'); }
    finally { this.lock(false); }
  }
  async select(id) {
    if (!this.ready || this.busy) return;
    if (!this.view.allowDiscard()) { this.view.setSelection(this.product?.product_id); return; }
    if (!id) { this.product = null; this.view.clear(); return; }
    this.lock(true);
    try {
      const [product, links] = await Promise.all([api.detail(id), spliceApi.links(id), this.refreshReferences()]);
      if(!Array.isArray(links))throw new Error('Не удалось получить заделки каната');
      this.view.spliceLinks = links;
      this.product = product;
      this.uncertain = false;
      this.view.renderProduct(this.product, this.groups, this.materials);
      this.view.message('Измените нужные поля и нажмите общую кнопку «Сохранить изменения».');
    } catch (error) {
      this.view.setSelection(this.product?.product_id);
      this.view.message(`Не удалось открыть канат: ${error.message}`, 'error');
    }
    finally { this.lock(false); }
  }
  async save() {
    if (this.busy) return;
    if (this.uncertain) { this.view.message('Ответ на создание не получен. Обновите список и проверьте запись перед повторным сохранением.', 'warning'); return; }
    const forms = [...this.root.querySelectorAll('[data-product-editor] form')];
    const colorsForm = forms.find(form => form.matches('[data-product-colors-form]'));
    const selected = colorsForm ? Object.entries(this.view.readForm(colorsForm))
      .filter(([key, value]) => key.startsWith('color_') && value).map(([key]) => Number(key.slice(6))) : [];
    const plans = [];
    try {
      for (const form of forms) {
        const values = this.view.readForm(form);
        const key = this.view.formKey(form);
        const isProduct = form.matches('[data-product-form]');
        if (JSON.stringify(values) === this.view.baselines.get(key) && !(isProduct && !this.product)) continue;
        if (form.matches('[data-color-order-form]')) {
          const link = this.product?.colors?.find(item => Number(item.id) === Number(form.dataset.linkId));
          if (link && !selected.includes(Number(link.color_id))) continue;
        }
        if (!form.checkValidity()) {
          for (let parent = form.closest('details'); parent; parent = parent.parentElement?.closest('details')) parent.open = true;
          form.reportValidity();
          this.view.message('Проверьте заполнение полей. Изменения пока не сохранены.', 'warning');
          return;
        }
        if (isProduct) plans.push({ form, type: 'product', payload: API_CONFIG.CATALOG_V2 ? AdminProductModel.catalogProduct(values) : AdminProductModel.product(values) });
        else if (form.matches('[data-variant-form]')) plans.push({ form, type: 'variant', payload: API_CONFIG.CATALOG_V2 ? AdminProductModel.catalogVariant(values) : AdminProductModel.variant(values), index: form.dataset.id ? AdminProductModel.index(values) : undefined });
        else if (form.matches('[data-color-order-form]')) plans.push({ form, type: 'order', index: AdminProductModel.index(values) });
        else if (form === colorsForm) plans.push({ form, type: 'colors' });
        else if (form.matches('[data-product-splices-form]')) plans.push({form,type:'splices',ids:Object.entries(values).filter(([key,value])=>key.startsWith('splice_')&&value).map(([key])=>Number(key.slice(7)))});
      }
    } catch (error) { this.view.message(error.message, 'error'); return; }
    if (!plans.length) { this.view.message('Нет изменений для сохранения.', 'notice'); return; }
    const newProduct = !this.product;
    const newVariant = plans.some(plan => plan.type === 'variant' && !plan.form.dataset.id);
    this.lock(true);
    this.view.message('Сохраняем все изменения…');
    let creating = false;
    try {
      // Preserve each successful step so a retry does not create duplicate records.
      for (const plan of plans) {
        if (plan.type === 'product') {
          creating = !this.product;
          const saved = await api.saveProduct(this.product?.product_id, plan.payload, saved => { this.product = saved; creating = false; });
          this.product = saved;
          creating = false;
        } else if (plan.type === 'variant') {
          creating = !plan.form.dataset.id;
          const saved = await api.saveVariant(this.product.product_id, plan.form.dataset.id, plan.payload);
          plan.form.dataset.id = saved.id;
          creating = false;
          if (plan.index !== undefined && Number(saved.index) !== plan.index) await api.orderVariant(saved.id, plan.index);
        } else if (plan.type === 'order') {
          await colorsApi.orderLink(plan.form.dataset.linkId, plan.index);
        } else if(plan.type === 'splices') {
          const savedLinks=await spliceApi.saveLinks(this.product.product_id,plan.ids);
          if(!Array.isArray(savedLinks))throw new Error('Сервер не подтвердил список заделок');
          this.view.spliceLinks=savedLinks;
        } else {
          const links = await colorsApi.links(this.product.product_id);
          const changes = AdminColorModel.linkChanges(links, selected);
          for (const colorId of changes.add) await colorsApi.attach(this.product.product_id, colorId);
          for (const id of changes.remove) await colorsApi.detach(id);
        }
        this.view.markSaved(plan.form, plan.form.dataset.id);
      }
      const id = this.product.product_id;
      const [products, detail] = await Promise.all([api.list(), api.detail(id)]);
      this.product = detail;
      this.view.renderList(products);
      this.view.setSelection(id);
      this.view.renderProduct(detail, this.groups, this.materials);
      this.view.message('Все изменения сохранены.', 'success');
      if (!newProduct && newVariant) {
        const container = this.root.querySelector('[data-variants-container]');
        container.insertAdjacentHTML('beforeend', this.view.variantRow(null, container.querySelectorAll('[data-variant-form]').length));
        const form = container.lastElementChild;
        this.view.baselines.set(this.view.formKey(form), JSON.stringify(this.view.readForm(form)));
        this.view.message('Диаметр сохранён. Можно добавить следующий.', 'success');
      }
      if (newProduct) {
        this.product = null; this.uncertain = false; this.view.spliceLinks = [];
        this.view.setSelection(null); this.view.renderProduct(null, this.groups, this.materials);
        this.view.message('Канат сохранён. Можно добавить следующий; для фотографий и диаметров выберите сохранённый канат в списке.', 'success');
      }
    } catch (error) {
      if (creating && (!error.status || error.status >= 500)) this.uncertain = true;
      this.view.message(`Сохранение не завершено: ${error.message}. Часть изменений могла сохраниться. Поля оставлены для проверки и повторного сохранения.`, 'error');
    } finally { this.lock(false); }
  }
  async image(action, id, file) {
    if (this.busy || !this.product || !API_CONFIG.CATALOG_V2) return;
    if (this.view.hasChanges()) { this.view.message('Сначала сохраните изменения в полях, затем измените фотографии.', 'warning'); return; }
    if (action === 'upload' && (!file || file.size > 10 * 1024 * 1024)) { this.view.message('Выберите изображение размером до 10 МБ.', 'warning'); return; }
    if (action === 'remove' && !window.confirm('Удалить фотографию товара?')) return;
    this.lock(true);
    try {
      if (action === 'upload') await api.upload(this.product.product_id, file);
      else if (action === 'main') await api.mainImage(id);
      else if (action === 'remove') await api.removeImage(id);
      this.product = await api.detail(this.product.product_id);
      this.view.renderProduct(this.product, this.groups, this.materials);
      this.root.querySelector('[data-product-photos]').open = true;
      this.view.message('Фотографии сохранены. Обновите каталог, чтобы увидеть результат.', 'success');
    } catch (e) { this.view.message(`Не удалось подтвердить изменение фотографии: ${e.message}. Обновите товар перед повтором.`, 'error'); }
    finally { this.lock(false); }
  }
  async remove(variantId) {
    if (this.busy || !this.product || !this.view.allowDiscard()) return;
    const productId = this.product.product_id;
    if (!window.confirm(variantId ? `Удалить диаметр #${variantId}? Это действие нельзя отменить.` : `Удалить канат #${productId}? Это действие нельзя отменить. Связанные записи могут препятствовать удалению.`)) return;
    this.lock(true); let committed = false;
    try {
      if (variantId) await api.removeVariant(variantId); else await api.removeProduct(productId);
      committed = true;
      if (!variantId) { this.product = null; this.view.clear(); }
      const products = await api.list(); this.view.renderList(products);
      if (variantId) { this.product = await api.detail(productId); this.view.renderProduct(this.product, this.groups, this.materials); this.view.setSelection(productId); }
      this.view.message(variantId ? 'Диаметр удалён.' : 'Канат удалён.', 'success');
    } catch (e) { this.view.message(`${committed ? 'Удалено, но не удалось обновить форму.' : 'Не удалось подтвердить удаление.'} ${e.message}. Обновите список. Для используемых диаметров можно снять флажок «Активен».`, 'error'); }
    finally { this.lock(false); }
  }
}
