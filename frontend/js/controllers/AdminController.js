import {AdminSettingsController} from './AdminSettingsController.js?v=20261028.16';
import {AdminContactsController} from './AdminContactsController.js?v=20261027.10';
import {AdminReviewsController} from './AdminReviewsController.js?v=20261028.16';
import { BaseController } from './BaseController.js?v=20261027.10';
import { AuthModel } from '../models/AuthModel.js?v=20261027.10';
import { authApi } from '../api/authApi.js?v=20261027.10';
import { AdminView } from '../views/admin/AdminView.js?v=20261027.10';
import { quoteApi } from '../api/quoteApi.js?v=20261027.10';
import { AdminNotificationView as NotificationView } from '../views/admin/AdminNotificationView.js?v=20261027.10';
import { AdminProductsController } from './AdminProductsController.js?v=20261028.18';
import { API_CONFIG } from '../api/config.js?v=20261027.10';
import { AdminContentController } from './AdminContentController.js?v=20261028.16';
import { AdminColorsController } from './AdminColorsController.js?v=20261028.16';
import { AdminConfigController } from './AdminConfigController.js?v=20261028.16';
import { AdminRequestModel } from '../models/AdminRequestModel.js?v=20261027.10';
import { AdminNavigation } from '../core/AdminNavigation.js?v=20261028.13';

export class AdminController extends BaseController {
  constructor() {
    super();
    this.authModel = new AuthModel();
    this.view = new AdminView('.admin');
    this.events=new AbortController();
    window.addEventListener('beforeunload',e=>{if(this.view.requestDirty()){e.preventDefault();e.returnValue='';}},{signal:this.events.signal});
  }

  async init() {
    await super.init();
    await this.checkAccess();
  }

  async checkAccess() {
    if (this.checkingAccess) return;
    this.checkingAccess = true;
    this.view.showSessionLoading();
    // 1. Проверяем валидность сессии и роль администратора на сервере
    try {
      const user = await this.authModel.checkSession();
      if (!user || user.role !== 'admin') {
        authApi.clearSession();
        window.location.replace('/login/');
        return;
      }

      this.activateDashboard(user);
      this.view.showDashboard();
    } catch (err) {
      console.warn('Ошибка проверки доступа к панели управления:', err);
      this.view.showSessionError('Не удалось проверить вход. Повторите проверку или войдите заново.',
        () => this.checkAccess(), () => authApi.clearSession());
    } finally {
      this.checkingAccess = false;
    }
  }

  /**
   * Активация интерактивных возможностей панели
   */
  activateDashboard(user) {
    this.productsController = new AdminProductsController(this.view.$('#panel-catalog'));
    this.colorsController = new AdminColorsController(this.view.$('#panel-colors'));
    this.configController = new AdminConfigController(this.view.$('#panel-configurator'));
    this.groupsController = new AdminConfigController(this.view.$('#panel-groups'), { sections: [API_CONFIG.CATALOG_V2 ? 'categories' : 'material_groups'], title: 'Разделы каталога', onCatalogChanged: () => this.productsController.refreshGroups() });
    if(API_CONFIG.CATALOG_V2) {
      this.contentController=new AdminContentController(this.view.$('#panel-content'));
      this.settingsController=new AdminSettingsController(this.view.$('#panel-settings'));
      this.contactsController=new AdminContactsController(this.view.$('#panel-contacts'));
      this.reviewsController=new AdminReviewsController(this.view.$('#panel-reviews'));
      this.galleryController=new AdminContentController(this.view.$('#panel-gallery'),true);
      this.view.root.querySelectorAll('[data-next-content]').forEach(el=>el.hidden=false);
    }
    // Reveal invalid inputs in collapsed blocks before native form validation focuses them.
    let validationNoticePending = false;
    this.view.root.addEventListener('invalid', event => {
      let block = event.target.closest('details');
      while (block) { block.open = true; block = block.parentElement.closest('details'); }
      if (!validationNoticePending) {
        validationNoticePending = true;
        NotificationView.show({ type: 'warning', title: 'Проверьте форму', message: event.target.validationMessage || 'Заполните обязательные поля и проверьте формат значений.' });
        queueMicrotask(() => { validationNoticePending = false; });
      }
    }, true);
    this.view.showUnavailablePanels();
    this.view.setAdminUser(user);
    this.view.$('[data-requests-refresh]')?.addEventListener('click', () => this.loadRequests());
    this.requestOffset = 0;
    const controls=document.createElement('form');
    controls.className='config-admin-toolbar';
    controls.innerHTML='<label class="field">Поиск заявки<input class="field__input" name="search" placeholder="Номер, имя, email"></label><button class="btn" type="submit">Найти</button><button class="btn" type="button" data-page-prev>Назад</button><button class="btn" type="button" data-page-next>Далее</button><span data-page-status></span>';
    this.view.$('#admin-requests-list').before(controls);this.requestControls=controls;
    const filtersBlock = document.createElement('details');
    filtersBlock.className = 'admin-disclosure';
    const filtersTitle = document.createElement('summary');
    filtersTitle.textContent = 'Поиск и фильтры заявок';
    controls.before(filtersBlock);
    filtersBlock.append(filtersTitle, controls);
    controls.querySelector('[name=search]').closest('label').insertAdjacentHTML('afterend',`<label class="field">Вид заказа<select class="field__input" name="configurator_type"><option value="">Все</option><option value="rope_with_splice">Канат</option><option value="loop_only">Петли на своём канате</option><option value="splice_only">Сращивание и обработка</option></select></label><label class="field">Срочность<select class="field__input" name="is_urgent"><option value="">Все</option><option value="true">Срочные</option><option value="false">Обычные</option></select></label><label class="field">Сортировка<select class="field__input" name="sort_by"><option value="created_at">Дата создания</option><option value="updated_at">Дата изменения</option><option value="total_price">Сумма</option><option value="request_number">Номер заявки</option></select></label><label class="field">Порядок<select class="field__input" name="sort_order"><option value="desc">По убыванию</option><option value="asc">По возрастанию</option></select></label>`);
    controls.addEventListener('submit',e=>{e.preventDefault();this.loadRequests(false,0);});
    controls.querySelector('[data-page-prev]').addEventListener('click',()=>this.loadRequests(false,Math.max(0,this.requestOffset-50)));
    controls.querySelector('[data-page-next]').addEventListener('click',()=>this.loadRequests(false,this.requestOffset+50));

    // Инициализируем табы сайдбара
    this.navigation = new AdminNavigation(this);
    this.view.initTabs(tabName => this.navigation.go(this.navigation.routeFor(tabName)));
    this.navigation.start();

    // Навешиваем обработчик выхода из системы
    if (this.view.logoutBtn) {
      this.view.logoutBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        try { await this.authModel.logout(); }
        catch (err) { console.warn('Не удалось завершить сессию на сервере:', err); }
        finally { window.location.replace('/login/'); }
      });
    }

    // Подгружаем заявки
  }

  async handleTabChange(tabName) {
    if (tabName === 'groups' && !this.groupsController.ready) await this.groupsController.load();
    if (tabName === 'configurator' && !this.configController.ready) await this.configController.load();
    if (tabName === 'colors' && !this.colorsController.ready) await this.colorsController.load();
    if (tabName === 'catalog' && !this.productsController.ready) await this.productsController.load();
    if (tabName === 'requests') {
      await this.loadRequests();
    }
  }

  destroy() {
    this.navigation?.destroy();
    this.events.abort();
    this.productsController?.destroy();
    this.colorsController?.destroy();
    this.configController?.destroy();
    this.groupsController?.destroy();
    this.contentController?.destroy();
    this.galleryController?.destroy();
    this.reviewsController?.destroy();
    this.contactsController?.destroy();
    this.settingsController?.destroy();
    super.destroy();
  }

  async loadRequests(force=false,offset=this.requestOffset) {
    if (this.loadingRequests) return;
    if(this.view.requestBusy&&!force)return;
    if(!this.view.allowRequestDiscard())return;
    this.requestOffset=offset;
    this.loadingRequests = true;
    this.view.showRequestsStatus('Загружаем заявки…');
    try {
      const filters=Object.fromEntries(new FormData(this.requestControls));
      const requests = await quoteApi.listQuoteRequests({...filters,skip:this.requestOffset,limit:50});
      if (!Array.isArray(requests)) throw new Error('Некорректный ответ сервера');
      this.requestControls.querySelector('[data-page-prev]').disabled=this.requestOffset===0;
      this.requestControls.querySelector('[data-page-next]').disabled=requests.length<50;
      this.requestControls.querySelector('[data-page-status]').textContent=`Страница ${this.requestOffset/50+1}`;
      this.view.renderQuoteRequests(requests, id => quoteApi.getQuoteRequest(id), {
        update:async(request,values)=>{
          const data=AdminRequestModel.payload(values,request);
          if(!Object.keys(data).length)return request;
          const saved=await quoteApi.update(request.id,data);
          NotificationView.success('Заявка сохранена',saved.request_number);
          return saved;
        },
        remove:async id=>{await quoteApi.remove(id);NotificationView.success('Заявка удалена');},
        reload:()=>this.loadRequests(true),
      });
    } catch (err) {
      this.view.showRequestsStatus(`Не удалось загрузить заявки. ${err.message}. Нажмите «Обновить».`, 'error');
    } finally {
      this.loadingRequests = false;
    }
  }
}
