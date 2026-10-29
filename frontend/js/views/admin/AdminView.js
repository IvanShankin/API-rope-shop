import { BaseView } from '../BaseView.js?v=20261027.10';
import { escapeHtml } from '../../utils/text.js?v=20261027.10';
import { AdminNotificationView } from './AdminNotificationView.js?v=20261027.10';

/**
 * Представление админ-панели (Dashboard View).
 * Инициализируется только на странице admin.html при подтвержденной сессии.
 */
export class AdminView extends BaseView {
  constructor(rootSelector = '.admin') {
    super(rootSelector);
    this.tabs = this.root ? this.root.querySelectorAll('.sidebar__tab') : [];
    this.panels = this.root ? this.root.querySelectorAll('.panel') : [];
    this.savebar = this.root ? this.root.querySelector('.savebar') : null;
    this.logoutBtn = this.root ? this.root.querySelector('.sidebar__logout') : null;
    this.userNameEl = this.root ? this.root.querySelector('.sidebar__user-name') : null;
  }

  /**
   * Установка имени текущего администратора в шапке сайдбара
   */
  setAdminUser(user) {
    if (this.userNameEl && user) {
      this.userNameEl.textContent = user.username || user.email || 'Администратор';
    }
  }

  showDashboard() {
    document.querySelector('.admin-session').hidden = true;
    this.root.hidden = false;
  }

  showSessionLoading() {
    this.root.hidden = true;
    const gate = document.querySelector('.admin-session');
    gate.hidden = false;
    const status = document.createElement('p');
    status.setAttribute('role', 'status');
    status.textContent = 'Проверяем вход…';
    gate.querySelector('.admin-session__card').replaceChildren(status);
  }

  showSessionError(message, onRetry, onLogin) {
    // Do not display an unverified dashboard, but retain credentials for a retry.
    const error = document.createElement('p');
    error.setAttribute('role', 'alert');
    error.textContent = message;
    const retry = document.createElement('button');
    retry.type = 'button';
    retry.className = 'btn';
    retry.textContent = 'Повторить проверку';
    retry.addEventListener('click', onRetry);
    const login = document.createElement('a');
    login.href = '/login/';
    login.className = 'btn';
    login.textContent = 'Войти заново';
    login.addEventListener('click', onLogin);
    const actions = document.createElement('div');
    actions.className = 'admin-session__actions';
    actions.append(retry, login);
    this.root.hidden = true;
    const gate = document.querySelector('.admin-session');
    gate.hidden = false;
    gate.querySelector('.admin-session__card').replaceChildren(error, actions);
  }

  showUnavailablePanels() {
    for (const name of ['home','business','private','charity','reviews','contacts']) {
      const panel = this.$(`#panel-${name}`);
      if (!panel || (['reviews','contacts'].includes(name) && panel.querySelector('[data-content-editor]'))) continue;
      panel.removeAttribute('data-savable');
      const title = panel.querySelector('h1')?.textContent || 'Контент сайта';
      panel.innerHTML = `<header class="panel__head"><h1 class="panel__title">${escapeHtml(title)}</h1></header><p>Редактирование этого раздела пока недоступно: сервер не предоставляет сохранение этих данных. Текущие страницы сайта сохранены.</p><p>Каталог, цвета, конфигуратор и заявки доступны в меню слева.</p>`;
    }
    if (this.savebar) this.savebar.hidden = true;
  }

  /**
   * Инициализация переключения вкладок в сайдбаре
   */
  initTabs(onTabChange) {
    this.tabs = this.root.querySelectorAll('.sidebar__tab');
    this.panels = this.root.querySelectorAll('.panel');
    this.tabs.forEach(tab => tab.addEventListener('click', () => onTabChange(tab.dataset.panel)));
  }
  showPanel(name) {
    this.tabs.forEach(tab => {
      tab.classList.toggle('sidebar__tab--active', tab.dataset.panel === name);
      if (tab.dataset.panel === name) tab.setAttribute('aria-current', 'page');
      else tab.removeAttribute('aria-current');
    });
    this.panels.forEach(panel => { panel.hidden = panel.id !== `panel-${name}`; });
    if (this.savebar) this.savebar.hidden = true;
  }
  /**
   * Отрисовка таблицы заявок из бэкенда
   */
  requestValues(){const form=this.root.querySelector('[data-request-edit]');return form?Object.fromEntries([...form.elements].filter(e=>e.name).map(e=>[e.name,e.type==='checkbox'?e.checked:e.value])):{};}
  requestDirty(){return Boolean(this.requestBaseline&&JSON.stringify(this.requestValues())!==this.requestBaseline);}
  allowRequestDiscard(){return !this.requestDirty()||window.confirm('Отбросить несохранённые изменения заявки?');}

  renderQuoteRequests(requests, onDetail, actions = {}) {
    this.openRequest = null;
    const tableContainer = this.root ? this.root.querySelector('#admin-requests-list') : null;
    if (!tableContainer) return;
    this.requestBaseline='';this.requestId=null;this.detailSelection=Symbol();
    requests = requests.map((request) => ({
      ...Object.fromEntries(Object.entries(request).map(([key, value]) => [key, escapeHtml(value)])),
      id: Number(request.id),
    }));

    if (!requests || requests.length === 0) {
      tableContainer.innerHTML = '<p style="padding: 24px; color: #888;">Заявок пока нет</p>';
      return;
    }

    tableContainer.innerHTML = `
      <table class="admin-table" style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr style="border-bottom: 2px solid #233446; text-align: left;">
            <th style="padding: 10px;">№ Заявки</th>
            <th style="padding: 10px;">Клиент</th>
            <th style="padding: 10px;">Контакты</th>
            <th style="padding: 10px;">Сумма</th>
          </tr>
        </thead>
        <tbody>
          ${requests.map((req) => `
            <tr style="border-bottom: 1px solid #1E2D3D;">
              <td data-label="Заявка" style="padding: 10px; font-weight: 600;"><button type="button" class="btn" data-request-detail="${req.id}">${req.request_number}</button></td>
              <td data-label="Клиент" style="padding: 10px;">${req.name}</td>
              <td data-label="Контакты" style="padding: 10px;">${req.email}<br><small style="color: #888;">${req.phone || ''}</small></td>
              <td data-label="Сумма" style="padding: 10px; font-weight: 600;">${req.total_price} ${req.currency || 'EUR'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    this.openRequest = async (id) => {
      if(this.requestBusy||!this.allowRequestDiscard())return;
      this.requestBaseline='';
      const selection = this.detailSelection = Symbol();
      let detail = tableContainer.querySelector('[data-request-content]');
      if (!detail) { detail=document.createElement('section'); detail.dataset.requestContent='';tableContainer.append(detail); }
      detail.setAttribute('role','status');detail.textContent='Загружаем состав заявки…';
      let request;
      try { request = await onDetail(Number(id)); }
      catch(error) { if(this.detailSelection===selection) AdminNotificationView.message(detail, `Не удалось загрузить заявку: ${error.message}. Нажмите её номер повторно.`, 'error'); return; }
      if(this.detailSelection!==selection || !detail.isConnected) return;
      const e=escapeHtml;
      const ropes=(request.rope_items||[]).map(item=>`<li>${e(item.product_name_snapshot)} · ${e(item.color_name_snapshot)} · ${e(item.diameter_mm)} мм · ${e(item.length_m)} м × ${e(item.quantity)} шт.<br>A: ${e(item.end_a_name_snapshot||'Без обработки')}, петля ${e(item.end_a_eye_size_cm??'—')} см; B: ${e(item.end_b_name_snapshot||'Без обработки')}, петля ${e(item.end_b_eye_size_cm??'—')} см.</li>`).join('');
      const services=(request.service_items||[]).map(item=>`<li>${e(item.service_name_snapshot)} · ${e(item.material_name_snapshot)} · ${e(item.diameter_mm)} мм × ${e(item.quantity)}; петля ${e(item.eye_size_cm??'—')} см. ${e(item.total_cost)} ${e(request.currency)}</li>`).join('');
      const extras=(request.extra_items||[]).map(item=>`<li>${e(item.name_snapshot)} × ${e(item.quantity)}: ${e(item.total_cost)} ${e(request.currency)}</li>`).join('');
      detail.className = 'admin-card admin-request-card';
      detail.innerHTML=`<h2>${e(request.request_number)}</h2><p>${e(request.name)} · ${e(request.email)} · ${e(request.phone||'')}</p><p>${request.is_urgent?'Срочное изготовление':'Обычное изготовление'} · ${e(request.created_at)}</p><ul>${ropes}${services}${extras}</ul><p style="white-space:pre-wrap">${e(request.comment||'Без комментария')}</p><p>Итого: ${e(request.total_price)} ${e(request.currency)}</p>`;
      if(actions.update){
        detail.insertAdjacentHTML('beforeend',`<h3>Редактировать заявку</h3><p>Изменение срочности и итоговой суммы — ручная корректировка. Сервер не пересчитывает состав заказа при таком сохранении.</p><form data-request-edit class="product-editor admin-card"><div class="admin-fields" style="padding: 0;"><label class="field">Имя<input class="field__input" name="name" required maxlength="255" value="${e(request.name)}"></label><label class="field">Email<input class="field__input" name="email" type="email" required value="${e(request.email)}"></label><label class="field">Телефон<input class="field__input" name="phone" maxlength="100" value="${e(request.phone||'')}"></label><label class="field">Итоговая сумма, ${e(request.currency)}<input class="field__input" name="total_price" type="number" min="0" step="0.01" required value="${e(request.total_price)}"></label><label class="field" style="grid-column: 1 / -1;">Комментарий<textarea class="field__input" name="comment">${e(request.comment||'')}</textarea></label></div><label class="admin-toggle"><input type="checkbox" name="is_urgent" ${request.is_urgent?'checked':''}> <span>Срочный заказ</span></label><div class="admin-form-actions"><button class="btn btn--primary" type="submit">Сохранить заявку</button><button class="btn btn--ghost" type="button" data-request-cancel>Отменить изменения</button><button class="btn btn--danger" type="button" data-request-remove>Удалить заявку</button></div></form><p role="status" data-request-edit-status></p>`);
        const form=detail.querySelector('form');const message=(text,type='info')=>{AdminNotificationView.message(detail.querySelector('[data-request-edit-status]'),text,type);};
        const lock=value=>{this.requestBusy=value;detail.querySelectorAll('input,select,textarea,button').forEach(el=>el.disabled=value);tableContainer.querySelectorAll('[data-request-detail]').forEach(el=>el.disabled=value);};
        this.requestBaseline=JSON.stringify(this.requestValues());
        form.addEventListener('submit',async event=>{
          event.preventDefault();if(this.requestBusy||!form.reportValidity())return;
          const values=this.requestValues();lock(true);message('Сохраняем…');
          try{request=await actions.update(request,values);this.requestBaseline='';await actions.reload();}
          catch(error){message(`Не удалось подтвердить сохранение: ${error.message}. При потере связи обновите заявку перед повтором.`, 'error');}
          finally{lock(false);}
        });
        detail.querySelector('[data-request-cancel]').addEventListener('click',()=>{if(this.allowRequestDiscard()){form.reset();this.requestBaseline=JSON.stringify(this.requestValues());message('Изменения отменены.', 'notice');}});
        detail.querySelector('[data-request-remove]').addEventListener('click',async()=>{
          if(this.requestBusy||!window.confirm(`Удалить заявку ${request.request_number} вместе с её составом? Это действие нельзя отменить.`))return;
          lock(true);message('Удаляем…');
          try{await actions.remove(request.id);this.requestBaseline='';await actions.reload();}
          catch(error){message(`Не удалось подтвердить удаление: ${error.message}. Обновите список перед повтором.`, 'error');}
          finally{lock(false);}
        });
      }
      this.requestId = Number(id);
      this.root.dispatchEvent(new CustomEvent('admin:request-open'));
      detail.scrollIntoView({behavior:'auto',block:'start'});
    };
    tableContainer.querySelectorAll('[data-request-detail]').forEach(button => button.addEventListener('click', () => this.openRequest(button.dataset.requestDetail)));

  }

  showRequestsStatus(message, type = 'info') {
    this.requestBaseline='';this.requestId=null;this.detailSelection=Symbol();
    const container = this.$('#admin-requests-list');
    AdminNotificationView.message(container, message, type);
  }
}
