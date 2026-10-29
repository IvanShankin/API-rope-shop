import { apiClient as client } from './apiClient.js?v=20261027.10';
import { API_CONFIG } from './config.js?v=20261027.10';
import { adminCatalogApi } from './adminCatalogApi.js?v=20261027.10';
const auth = { requiresAuth:true };
export const adminConfigApi = {
  list: async (section,params) => {
    if(API_CONFIG.CATALOG_V2 && section==='rope_products') return adminCatalogApi.list();
    const result=await client.get(`/${section}`,{...auth,params});
    return section==='categories' ? result.items : result;
  },
  detail: (section,id) => client.get(`/${section}/${Number(id)}`,auth),
  save: (section,id,data,singleton=false) => singleton ? client.patch(`/${section}`,data,auth)
    : id ? client.patch(`/${section}/${Number(id)}`,data,auth) : client.post(`/${section}`,data,auth),
  translation: (section,id,translation) => translation.id
    ? client.patch(`/${section}/translations/${Number(translation.id)}`,{name:translation.name,...('description' in translation ? {description:translation.description} : {})},auth)
    : client.post(`/${section}/${Number(id)}/translations`,translation,auth),
  links: id => client.get(`/rope_allowed_splices/by-product/${Number(id)}`,auth),
  order: (section,id,index) => client.patch(`/${section}/${Number(id)}/index`,{new_index:index},auth),
  remove: (section,id) => client.delete(`/${section}/${Number(id)}`,auth),
  removeTranslation: (section,id) => client.delete(`/${section}/translations/${Number(id)}`,auth),
  removeImage: (id,section='splice_types') => client.delete(`/${section}/${Number(id)}/image`,auth),
  saveLinks: (id,ids) => client.request(`/rope_allowed_splices/by-product/${Number(id)}`,{...auth,method:'PUT',data:{splice_type_ids:ids}}),
  upload: (id,file,section='splice_types') => { const data = new FormData(); data.append('file',file); return client.post(`/${section}/${Number(id)}/image`,data,auth); },
};
