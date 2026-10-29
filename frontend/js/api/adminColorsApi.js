import { apiClient } from './apiClient.js?v=20261027.10';
import { API_CONFIG } from './config.js?v=20261027.10';
const auth = { requiresAuth: true };
let listCache = null;
export const adminColorsApi = {
  list: ({refresh=false}={}) => {
    if(refresh || !listCache || Date.now()-listCache.at>30000) {
      const entry={at:Date.now()};
      entry.promise=apiClient.get('/colors',auth).catch(error=>{if(listCache===entry)listCache=null;throw error;});
      listCache=entry;
    }
    return listCache.promise;
  },
  detail: id => apiClient.get(`/colors/${Number(id)}`,auth),
  create: data => apiClient.post('/colors', data, auth),
  update: (id, data) => apiClient.patch(`/colors/${Number(id)}`, data, auth),
  remove: id => apiClient.delete(`/colors/${Number(id)}`, auth),
  removeTranslation: id => apiClient.delete(`/colors/translations/${Number(id)}`, auth),
  order: (id, index) => apiClient.patch(`/colors/${Number(id)}/index`, { new_index: index }, auth),
  orderLink: (id, index) => apiClient.patch(`/rope_product_colors/${Number(id)}/index`, { new_index: index }, auth),
  addTranslation: (id, data) => apiClient.post(`/colors/${Number(id)}/translations`, data, auth),
  updateTranslation: (id, data) => apiClient.patch(`/colors/translations/${Number(id)}`, data, auth),
  links: id => apiClient.get(`/rope_product_colors/by-product/${Number(id)}`,auth),
  attach: (productId, colorId) => apiClient.post('/rope_product_colors', { [API_CONFIG.CATALOG_V2 ? 'product_id' : 'rope_product_id']: Number(productId), color_id: Number(colorId) }, auth),
  detach: id => apiClient.delete(`/rope_product_colors/${Number(id)}`, auth),
};
for(const key of ['create','update','remove','removeTranslation','order','addTranslation','updateTranslation']) {
  const action=adminColorsApi[key];
  adminColorsApi[key]=async(...args)=>{listCache=null;try{return await action(...args);}finally{listCache=null;}};
}
