export class AdminColorModel {
  static index(values){const raw=values.index;const value=Number(raw);if(raw==null||String(raw).trim()===''||!Number.isInteger(value)||value<0)throw new Error('Порядок должен быть целым неотрицательным числом');return value;}
  static payload(values) {
    const code = String(values.code || '').trim();
    const hex = String(values.hex || '').trim();
    if (!code || code.length > 100) throw new Error('Укажите код цвета длиной до 100 символов');
    if (hex && !/^#[0-9a-f]{6}$/i.test(hex)) throw new Error('HEX должен иметь вид #AABBCC');
    const translations = ['rus','eng','ger'].map(locale => ({locale,name:String(values[locale]||'').trim()})).filter(t=>t.name);
    if (!translations.length||translations.some(t=>t.name.length>255)) throw new Error('Заполните название хотя бы на одном языке (до 255 символов)');
    return { code, hex: hex ? hex.toUpperCase() : null, is_active: Boolean(values.is_active), translations };
  }
  static linkChanges(current, selected) {
    const wanted = new Set(selected.map(Number));
    if ([...wanted].some(id => !Number.isInteger(id) || id <= 0)) throw new Error('Некорректный цвет');
    const existing = new Set(current.map(link => Number(link.color_id)));
    return { add: [...wanted].filter(id => !existing.has(id)), remove: current.filter(link => !wanted.has(Number(link.color_id))).map(link => link.id) };
  }
}
