import {apiClient as client} from './apiClient.js?v=20261027.10';
const auth={requiresAuth:true};
export const reviewsApi={
  async list(locale,admin=false) {
    const result = await client.get('/reviews',{requiresAuth:admin,params:{locale,...(!admin?{status:'confirmed',is_published:true}:{})}});
    if (!admin) return result;
    if (!result.items.length) return result;
    // The API omits moderation fields from list DTOs. Resolve membership with
    // three filtered lists, independent of review count; details load on select.
    const [pending,rejected,published]=await Promise.all([
      {status:'new'}, {status:'rejected'}, {status:'confirmed',is_published:true},
    ].map(params=>client.get('/reviews',{...auth,params:{locale,...params}})));
    const ids=list=>new Set(list.items.map(item=>item.id));
    const pendingIds=ids(pending), rejectedIds=ids(rejected), publishedIds=ids(published);
    return {...result,items:result.items.map(item=>({...item,
      status:pendingIds.has(item.id)?'new':rejectedIds.has(item.id)?'rejected':'confirmed',
      is_published:publishedIds.has(item.id),translations:[{locale,text:item.text||''}],
    }))};
  },
  get:id=>client.get(`/reviews/${Number(id)}`,auth),
  create:data=>client.post('/reviews',data),
  remove:id=>client.delete(`/reviews/${Number(id)}`,auth),
  async save(id,data,onCreated=()=>{}) {
    const translations=data.translations.filter(t=>t.text);
    if(!id){const created=await this.create({author_name:data.author_name,rating:data.rating,...translations[0]});id=created.id;onCreated(created);}
    // Keep moderation/publication last: a failed translation must not publish a new review.
    const fresh=await this.get(id);
    for(const t of translations){
      const existing=fresh.translations.find(x=>x.locale===t.locale);
      if(existing && existing.text!==t.text)await client.patch(`/reviews/${id}/translations/${existing.id}`,{text:t.text},auth);
      else if(!existing)await client.post(`/reviews/${id}/translations`,t,auth);
    }
    for(const old of fresh.translations){
      if(!translations.some(t=>t.locale===old.locale))await client.delete(`/reviews/${id}/translations/${old.id}`,auth);
    }
    if(fresh.index!==data.index)await client.patch(`/reviews/${id}/index`,{new_index:data.index},auth);
    const fields={author_name:data.author_name,rating:data.rating,status:data.status,is_published:data.status==='confirmed'&&data.is_published};
    const changed=Object.fromEntries(Object.entries(fields).filter(([key,value])=>fresh[key]!==value));
    if(Object.keys(changed).length)await client.patch(`/reviews/${id}`,changed,auth);
    return this.get(id);
  }
};
