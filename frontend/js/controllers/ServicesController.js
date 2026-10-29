import { loadErrorMessage } from '../ui/load-state.js?v=20261027.10';
import { configuratorApi } from '../api/configuratorApi.js?v=20261027.10';
import { quoteApi } from '../api/quoteApi.js?v=20261027.10';
import { ServiceConfiguratorModel } from '../models/ServiceConfiguratorModel.js?v=20261027.10';
import { ServiceConfiguratorView } from '../views/configurator/ServiceConfiguratorView.js?v=20261027.10';

class ServiceController {
  constructor(root) {
    this.model = new ServiceConfiguratorModel(root.dataset.serviceMode === 'loops' ? 'loop_only' : 'splice_only');
    this.view = new ServiceConfiguratorView(root);
    this.view.bind({ change: (name, value) => {
      if (this.busy || this.sent) return;
      this.model.set(name, value); this.view.render(this.model.calculate());
    }, submit: customer => this.submit(customer), retry: () => this.load() });
  }
  async load() {
    if (this.loading || this.busy || this.sent || this.destroyed) return;
    this.loading = true;
    this.view.statusMessage('loading', 'Загружаем материалы, работы и цены…');
    try {
      const refresh = Boolean(this.attempted);
      this.attempted = true;
      const data = await configuratorApi.getData(this.model.type, undefined, { refresh });
      if (this.destroyed) return;
      this.model.init(data);
      if (!this.model.materials.length || !this.model.services.length) {
        this.view.statusMessage('empty', 'Нет доступных материалов или услуг.'); return;
      }
      this.view.populate(this.model);
      this.view.statusMessage('ready');
    } catch (error) { if (!this.destroyed) this.view.statusMessage('error', loadErrorMessage(error)); }
    finally { this.loading = false; }
  }
  async submit(customer) {
    if (this.busy || this.sent || this.loading || this.destroyed) return;
    this.busy = true;
    this.view.setBusy(true);
    this.view.result('');
    try {
      const response = await quoteApi.createQuoteRequest(this.model.payload(customer));
      this.sent = true;
      this.view.result(response?.request_number
        ? `Заявка ${response.request_number} принята. Сумма сервера: ${response.total_price} ${response.currency}. Стоимость и срок подтвердит менеджер.`
        : 'Сервер обработал запрос, но не вернул номер. Уточните результат у менеджера перед повторной отправкой.');
      this.view.tracking(response);
    } catch (error) {
      this.view.result(`${error.message}. При потере связи заявка могла сохраниться — уточните результат перед повторной отправкой.`);
    } finally { this.busy = false; this.view.setBusy(false, this.sent); }
  }
  destroy() { this.destroyed = true; this.view.destroy(); }
}

export class ServicesController {
  constructor(roots) { this.controllers = Array.from(roots?.nodeType ? [roots] : roots || []).map(root => new ServiceController(root)); }
  async init() { await Promise.all(this.controllers.map(controller => controller.load())); }
  destroy() { this.controllers.forEach(controller => controller.destroy()); }
}
