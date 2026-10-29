// Pure DTO validation; independent of DOM and HTTP transport.
export class AdminProductModel {
  static catalogProduct(values) {
    const settings = this.product(values);
    delete settings.working_stretch_percent;
    const translations = ['rus','eng','ger'].filter(locale=>String(values[`name_${locale}`]||'').trim()).map(locale=>({
      locale, name: values[`name_${locale}`].trim(), subtitle: String(values[`subtitle_${locale}`]||'').trim()||null,
      description: String(values[`description_${locale}`]||'').trim()||null,
    }));
    if(!translations.length) throw new Error('Укажите название хотя бы на одном языке.');
    const slug = String(values.slug||'').trim();
    if(!slug || slug.length>150) throw new Error('Укажите адрес товара длиной до 150 символов.');
    return { category_id:this.number(values,'category_id',{required:true,min:1,integer:true}), slug,
      product_type:'rope',price_unit:'meter',has_configurator:Boolean(values.has_configurator),
      construction_type:String(values.construction_type||'').trim()||null,
      index:this.index(values), is_active:Boolean(values.is_active),translations,settings };
  }
  static catalogVariant(values) {
    const old = this.variant(values);
    const variant_name = String(values.variant_name || (old.diameter_mm ? `${old.diameter_mm} мм` : '')).trim();
    if(!variant_name) throw new Error('Укажите название диаметра.');
    return { variant_name, size_value:old.diameter_mm, price:old.price_per_meter,weight_g:old.weight_g_per_m,
      breaking_load_dan:old.breaking_load_dan,is_active:old.is_active,sku:String(values.sku||'').trim()||null,
      working_load_dan:this.number(values,'working_load_dan'),working_stretch_percent:this.number(values,'working_stretch_percent',{max:100}) };
  }
  static index(values) {
    return this.number(values, 'index', { required: true, min: 0, integer: true });
  }
  static number(values, key, { required = false, min = 0, max = Infinity, integer = false } = {}) {
    const raw = values[key];
    if (raw == null || String(raw).trim() === '') {
      if (required) throw new Error(`Не заполнено поле ${key}`);
      return null;
    }
    const value = Number(raw);
    if (!Number.isFinite(value) || value < min || value > max || (integer && !Number.isInteger(value))) {
      throw new Error(`Некорректное значение ${key}`);
    }
    return value;
  }
  static product(values) {
    const text = key => String(values[key] ?? '').trim() || null;
    const construction = text('construction');
    if (construction?.length > 255) throw new Error('Название длиннее 255 символов');
    return {
      material_group_id: this.number(values, 'material_group_id', { required: true, min: 1, integer: true }),
      splice_material_id: this.number(values, 'splice_material_id', { required: true, min: 1, integer: true }),
      construction, core_description: text('core_description'), cover_description: text('cover_description'),
      working_stretch_percent: this.number(values, 'working_stretch_percent', { max: 100 }),
      can_be_spliced: Boolean(values.can_be_spliced),
    };
  }
  static variant(values) {
    return {
      diameter_mm: this.number(values, 'diameter_mm', { required: true, min: 0.01, max: 9999.99 }),
      price_per_meter: this.number(values, 'price_per_meter', { required: true, max: 99999999.99 }),
      breaking_load_dan: this.number(values, 'breaking_load_dan', { max: 99999999.99 }),
      weight_g_per_m: this.number(values, 'weight_g_per_m', { max: 99999999.99 }),
      is_active: Boolean(values.is_active),
    };
  }
}
