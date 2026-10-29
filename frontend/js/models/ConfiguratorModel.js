import { BaseModel } from './BaseModel.js?v=20261027.10';
import { displayName } from '../utils/text.js?v=20261027.10';
import { apiLocale } from '../i18n/locale.js?v=20261027.10';
import { normalizeProduct } from '../api/productAdapter.js?v=20261027.10';

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
    this.priceStatus = 'loading';

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
  initData({ settings, products, colors, spliceTypes, extras }) {
    const required = ['min_length_m', 'max_length_m', 'splice_allowance_until_mm', 'splice_allowance_until_m',
      'splice_allowance_over_m', 'urgent_surcharge_per_splice', 'urgent_max_splices'];
    if (!settings || required.some((key) => settings[key] == null || !Number.isFinite(Number(settings[key])) || Number(settings[key]) < 0)
      || Number(settings.min_length_m) <= 0 || Number(settings.max_length_m) < Number(settings.min_length_m)) {
      throw new Error('Не получены корректные настройки расчёта.');
    }
    if (![products, colors, spliceTypes, extras].every(Array.isArray)) throw new Error('Некорректные справочники конфигуратора.');
    this.settings = settings;
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
      this.priceStatus = 'loading';
      this.spliceRules = [];
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
    this.emit('change:color', this.getDataSnapshot());
  }

  syncProductSelection() {
    const variants = this.getCurrentProduct()?.variants || [];
    const variant = variants.find((v) => v.id === this.state.selectedVariantId) || variants[0];
    this.state.selectedVariantId = variant?.id ?? null;
    this.state.diameterMm = variant ? Number(variant.diameter_mm) : null;
    const colors = this.getAvailableColors();
    this.state.selectedColorId = colors.find((c) => c.id === this.state.selectedColorId)?.id ?? colors[0]?.id ?? null;
    this.priceStatus = 'loading';
    this.spliceRules = [];
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

  setPrices(rules, status) {
    this.spliceRules = Array.isArray(rules) ? rules : [];
    this.priceStatus = Array.isArray(rules) ? status : 'error';
    this.recalculate();
    this.emit('change:prices', this.getDataSnapshot());
  }

  endPrice(end) {
    if (end.spliceTypeId === null) return 0;
    if (this.priceStatus !== 'ready') return null;
    const rules = this.spliceRules.filter((rule) => Number(rule.splice_type_id) === end.spliceTypeId
      && Number(rule.splice_material_id) === Number(this.getCurrentProduct()?.splice_material_id)
      && rule.is_active !== false
      && (rule.diameter_from_mm == null || Number(rule.diameter_from_mm) <= this.state.diameterMm)
      && (rule.diameter_to_mm == null || Number(rule.diameter_to_mm) >= this.state.diameterMm));
    if (this.getCurrentProduct()?.apiVersion === 2) rules.sort((a,b) =>
      (b.diameter_from_mm ?? -Infinity) - (a.diameter_from_mm ?? -Infinity) || Number(b.id) - Number(a.id));
    if (!rules.length || (this.getCurrentProduct()?.apiVersion !== 2 && rules.length !== 1)
      || rules[0].price == null || !Number.isFinite(Number(rules[0].price)) || Number(rules[0].price) < 0) return null;
    return Number(rules[0].price);
  }

  getAvailableColors() {
    // color_id — ID цвета; id в этой связи принадлежит записи привязки к товару.
    return [...(this.getCurrentProduct()?.colors || [])].sort((a,b)=>(Number(a.index)||0)-(Number(b.index)||0)).map((link) => {
      const color = link.color || this.colors.find((c) => Number(c.id) === Number(link.color_id));
      return color ? { ...color, id: Number(link.color_id) } : null;
    }).filter((color) => color && color.is_active !== false && Number.isInteger(color.id) && color.id > 0);
  }

  hasValidSelection() {
    return Boolean(this.getCurrentProduct() && this.getCurrentVariant()
      && this.getAvailableColors().some((c) => c.id === this.state.selectedColorId)
      && Number.isInteger(this.state.quantity) && this.state.quantity >= 1 && this.state.quantity <= 999
      && this.settings && Number.isFinite(this.state.lengthM)
      && this.state.lengthM >= Number(this.settings.min_length_m) && this.state.lengthM <= Number(this.settings.max_length_m)
      && this.priceStatus === 'ready' && this.calculation.totalPrice !== null
      && (!this.state.isUrgent || [this.state.endA, this.state.endB].filter((end) => end.spliceTypeId !== null).length * this.state.quantity <= Number(this.settings.urgent_max_splices))
      && [this.state.endA, this.state.endB].every((end) => !this.isLoopOrSplice(end.typeCode)
        || (Number.isFinite(end.eyeSizeCm) && end.eyeSizeCm >= 0.1)));
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
   * Пересчет показателей стоимости и длин
   */
  recalculate() {
    const product = this.getCurrentProduct();
    const variant = this.getCurrentVariant();

    // 1. Технологический запас на сплайс
    const allowanceLimit = this.settings?.splice_allowance_until_mm;
    const allowanceUnder = Number(this.settings?.splice_allowance_until_m ?? 0);
    const allowanceOver = Number(this.settings?.splice_allowance_over_m ?? 0);

    const d = this.state.diameterMm;
    const perSpliceAllowance = d <= allowanceLimit ? allowanceUnder : allowanceOver;

    const modern = product?.apiVersion === 2;
    const money = value => Math.round((value + Number.EPSILON * Math.max(1, Math.abs(value))) * 100) / 100;
    const hasSpliceA = modern ? this.state.endA.spliceTypeId !== null : this.isLoopOrSplice(this.state.endA.typeCode);
    const hasSpliceB = modern ? this.state.endB.spliceTypeId !== null : this.isLoopOrSplice(this.state.endB.typeCode);

    let splicesCount = (hasSpliceA ? 1 : 0) + (hasSpliceB ? 1 : 0);
    const ropeLengthAllowanceM = splicesCount * perSpliceAllowance;
    const totalLengthM = this.state.lengthM + ropeLengthAllowanceM;

    // 2. Стоимость каната
    const pricePerMeter = Number(variant?.price_per_meter || 0);
    const ropeCost = totalLengthM * pricePerMeter;

    // 3. Стоимость заделок (базовая оценка)
    const endACost = this.endPrice(this.state.endA);
    const endBCost = this.endPrice(this.state.endB);

    // 4. Дополнительные опции
    let extrasCost = 0;
    this.extrasList.forEach((extra) => {
      if (this.state.selectedExtraIds.has(extra.id)) {
        const units = extra.billing_type === 'per_item' ? this.state.quantity
          : extra.billing_type === 'per_meter' ? this.state.lengthM * this.state.quantity : 1;
        extrasCost += modern ? money(Number(extra.price) * units) : Number(extra.price) * units;
      }
    });

    // 5. Надбавка за срочность
    let urgentCost = 0;
    if (this.state.isUrgent) {
      const surcharge = Number(this.settings?.urgent_surcharge_per_splice ?? 0);
      urgentCost = [this.state.endA, this.state.endB].filter((end) => end.spliceTypeId !== null).length * surcharge * this.state.quantity;
    }

    const totalPrice = modern
      ? money(ropeCost * this.state.quantity) + money(endACost * this.state.quantity)
        + money(endBCost * this.state.quantity) + extrasCost + money(urgentCost)
      : (ropeCost + endACost + endBCost) * this.state.quantity + extrasCost + urgentCost;

    this.calculation = {
      ropeLengthAllowanceM,
      totalLengthM,
      ropeCost,
      endACost,
      endBCost,
      extrasCost,
      urgentCost,
      totalPrice: this.priceStatus === 'ready' && endACost !== null && endBCost !== null && Number.isFinite(totalPrice)
        && Number.isInteger(this.state.quantity) && this.state.quantity >= 1 && this.state.quantity <= 999
        && Number.isFinite(this.state.lengthM) && this.state.lengthM >= Number(this.settings?.min_length_m)
        && this.state.lengthM <= Number(this.settings?.max_length_m)
        && variant?.price_per_meter != null && Number.isFinite(Number(variant.price_per_meter))
        && Number(variant.price_per_meter) >= 0 ? Math.round(totalPrice * 100) / 100 : null,
      breakingLoadDan: variant?.breaking_load_dan || 0,
      weightG: Math.round(totalLengthM * Number(variant?.weight_g_per_m || 0)),
      currency: this.settings?.currency || 'EUR',
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
   * Сформировать DTO для отправки в POST /quote_requests
   */
  toQuoteRequestPayload() {
    if (!this.hasValidSelection()) {
      throw new Error('Проверьте выбор троса, диаметра, цвета, количество и размеры петель.');
    }

    return {
      configurator_type: 'rope_with_splice',
      name: this.state.customer.name || 'Клиент сайта',
      email: this.state.customer.email,
      phone: this.state.customer.phone || null,
      comment: this.state.customer.comment || null,
      is_urgent: Boolean(this.state.isUrgent),
      locale: apiLocale(),
      rope_items: [
        {
          [this.getCurrentProduct()?.apiVersion === 2 ? 'product_id' : 'rope_product_id']: Number(this.state.selectedProductId),
          color_id: this.state.selectedColorId,
          diameter_mm: Number(this.state.diameterMm),
          length_m: Number(this.state.lengthM),
          quantity: this.state.quantity,
          end_a_type_id: this.state.endA.spliceTypeId,
          end_a_eye_size_cm: this.isLoopOrSplice(this.state.endA.typeCode) ? this.state.endA.eyeSizeCm : null,
          end_b_type_id: this.state.endB.spliceTypeId,
          end_b_eye_size_cm: this.isLoopOrSplice(this.state.endB.typeCode) ? this.state.endB.eyeSizeCm : null,
        }
      ],
      service_items: [],
      extra_items: Array.from(this.state.selectedExtraIds).map((id) => ({ extra_id: Number(id) })),
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
      settings: this.settings,
      availableColors: this.getAvailableColors(),
      selectionValid: this.hasValidSelection(),
    };
  }
}
