import { loadErrorMessage } from '../ui/load-state.js?v=20261027.10';
import { BaseController } from './BaseController.js?v=20261027.10';
import { ConfiguratorModel } from '../models/ConfiguratorModel.js?v=20261027.10';
import { ConfiguratorView } from '../views/configurator/ConfiguratorView.js?v=20261027.10';
import { configuratorApi } from '../api/configuratorApi.js?v=20261027.10';
import { quoteApi } from '../api/quoteApi.js?v=20261027.10';

export class ConfiguratorController extends BaseController {
  constructor() {
    super();
    this.model = new ConfiguratorModel();
    this.view = new ConfiguratorView('#configurator');
    this.submitting = false;
    this.sent = false;
  }

  async init() {
    if (!this.view.form) return;
    await super.init();
    this.bindViewEvents();
    const render = (snapshot) => this.view.render(snapshot);
    for (const event of ['data:loaded', 'change:product', 'change:variant', 'change:color', 'change:length',
      'change:quantity', 'change:endA', 'change:endB', 'change:extras', 'change:urgent', 'change:prices']) {
      this.model.on(event, render);
    }
    this.view.initListeners();
    this.view.onEvent('onRetry', () => this.loadData());
    this.view.onEvent('onPriceRetry', () => this.loadData());
    await this.loadData();
  }

  bindViewEvents() {
    for (const [event, method] of [['onColorChange', 'setColor'], ['onLengthChange', 'setLength'],
      ['onQuantityChange', 'setQuantity'], ['onEyeSizeChange', 'setEyeSize'], ['onExtraChange', 'toggleExtra'],
      ['onUrgentChange', 'setUrgent'], ['onEndAChange', 'setEndA'], ['onEndBChange', 'setEndB']]) {
      this.view.onEvent(event, (...args) => this.model[method](...args));
    }
    this.view.onEvent('onProductChange', (id) => { this.model.setProduct(id); this.loadPrices(); });
    this.view.onEvent('onVariantChange', (id) => { this.model.setVariant(id); this.loadPrices(); });
    this.view.onEvent('onSubmit', async (customer) => {
      this.model.setCustomerInfo(customer);
      await this.submitOrder();
    });
  }

  async loadData() {
    if (this.loading || this.submitting || this.sent) return;
    this.loading = true;
    this.view.setDataStatus('loading', 'Загружаем товары и настройки…');
    try {
      const refresh = Boolean(this.attempted);
      this.attempted = true;
      const data = await configuratorApi.getData('rope_with_splice', undefined, { refresh });
      const { settings, rope_products: products, splice_types: spliceTypes, extras } = data;
      if (!products.length) { this.view.setDataStatus('empty', 'Доступных товаров пока нет.'); return; }
      const colors = products.flatMap(p => (p.colors || []).map(link => link.color).filter(Boolean));
      this.rules = data.splice_price_rules;
      this.model.initData({ settings, products, colors, spliceTypes, extras });
      const requested = new URLSearchParams(window.location.search).get('product');
      if (requested) {
        if (!this.model.getProductById(requested)) { this.view.setDataStatus('missing', 'Товар по этой ссылке недоступен. Выберите другой товар в каталоге.'); return; }
        this.model.setProduct(requested);
      }
      this.view.setDataStatus('ready', products.length ? '' : 'Доступных товаров пока нет.');
      await this.loadPrices();
    } catch (error) {
      this.view.setDataStatus('error', loadErrorMessage(error));
    } finally {
      this.loading = false;
    }
  }

  async loadPrices() {
    this.model.setPrices(this.rules || [], 'ready');
  }

  async submitOrder() {
    if (this.submitting || this.sent) return;
    this.submitting = true;
    this.view.setSubmitLoading(true);
    try {
      const payload = this.model.toQuoteRequestPayload();
      const response = await quoteApi.createQuoteRequest(payload);
      this.sent = true;
      this.view.submitted = true;
      if (!response?.request_number) {
        this.view.showSubmitError('Сервер обработал запрос, но не вернул номер заявки. Уточните результат у менеджера перед повторным обращением.');
      } else {
        this.view.showSubmitSuccess(response);
      }
    } catch (error) {
      this.view.showSubmitError(`${error.message || 'Ошибка соединения'}. При потере связи заявка могла сохраниться — уточните результат перед повторной отправкой.`);
    } finally {
      this.submitting = false;
      this.view.setSubmitLoading(false);
    }
  }
}
