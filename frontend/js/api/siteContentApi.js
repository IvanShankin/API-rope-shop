import {apiClient as client} from './apiClient.js?v=20261027.10';
const auth={requiresAuth:true};
export const siteContentApi = {
  blocks:(page,locale,admin=false)=>client.get(`/content_blocks/page/${encodeURIComponent(page)}`,{requiresAuth:admin,params:{locale,...(!admin?{is_active:true}:{})}}),
  saveBlock:(code,data)=>client.request(`/content_blocks/${encodeURIComponent(code)}`,{...auth,method:'PUT',data}),
  photos:(section,locale,admin=false)=>client.get(`/${section}`,{requiresAuth:admin,params:{locale,...(!admin?{is_active:true}:{})}}),
  photo:(section,id)=>client.get(`/${section}/${Number(id)}`,auth),
  async savePhoto(section,id,data,file,onCommitted=()=>{}) {
    let fresh;
    if(!id) {
      if(!file)throw new Error('Выберите фотографию.');
      const body=new FormData();body.set('file',file);body.set('is_active',data.is_active);body.set('index',data.index);
      body.set('locale','rus');body.set('title',data.translations[0].title);body.set('description',data.translations[0].description);
      const created=await client.post(`/${section}`,body,auth);id=created.id;onCommitted(created);
      fresh=await this.photo(section,id);
    } else {
      fresh=await this.photo(section,id);
      if(fresh.is_active!==data.is_active)await client.patch(`/${section}/${id}`,{is_active:data.is_active},auth);
      if(file) {const body=new FormData();body.set('file',file);await client.post(`/${section}/${id}/upload-image`,body,auth);}
    }
    if(Number(fresh.index)!==data.index)await client.patch(`/${section}/${id}/index`,{new_index:data.index},auth);
    for(const t of data.translations) {
      const existing=fresh.translations.find(x=>x.locale===t.locale);
      const {locale,...fields}=t;
      if(existing) {
        if(Object.entries(fields).some(([key,value])=>(existing[key]||'')!==(value||'')))await client.patch(`/${section}/${id}/translations/${existing.id}`,fields,auth);
      } else if(t.title||t.description)await client.post(`/${section}/${id}/translations`,t,auth);
    }
    return this.photo(section,id);
  },
  removePhoto:(section,id)=>client.delete(`/${section}/${Number(id)}`,auth),
};
