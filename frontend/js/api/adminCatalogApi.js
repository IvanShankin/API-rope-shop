import { apiClient as client } from './apiClient.js?v=20261027.10';
const auth = { requiresAuth: true };
const normalize = p => ({ ...p, product_id: p.id, construction: p.name || p.translations?.[0]?.name,
  variants: (p.variants || []).map(v => ({ ...v, diameter_mm: v.size_value, price_per_meter: v.price, weight_g_per_m: v.weight_g })) });

// Admin reads retain inactive records. Public adapters intentionally hide them.
export const adminCatalogApi = {
  async list() { const result = await client.get('/products', {...auth,params:{locale:'rus',product_type:'rope'}}); return result.items.filter(p=>p.price_unit==='meter').map(normalize); },
  async detail(id) {
    const product = await client.get(`/products/${Number(id)}`,auth);
    let settings = null;
    try { settings = await client.get(`/rope_products/${Number(id)}`,auth); } catch(e) { if(e.status!==404) throw e; }
    return { ...normalize(product), ...(settings || {}), variants: normalize(product).variants, hasRopeSettings: Boolean(settings) };
  },
  async categories() { return (await client.get('/categories',{...auth,params:{locale:'rus'}})).items; },
  async saveProduct(id, data, onCommitted = () => {}) {
    const { translations, index, settings, ...fields } = data;
    let saved;
    if (id) {
      const current = await client.get(`/products/${Number(id)}`,auth);
      if (current.translations.some(t => !translations.some(next => next.locale === t.locale))) {
        throw new Error('Пустое название не удаляет перевод. Заполните существующие названия.');
      }
      const changed=Object.fromEntries(Object.entries(fields).filter(([key,value])=>current[key]!==value));
      saved = Object.keys(changed).length ? await client.patch(`/products/${Number(id)}`, changed, auth) : current;
    } else saved = await client.post('/products', {...fields, index, translations}, auth);
    // Preserve a committed base ID before secondary writes; retries update this product.
    id = saved.id;
    onCommitted({ ...normalize(saved), product_id: id });
    if(Number(saved.index)!==index) await client.patch(`/products/${id}/index`,{new_index:index},auth);
    const fresh = Array.isArray(saved.translations) ? saved : await client.get(`/products/${id}`,auth);
    for (const t of translations) {
      const old = fresh.translations.find(x=>x.locale===t.locale);
      const {locale,...values} = t;
      if(old) {
        if(Object.entries(values).some(([key,value])=>(old[key]||'')!==(value||'')))await client.patch(`/products/translations/${old.id}`,values,auth);
      } else await client.post(`/products/${id}/translations`,t,auth);
    }
    let currentSettings = null;
    try { currentSettings = await client.get(`/rope_products/${id}`,auth); } catch(e) { if(e.status!==404) throw e; }
    if(currentSettings) {
      const changed=Object.fromEntries(Object.entries(settings).filter(([key,value])=>currentSettings[key]!==value));
      if(Object.keys(changed).length)await client.patch(`/rope_products/${id}`, changed, auth);
    }
    else await client.post('/rope_products',{...settings,product_id:id},auth);
    return this.detail(id);
  },
  removeProduct: id => client.delete(`/products/${Number(id)}`,auth),
  upload(id,file) { const data=new FormData();data.append('product_id',id);data.append('file',file);return client.post('/product_images/upload',data,auth); },
  mainImage: id => client.patch(`/product_images/${Number(id)}/main`,{},auth),
  removeImage: id => client.delete(`/product_images/${Number(id)}`,auth),
};
