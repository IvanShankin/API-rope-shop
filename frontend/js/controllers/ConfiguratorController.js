import { loadErrorMessage } from '../ui/load-state.js?v=20261106.1';
import { BaseController } from './BaseController.js?v=20261106.1';
import { ConfiguratorModel } from '../models/ConfiguratorModel.js?v=20261106.1';
import { ConfiguratorView } from '../views/configurator/ConfiguratorView.js?v=20261106.1';
import { configuratorApi } from '../api/configuratorApi.js?v=20261106.1';
import { quoteApi } from '../api/quoteApi.js?v=20261106.1';
import { QuoteCalculator } from '../api/quoteCalculator.js?v=20261106.1';

export class ConfiguratorController extends BaseController {
  constructor() {
    super();
    this.model = new ConfiguratorModel();
    this.view = new ConfiguratorView('#configurator');
    this.submitting = false;
    this.sent = false;
    this.calculator = new QuoteCalculator({
      onResult: (quote, key) => this.model.setQuote(quote, key),
      onError: (error, key) => this.model.setPriceError(error, key),
    });
  }

  async init() {
    if (!this.view.form) return;
    await super.init();
    this.bindViewEvents();
    // Любое изменение параметров: перерисовать сразу и попросить у сервера новую цену.
    const update = (snapshot) => { this.view.render(snapshot); this.requestPrice(); };
    for (const event of ['data:loaded', 'change:product', 'change:variant', 'change:color', 'change:length',
      'change:quantity', 'change:endA', 'change:endB', 'change:extras', 'change:urgent']) {
      this.model.on(event, update);
    }
    this.model.on('change:prices', (snapshot) => this.view.render(snapshot));
    this.view.initListeners();
    this.view.onEvent('onRetry', () => this.loadData());
    this.view.onEvent('onPriceRetry', () => this.calculator.retry(this.model.toCalculatePayload()));
    await this.loadData();
  }

  bindViewEvents() {
    for (const [event, method] of [['onColorChange', 'setColor'], ['onLengthChange', 'setLength'],
      ['onQuantityChange', 'setQuantity'], ['onEyeSizeChange', 'setEyeSize'], ['onExtraChange', 'toggleExtra'],
      ['onUrgentChange', 'setUrgent'], ['onEndAChange', 'setEndA'], ['onEndBChange', 'setEndB']]) {
      this.view.onEvent(event, (...args) => this.model[method](...args));
    }
    this.view.onEvent('onProductChange', (id) => this.model.setProduct(id));
    this.view.onEvent('onVariantChange', (id) => this.model.setVariant(id));
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
      const { settings, rope_products: products, splice_types: spliceTypes, extras, splice_price_rules: spliceRules } = data;
      if (!products.length) { this.view.setDataStatus('empty', 'Доступных товаров пока нет.'); return; }
      const colors = products.flatMap(p => (p.colors || []).map(link => link.color).filter(Boolean));
      this.model.initData({ settings, products, colors, spliceTypes, extras, spliceRules });
      const requested = new URLSearchParams(window.location.search).get('product');
      if (requested) {
        if (!this.model.getProductById(requested)) { this.view.setDataStatus('missing', 'Товар по этой ссылке недоступен. Выберите другой товар в каталоге.'); return; }
        this.model.setProduct(requested);
      }
      this.view.setDataStatus('ready', '');
    } catch (error) {
      this.view.setDataStatus('error', loadErrorMessage(error));
    } finally {
      this.loading = false;
    }
  }

  requestPrice() {
    if (this.sent) return;
    this.calculator.schedule(this.model.priceStatus === 'loading' ? this.model.toCalculatePayload() : null);
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
