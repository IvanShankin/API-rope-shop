const field = (name, label, type = 'text', extra = {}) => ({ name, label, type, ...extra });
const active = field('is_active', 'Активен', 'checkbox');
const code = field('code', 'Код', 'text', { required: true, maxLength:100 });
const order = field('index','Порядок','number',{min:0,integer:true,required:true,default:0});
const price = field('price', 'Цена, EUR', 'number', { min: 0, required: true });
export const configSections = {
  categories: { title:'Категории каталога', translated:true, separateIndex:true, fields:[field('slug','Адрес категории (латиницей, без пробелов)','text',{required:true,maxLength:100}),order,active] },
  splice_types: { title: 'Заделки и виды работ', translated: true, description: true, fields: [code,
    field('category', 'Категория', 'select', { options: { loop: 'Петля', splice: 'Сращивание / обработка' } }),
    field('visual_type', 'Вид на схеме', 'select', { options: { aug_splice:'Петля', takling:'Обмотка', pilotauge:'Петля-проводник', endless_splice:'Замкнутое сращивание', shackle:'Скоба', kausche:'Коуш', exposed_eye:'Открытая петля', sewn_eye:'Прошитая петля', protection:'Защита', leather:'Кожа', friction_ring:'Кольцо', soft_shackle:'Мягкая скоба', generic:'Другое' } }),
    field('index', 'Порядок', 'number', { min:0, integer:true, required:true, default:0 }), active] },
  splice_materials: { title: 'Тарифные материалы', fields: [code, field('name', 'Название', 'text', { required:true })] },
  splice_prices: { title: 'Тарифы работ', fields: [field('splice_type_id','Вид работы','select',{source:'splice_types'}),
    field('splice_material_id','Тарифный материал','select',{source:'splice_materials'}),
    field('diameter_from_mm','Диаметр от, мм (пусто — без нижней границы)','number',{min:0,nullable:true}),
    field('diameter_to_mm','Диаметр до, мм (пусто — без верхней границы)','number',{min:0,nullable:true}),price,active] },
  configurator_extras: { title:'Дополнительные опции', translated:true, description:true, separateIndex:true, fields:[code,price,
    field('billing_type','Начисление','select',{options:{fixed:'За заказ',per_item:'За изделие / работу',per_meter:'За метр каната'}}),order,active] },
  material_groups: { title:'Группы каталога', translated:true, separateIndex:true, fields:[code,order,active] },
  materials: { title:'Материалы каталога', translated:true, separateIndex:true, fields:[field('material_group_id','Группа','select',{source:'material_groups'}),code,order,active] },
  configurator_settings: { title:'Настройки расчёта', singleton:true, fields:[
    field('min_length_m','Минимальная длина, м','number',{min:0.01,required:true}),
    field('max_length_m','Максимальная длина, м','number',{min:0.01,required:true}),
    field('splice_allowance_until_mm','Граница диаметра для запаса, мм','number',{min:0.01,required:true}),
    field('splice_allowance_until_m','Запас до границы включительно, м','number',{min:0,required:true}),
    field('splice_allowance_over_m','Запас выше границы, м','number',{min:0,required:true}),
    field('urgent_surcharge_per_splice','Доплата за срочность одной работы, EUR','number',{min:0,required:true}),
    field('urgent_max_splices','Максимум срочных работ','number',{min:0,integer:true,required:true}),
    field('standard_turnaround_hours','Обычный срок, часов','number',{min:0,integer:true,required:true}),
    field('urgent_turnaround_hours','Срочный срок, часов','number',{min:0,integer:true,required:true}),
    field('vat_rate','НДС, %','number',{min:0,required:true}),field('vat_note','Примечание о НДС')] },
};

export function automaticConfigCode(section, values, items = []) {
  const names = ['name_eng', 'name_ger', 'name_rus', 'name'].map(key => String(values[key] || '').trim()).filter(Boolean);
  const sleeveNames = ['sleeve', 'protective sleeve', 'защитный рукав', 'schutzschlauch'];
  const chars = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya','ä':'ae','ö':'oe','ü':'ue','ß':'ss'};
  const name = names[0] || '';
  let base = section === 'configurator_extras' && names.some(value => sleeveNames.includes(value.toLowerCase())) ? 'sleeve'
    : [...name.toLowerCase()].map(char => chars[char] ?? char).join('').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,'');
  if (!base) base = 'item';
  const limit = section === 'material_groups' ? 50 : 100;
  base = base.slice(0, limit).replace(/_+$/,'');
  const used = new Set(items.map(item => String(item.code || '').toLowerCase()));
  let candidate = base, number = 2;
  while (used.has(candidate)) { const suffix = `_${number++}`; candidate = base.slice(0, limit - suffix.length).replace(/_+$/,'') + suffix; }
  return candidate;
}

export function configPayload(section, values, rules = [], id = null) {
  const schema = configSections[section]; const data = {};
  for (const f of schema.fields) {
    let value = values[f.name] ?? f.default;
    if (f.type === 'checkbox') value = Boolean(value);
    else if (f.type === 'number' || f.source) {
      if (value === '' || value == null) { if (f.nullable) value = null; else throw new Error(`Заполните «${f.label}».`); }
      else { value = Number(value); if (!Number.isFinite(value) || value < (f.min ?? (f.source ? 1 : 0)) || ((f.integer || f.source) && !Number.isInteger(value))) throw new Error(`Проверьте «${f.label}».`); }
    } else { value = String(value ?? '').trim(); if (f.required && !value) throw new Error(`Заполните «${f.label}».`); if(f.options && !(value in f.options)) throw new Error(`Проверьте «${f.label}».`); }
    if(f.maxLength && value.length>f.maxLength)throw new Error(`«${f.label}»: не более ${f.maxLength} символов.`);
    data[f.name] = value;
  }
  if (schema.translated) {
    data.translations = ['rus','eng','ger'].filter(locale => String(values[`name_${locale}`] || '').trim()).map(locale => ({locale,name:values[`name_${locale}`].trim(),...(schema.description ? {description:values[`description_${locale}`]?.trim() || null} : {})}));
    if (!data.translations.length) throw new Error('Заполните название хотя бы на одном языке.');
  }
  if (section === 'configurator_settings' && data.max_length_m < data.min_length_m) throw new Error('Максимальная длина меньше минимальной.');
  if (section === 'splice_prices') {
    const low = data.diameter_from_mm ?? -Infinity, high = data.diameter_to_mm ?? Infinity;
    if (low > high) throw new Error('Нижняя граница диаметра больше верхней.');
    if (data.is_active && rules.some(r => Number(r.id) !== Number(id) && r.is_active !== false
      && Number(r.splice_type_id) === data.splice_type_id && Number(r.splice_material_id) === data.splice_material_id
      && (r.diameter_from_mm == null ? -Infinity : Number(r.diameter_from_mm)) <= high
      && (r.diameter_to_mm == null ? Infinity : Number(r.diameter_to_mm)) >= low)) throw new Error('Диапазон пересекается с активным тарифом этой работы и материала. Границы включаются в диапазон.');
  }
  return data;
}
