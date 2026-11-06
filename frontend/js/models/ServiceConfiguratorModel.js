import { apiLocale } from '../i18n/locale.js?v=20261106.1';
const number = value => value === '' || value == null ? NaN : Number(value);

export class ServiceConfiguratorModel {
  constructor(type) {
    this.type = type;
    this.state = { material: null, service: null, diameter: 8, quantity: 1, eye: 10, urgent: false, extras: new Set() };
    // Цена с сервера: quote — ответ /quote_requests/calculate, quoteFor — для каких параметров.
    this.quote = null;
    this.quoteFor = null;
    this.priceError = null;
    this.priceErrorFor = null;
  }

  init(data) {
    const settings = data.settings;
    if (!settings || !Number.isInteger(number(settings.urgent_max_splices)) || number(settings.urgent_max_splices) < 0) {
      throw new Error('Не получены корректные настройки расчёта.');
    }
    this.settings = settings;
    this.materials = data.splice_materials;
    this.services = data.splice_types.filter(s => s.is_active !== false && s.category === (this.type === 'loop_only' ? 'loop' : 'splice'));
    this.extras = data.extras.filter(e => e.is_active !== false && ['fixed', 'per_item'].includes(e.billing_type));
    if (!this.materials.some(m => Number(m.id) === this.state.material)) this.state.material = Number(this.materials[0]?.id) || null;
    if (!this.services.some(s => Number(s.id) === this.state.service)) this.state.service = Number(this.services[0]?.id) || null;
    this.state.extras = new Set([...this.state.extras].filter(id => this.extras.some(e => Number(e.id) === id)));
  }

  set(name, value) {
    if (name === 'urgent') this.state.urgent = Boolean(value);
    else if (name === 'extra') {
      const id = Number(value);
      if (!this.extras.some(e => Number(e.id) === id)) return;
      this.state.extras.has(id) ? this.state.extras.delete(id) : this.state.extras.add(id);
    } else if (['material', 'service', 'diameter', 'quantity', 'eye'].includes(name)) this.state[name] = number(value);
  }

  needsEye() {
    return this.services?.find(item => Number(item.id) === this.state.service)?.category === 'loop';
  }

  // Ошибка в параметрах, которую видно без сервера. Пустая строка — можно считать цену.
  localError() {
    const s = this.state;
    if (!this.services?.some(item => Number(item.id) === s.service) || !this.materials?.some(m => Number(m.id) === s.material)) return 'Нет доступных материалов или услуг.';
    if (!Number.isFinite(s.diameter) || s.diameter <= 0 || !Number.isInteger(s.quantity) || s.quantity < 1 || s.quantity > 999
      || (this.needsEye() && (!Number.isFinite(s.eye) || s.eye < 0.1))) return 'Проверьте диаметр, количество и размер петли.';
    if (s.urgent && s.quantity > Number(this.settings.urgent_max_splices)) return `Срочное изготовление: не более ${this.settings.urgent_max_splices} работ.`;
    return '';
  }

  // Тело для POST /quote_requests/calculate. Размер петли на цену не влияет и в расчёт не идёт.
  calcPayload() {
    if (this.localError()) return null;
    const s = this.state;
    return { configurator_type: this.type, is_urgent: s.urgent, locale: apiLocale(), rope_items: [],
      service_items: [{ splice_type_id: s.service, splice_material_id: s.material, diameter_mm: s.diameter, quantity: s.quantity }],
      extra_items: [...s.extras].sort((a, b) => a - b).map(extra_id => ({ extra_id })) };
  }

  quoteKey() {
    const payload = this.calcPayload();
    return payload ? JSON.stringify(payload) : null;
  }

  setQuote(quote, key) { this.quote = quote; this.quoteFor = key; }
  setPriceError(error, key) { this.priceError = error; this.priceErrorFor = key; }

  // Состояние для вида: ошибки ввода, статус расчёта и суммы из ответа сервера.
  summary() {
    const key = this.quoteKey();
    const quote = key && this.quoteFor === key ? this.quote : null;
    const status = !key ? 'invalid' : quote ? 'ready' : this.priceErrorFor === key ? 'error' : 'loading';
    const sum = items => (items || []).reduce((total, item) => total + Number(item.total_cost || 0), 0);
    return {
      status,
      needsEye: this.needsEye(),
      error: status === 'invalid' ? this.localError() : status === 'error' ? this.priceError.text : '',
      retry: status === 'error' && this.priceError.retry,
      work: quote ? sum(quote.service_items) : null,
      extras: quote ? sum(quote.extra_items) : null,
      urgent: quote ? Number(quote.urgent_surcharge || 0) : null,
      total: quote ? Number(quote.total_price) : null,
      currency: quote?.currency || this.settings?.currency || 'EUR',
    };
  }

  payload(customer) {
    const payload = this.calcPayload();
    if (!payload || this.summary().status !== 'ready') throw new Error(this.localError() || 'Дождитесь расчёта стоимости.');
    if (!customer.name?.trim() || !customer.email?.trim() || !customer.consent) throw new Error('Заполните контакты и согласие на обработку данных.');
    payload.service_items[0].eye_size_cm = this.needsEye() ? this.state.eye : null;
    return { ...payload, name: customer.name.trim(), email: customer.email.trim(),
      phone: customer.phone?.trim() || null, comment: customer.comment?.trim() || null };
  }
}
