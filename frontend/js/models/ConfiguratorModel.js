import { BaseModel } from './BaseModel.js?v=20261106.1';
import { displayName } from '../utils/text.js?v=20261106.1';
import { apiLocale } from '../i18n/locale.js?v=20261106.1';
import { normalizeProduct } from '../api/productAdapter.js?v=20261106.1';

/**
 * Модель данных и бизнес-логики интерактивного конфигуратора
 */
export class ConfiguratorModel extends BaseModel {
  constructor() {
    super();

    // Загруженные с бэкенда справочники
    this.settings = null;
    this.products = [];
    this.colors = [];
    this.spliceTypes = [];
    this.extrasList = [];
    this.spliceRules = [];
    // Цена с сервера: quote — ответ /quote_requests/calculate, quoteFor — для каких параметров.
    this.quote = null;
    this.quoteFor = null;
    this.priceStatus = 'loading';
    this.priceError = '';
    this.priceErrorFor = null;

    // Текущий выбор пользователя (Состояние конфигуратора)
    this.state = {
      selectedProductId: null,
      selectedVariantId: null,
      selectedColorId: null,
      diameterMm: 10,
      lengthM: 10,
      quantity: 1,

      endA: {
        typeCode: 'cut',
        spliceTypeId: null,
        eyeSizeCm: 10,
      },

      endB: {
        typeCode: 'cut',
        spliceTypeId: null,
        eyeSizeCm: 10,
      },

      selectedExtraIds: new Set(),
      isUrgent: false,

      // Контактные данные
      customer: {
        name: '',
        email: '',
        phone: '',
        comment: '',
      },
    };

    // Предварительно рассчитанные показатели
    this.calculation = {
      ropeLengthAllowanceM: 0,
      totalLengthM: 10,
      ropeCost: 0,
      endACost: 0,
      endBCost: 0,
      extrasCost: 0,
      urgentCost: 0,
      totalPrice: 0,
      breakingLoadDan: 0,
      weightG: 0,
      currency: '€',
    };
  }

  /**
   * Инициализация данных из бэкенда
   */
  initData({ settings, products, colors, spliceTypes, extras, spliceRules = [] }) {
    const required = ['min_length_m', 'max_length_m', 'splice_allowance_until_mm', 'splice_allowance_until_m',
      'splice_allowance_over_m', 'urgent_surcharge_per_splice', 'urgent_max_splices'];
    if (!settings || required.some((key) => settings[key] == null || !Number.isFinite(Number(settings[key])) || Number(settings[key]) < 0)
      || Number(settings.min_length_m) <= 0 || Number(settings.max_length_m) < Number(settings.min_length_m)) {
      throw new Error('Не получены корректные настройки расчёта.');
    }
    if (![products, colors, spliceTypes, extras].every(Array.isArray)) throw new Error('Некорректные справочники конфигуратора.');
    this.settings = settings;
    this.spliceRules = Array.isArray(spliceRules) ? spliceRules : [];
    this.products = (products || []).map(normalizeProduct).map((product) => ({
      ...product,
      product_id: Number(product.product_id ?? product.id),
      variants: (product.variants || []).filter((v) => v.is_active !== false).map((v) => ({ ...v, id: Number(v.id) })).sort((a,b)=>(Number(a.index)||0)-(Number(b.index)||0)),
    }));
    this.colors = (colors || []).filter((color) => color.is_active !== false);
    this.spliceTypes = spliceTypes.filter((type) => type.is_active !== false);
    this.extrasList = (extras || []).filter((extra) => extra.is_active !== false).map((extra) => ({ ...extra, id: Number(extra.id) }));
    this.state.selectedExtraIds = new Set([...this.state.selectedExtraIds].filter((id) => this.extrasList.some((extra) => extra.id === id)));

    this.state.selectedProductId = this.getCurrentProduct()?.product_id ?? this.products[0]?.product_id ?? null;
    this.syncProductSelection();
    this.state.lengthM = Math.min(Number(settings.max_length_m), Math.max(Number(settings.min_length_m), this.state.lengthM || Number(settings.min_length_m)));

    this.recalculate();
    this.emit('data:loaded', this.getDataSnapshot());
  }

  /**
   * Установить выбранный канат
   */
  setProduct(productId) {
    const product = this.getProductById(productId);
    if (!product) return;

    this.state.selectedProductId = product.product_id;
    this.syncProductSelection();

    this.recalculate();
    this.emit('change:product', this.getDataSnapshot());
  }

  /**
   * Установить диаметр / вариант
   */
  setVariant(variantId) {
    const product = this.getCurrentProduct();
    if (!product) return;

    const variant = product.variants?.find((v) => v.id === Number(variantId));
    if (variant) {
      this.state.selectedVariantId = variant.id;
      this.state.diameterMm = Number(variant.diameter_mm);
      this.recalculate();
      this.emit('change:variant', this.getDataSnapshot());
    }
  }

  /**
   * Установить цвет
   */
  setColor(colorId) {
    const color = this.getAvailableColors().find((item) => item.id === Number(colorId));
    if (!color) return;
    this.state.selectedColorId = color.id;
    this.recalculate();
    this.emit('change:color', this.getDataSnapshot());
  }

  syncProductSelection() {
    const variants = this.getCurrentProduct()?.variants || [];
    const variant = variants.find((v) => v.id === this.state.selectedVariantId) || variants[0];
    this.state.selectedVariantId = variant?.id ?? null;
    this.state.diameterMm = variant ? Number(variant.diameter_mm) : null;
    const colors = this.getAvailableColors();
    this.state.selectedColorId = colors.find((c) => c.id === this.state.selectedColorId)?.id ?? colors[0]?.id ?? null;
    for (const key of ['endA', 'endB']) {
      if (!this.getAvailableEnds().some((end) => end.id === this.state[key].spliceTypeId)) {
        this.state[key] = { ...this.state[key], typeCode: 'cut', spliceTypeId: null };
      }
    }
  }

  getAvailableEnds() {
    const product = this.getCurrentProduct();
    const cut = { id: null, name: 'Без обработки', visual: 'cut' };
    if (!product || product.can_be_spliced === false) return [cut];
    const allowed = (product.allowed_splices || []).map((link) => Number(link.splice_type_id));
    const visuals = { aug_splice: 'eye', pilotauge: 'eye', exposed_eye: 'eye', sewn_eye: 'eye',
      takling: 'whip', kausche: 'thimble', shackle: 'shackle', soft_shackle: 'soft' };
    return [cut, ...this.spliceTypes.filter((type) => (!allowed.length || allowed.includes(Number(type.id)))
      && visuals[type.visual_type]).map((type) => ({ id: Number(type.id), name: displayName(type), visual: visuals[type.visual_type] }))];
  }

  // Тарифы из GET /configurators — только подсказка цены у вариантов обработки.
  // Итог и детализацию считает сервер (POST /quote_requests/calculate).
  endPrice(end) {
    if (end.spliceTypeId === null) return 0;
    const product = this.getCurrentProduct();
    const rule = this.spliceRules.filter((item) => Number(item.splice_type_id) === end.spliceTypeId
      && Number(item.splice_material_id) === Number(product?.splice_material_id)
      && item.is_active !== false
      && (item.diameter_from_mm == null || Number(item.diameter_from_mm) <= this.state.diameterMm)
      && (item.diameter_to_mm == null || Number(item.diameter_to_mm) >= this.state.diameterMm))
      .sort((a, b) => (b.diameter_from_mm ?? -Infinity) - (a.diameter_from_mm ?? -Infinity) || Number(b.id) - Number(a.id))[0];
    const price = Number(rule?.price);
    return rule && rule.price != null && Number.isFinite(price) && price >= 0 ? price : null;
  }

  /** Ответ сервера на расчёт. key — параметры, для которых он получен. */
  setQuote(quote, key) {
    this.quote = quote;
    this.quoteFor = key;
    this.recalculate();
    this.emit('change:prices', this.getDataSnapshot());
  }

  setPriceError({ text, retry }, key) {
    this.priceError = text;
    this.priceRetry = retry;
    this.priceErrorFor = key;
    this.recalculate();
    this.emit('change:prices', this.getDataSnapshot());
  }

  getAvailableColors() {
    // color_id — ID цвета; id в этой связи принадлежит записи привязки к товару.
    return [...(this.getCurrentProduct()?.colors || [])].sort((a,b)=>(Number(a.index)||0)-(Number(b.index)||0)).map((link) => {
      const color = link.color || this.colors.find((c) => Number(c.id) === Number(link.color_id));
      return color ? { ...color, id: Number(link.color_id) } : null;
    }).filter((color) => color && color.is_active !== false && Number.isInteger(color.id) && color.id > 0);
  }

  // Ошибка в параметрах, которую видно без сервера. Пустая строка — можно считать цену.
  localError() {
    const { state, settings } = this;
    if (!this.getCurrentProduct() || !this.getCurrentVariant() || !settings) return 'Выберите канат и диаметр.';
    if (!this.getAvailableColors().some((c) => c.id === state.selectedColorId)) return 'Выберите цвет.';
    if (!Number.isInteger(state.quantity) || state.quantity < 1 || state.quantity > 999) return 'Укажите количество от 1 до 999.';
    if (!Number.isFinite(state.lengthM) || state.lengthM < Number(settings.min_length_m) || state.lengthM > Number(settings.max_length_m)) {
      return `Укажите длину от ${settings.min_length_m} до ${settings.max_length_m} м.`;
    }
    if ([state.endA, state.endB].some((end) => this.isLoopOrSplice(end.typeCode) && !(Number.isFinite(end.eyeSizeCm) && end.eyeSizeCm >= 0.1))) {
      return 'Укажите размер петли.';
    }
    if (state.isUrgent && this.splicesCount() * state.quantity > Number(settings.urgent_max_splices)) {
      return `Срочное изготовление: не более ${settings.urgent_max_splices} сращиваний в заказе.`;
    }
    return '';
  }

  splicesCount() {
    return [this.state.endA, this.state.endB].filter((end) => end.spliceTypeId !== null).length;
  }

  hasValidSelection() {
    return this.priceStatus === 'ready';
  }

  setQuantity(value) {
    const quantity = Number(value);
    this.state.quantity = Number.isInteger(quantity) && quantity >= 1 && quantity <= 999 ? quantity : null;
    this.recalculate();
    this.emit('change:quantity', this.getDataSnapshot());
  }

  setEyeSize(side, value) {
    if (!['a', 'b'].includes(side)) return;
    const end = this.state[side === 'a' ? 'endA' : 'endB'];
    const size = Number(value);
    end.eyeSizeCm = Number.isFinite(size) && size >= 0.1 ? size : null;
    this.recalculate();
    this.emit(side === 'a' ? 'change:endA' : 'change:endB', this.getDataSnapshot());
  }

  /**
   * Установить длину чистового троса
   */
  setLength(meters) {
    const value = Number(meters);
    this.state.lengthM = meters !== '' && Number.isFinite(value) ? value : null;
    this.recalculate();
    this.emit('change:length', this.getDataSnapshot());
  }

  /**
   * Установить конфигурацию конца A
   */
  setEndA(value) {
    this.setEnd('endA', value);
  }

  /**
   * Установить конфигурацию конца B
   */
  setEndB(value) {
    this.setEnd('endB', value);
  }

  setEnd(key, value) {
    const selected = this.getAvailableEnds().find((end) => end.id === (value === 'cut' ? null : Number(value)));
    if (!selected) return;
    this.state[key] = { ...this.state[key], typeCode: selected.visual, spliceTypeId: selected.id };
    this.recalculate();
    this.emit(`change:${key}`, this.getDataSnapshot());
  }

  /**
   * Переключить доп. опцию
   */
  toggleExtra(extraId) {
    const id = Number(extraId);
    if (!this.extrasList.some((extra) => extra.id === id)) return;
    if (this.state.selectedExtraIds.has(id)) {
      this.state.selectedExtraIds.delete(id);
    } else {
      this.state.selectedExtraIds.add(id);
    }
    this.recalculate();
    this.emit('change:extras', this.getDataSnapshot());
  }

  /**
   * Переключить флаг срочности
   */
  setUrgent(isUrgent) {
    this.state.isUrgent = Boolean(isUrgent);
    this.recalculate();
    this.emit('change:urgent', this.getDataSnapshot());
  }

  /**
   * Установить контакты клиента
   */
  setCustomerInfo(info) {
    this.state.customer = { ...this.state.customer, ...info };
    this.emit('change:customer', this.state.customer);
  }

  /**
   * Длины и вес считаем на месте (для подсказок), деньги берём только из ответа сервера.
   * Любое изменение параметров сбрасывает старый расчёт — контроллер запросит новый.
   */
  recalculate() {
    const variant = this.getCurrentVariant();
    const d = this.state.diameterMm;
    const perSpliceAllowance = d <= Number(this.settings?.splice_allowance_until_mm)
      ? Number(this.settings?.splice_allowance_until_m ?? 0) : Number(this.settings?.splice_allowance_over_m ?? 0);
    const ropeLengthAllowanceM = this.splicesCount() * perSpliceAllowance;
    const totalLengthM = Math.round(((this.state.lengthM ?? 0) + ropeLengthAllowanceM) * 100) / 100;

    const key = this.quoteKey();
    const quote = key && this.quoteFor === key ? this.quote : null;
    this.priceStatus = !key ? 'invalid' : quote ? 'ready' : this.priceErrorFor === key ? 'error' : 'loading';

    const rope = quote?.rope_items?.[0];
    const sum = (items) => (items || []).reduce((total, item) => total + Number(item.total_cost || 0), 0);
    this.calculation = {
      ropeLengthAllowanceM,
      totalLengthM,
      pricePerMeter: rope ? Number(rope.price_per_meter_snapshot) : null,
      ropeCost: rope ? Number(rope.total_rope_cost) : null,
      endACost: rope ? Number(rope.end_a_cost) : null,
      endBCost: rope ? Number(rope.end_b_cost) : null,
      extrasCost: quote ? sum(quote.extra_items) : null,
      urgentCost: quote ? Number(quote.urgent_surcharge || 0) : null,
      totalPrice: quote ? Number(quote.total_price) : null,
      breakingLoadDan: variant?.breaking_load_dan || 0,
      weightG: Math.round(totalLengthM * Number(variant?.weight_g_per_m || 0)),
      currency: quote?.currency || this.settings?.currency || 'EUR',
    };
  }

  isLoopOrSplice(typeCode) {
    return ['eye', 'thimble', 'shackle', 'soft'].includes(typeCode);
  }

  getCurrentProduct() {
    return this.products.find((p) => (p.product_id || p.id) === this.state.selectedProductId) || null;
  }

  getCurrentVariant() {
    const product = this.getCurrentProduct();
    return product?.variants?.find((v) => v.id === this.state.selectedVariantId) || null;
  }

  getProductById(id) {
    return this.products.find((p) => (p.product_id || p.id) === Number(id)) || null;
  }

  /**
   * Тело для POST /quote_requests/calculate. Размер петли на цену не влияет,
   * поэтому в расчёт не передаём: меньше лишних запросов при наборе.
   */
  toCalculatePayload() {
    if (this.localError()) return null;
    return {
      configurator_type: 'rope_with_splice',
      is_urgent: Boolean(this.state.isUrgent),
      locale: apiLocale(),
      rope_items: [{
        product_id: Number(this.state.selectedProductId),
        color_id: this.state.selectedColorId,
        diameter_mm: Number(this.state.diameterMm),
        length_m: Number(this.state.lengthM),
        quantity: this.state.quantity,
        end_a_type_id: this.state.endA.spliceTypeId,
        end_b_type_id: this.state.endB.spliceTypeId,
      }],
      service_items: [],
      extra_items: Array.from(this.state.selectedExtraIds).sort((a, b) => a - b).map((id) => ({ extra_id: Number(id) })),
    };
  }

  quoteKey() {
    const payload = this.toCalculatePayload();
    return payload ? JSON.stringify(payload) : null;
  }

  /**
   * Сформировать DTO для отправки в POST /quote_requests
   */
  toQuoteRequestPayload() {
    if (!this.hasValidSelection()) {
      throw new Error('Проверьте выбор троса, диаметра, цвета, количество и размеры петель.');
    }
    const payload = this.toCalculatePayload();
    const [rope] = payload.rope_items;
    return {
      ...payload,
      name: this.state.customer.name || 'Клиент сайта',
      email: this.state.customer.email,
      phone: this.state.customer.phone || null,
      comment: this.state.customer.comment || null,
      rope_items: [{
        ...rope,
        end_a_eye_size_cm: this.isLoopOrSplice(this.state.endA.typeCode) ? this.state.endA.eyeSizeCm : null,
        end_b_eye_size_cm: this.isLoopOrSplice(this.state.endB.typeCode) ? this.state.endB.eyeSizeCm : null,
      }],
    };
  }

  getDataSnapshot() {
    return {
      state: { ...this.state },
      calculation: { ...this.calculation },
      currentProduct: this.getCurrentProduct(),
      currentVariant: this.getCurrentVariant(),
      products: this.products,
      extras: this.extrasList,
      ends: this.getAvailableEnds().map((end) => ({ ...end, price: this.endPrice({ spliceTypeId: end.id }) })),
      priceStatus: this.priceStatus,
      priceError: this.priceStatus === 'error' ? this.priceError : this.priceStatus === 'invalid' ? this.localError() : '',
      priceRetry: this.priceStatus === 'error' && this.priceRetry,
      settings: this.settings,
      availableColors: this.getAvailableColors(),
      selectionValid: this.hasValidSelection(),
    };
  }
}
