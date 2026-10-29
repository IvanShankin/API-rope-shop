import { apiLocale } from '../i18n/locale.js?v=20261027.10';
const number = value => value === '' || value == null ? NaN : Number(value);
const money = value => Math.round(value * 100) / 100;

export class ServiceConfiguratorModel {
  constructor(type) {
    this.type = type;
    this.state = { material: null, service: null, diameter: 8, quantity: 1, eye: 10, urgent: false, extras: new Set() };
  }

  init(data) {
    const settings = data.settings;
    if (!settings || !Number.isInteger(number(settings.urgent_max_splices)) || number(settings.urgent_max_splices) < 0
      || !Number.isFinite(number(settings.urgent_surcharge_per_splice)) || number(settings.urgent_surcharge_per_splice) < 0) {
      throw new Error('Не получены корректные настройки расчёта.');
    }
    this.settings = settings;
    this.apiVersion = data.apiVersion;
    this.materials = data.splice_materials;
    this.services = data.splice_types.filter(s => s.is_active !== false && s.category === (this.type === 'loop_only' ? 'loop' : 'splice'));
    this.rules = data.splice_price_rules;
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

  calculate() {
    const s = this.state;
    const selected = this.services?.find(item => Number(item.id) === s.service);
    const needsEye = selected?.category === 'loop';
    const rules = (this.rules || []).filter(r => r.is_active !== false && Number(r.splice_type_id) === s.service
      && Number(r.splice_material_id) === s.material
      && (r.diameter_from_mm == null || Number(r.diameter_from_mm) <= s.diameter)
      && (r.diameter_to_mm == null || Number(r.diameter_to_mm) >= s.diameter));
    if (this.apiVersion === 2) {
      rules.sort((a,b) => (b.diameter_from_mm ?? -Infinity) - (a.diameter_from_mm ?? -Infinity) || Number(b.id) - Number(a.id));
      rules.splice(1);
    }
    let error = '';
    if (!selected || !this.materials?.some(m => Number(m.id) === s.material)) error = 'Нет доступных материалов или услуг.';
    else if (!Number.isFinite(s.diameter) || s.diameter <= 0 || !Number.isInteger(s.quantity) || s.quantity < 1 || s.quantity > 999
      || (needsEye && (!Number.isFinite(s.eye) || s.eye < 0.1))) error = 'Проверьте диаметр, количество и размер петли.';
    else if (rules.length !== 1 || !Number.isFinite(number(rules[0].price)) || number(rules[0].price) < 0) error = 'Для выбранного материала, диаметра и работы нет однозначного тарифа.';
    else if (s.urgent && s.quantity > Number(this.settings.urgent_max_splices)) error = `Срочное изготовление: не более ${this.settings.urgent_max_splices} работ.`;
    const each = rules.length === 1 ? number(rules[0].price) : NaN;
    let extras = 0;
    for (const extra of this.extras || []) {
      if (!s.extras.has(Number(extra.id))) continue;
      if (!Number.isFinite(number(extra.price)) || number(extra.price) < 0) error = 'Некорректная цена дополнительной опции.';
      extras += money(number(extra.price) * (extra.billing_type === 'per_item' ? s.quantity : 1));
    }
    const work = money(each * s.quantity);
    const urgent = s.urgent ? money(Number(this.settings?.urgent_surcharge_per_splice) * s.quantity) : 0;
    const total = money(work + extras + urgent);
    if (!error && !Number.isFinite(total)) error = 'Не удалось рассчитать стоимость.';
    return { error, needsEye, each, work, extras, urgent, total: error ? null : total, currency: this.settings?.currency || 'EUR' };
  }

  payload(customer) {
    const result = this.calculate();
    if (result.error) throw new Error(result.error);
    if (!customer.name?.trim() || !customer.email?.trim() || !customer.consent) throw new Error('Заполните контакты и согласие на обработку данных.');
    const s = this.state;
    return { configurator_type: this.type, locale: apiLocale(), name: customer.name.trim(), email: customer.email.trim(),
      phone: customer.phone?.trim() || null, comment: customer.comment?.trim() || null, is_urgent: s.urgent,
      rope_items: [], service_items: [{ splice_type_id: s.service, splice_material_id: s.material,
        diameter_mm: s.diameter, quantity: s.quantity, eye_size_cm: result.needsEye ? s.eye : null }],
      extra_items: [...s.extras].map(extra_id => ({ extra_id })) };
  }
}
