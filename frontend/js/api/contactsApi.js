import {apiClient as client} from './apiClient.js?v=20261106.1';
import {API_CONFIG} from './config.js?v=20261106.1';
const company = data => ({name:data.company_name,email:data.contact_email,phone:data.contact_phone});
export const contactsApi={
  submit:data=>client.post('/contact_requests',data),
  listRequests:(offset=0)=>client.get('/contact_requests',{requiresAuth:true,params:{offset,limit:25}}),
  async get(){
    if (!API_CONFIG.PUBLIC_CONTACTS_URL) return null;
    const data=await client.get(API_CONFIG.PUBLIC_CONTACTS_URL);
    if (!data || Array.isArray(data) || typeof data!=='object') throw new Error('Некорректные публичные реквизиты.');
    // /settings/public uses settings field names; the site shows only phone and email (the brand is already in the logo).
    return {email:data.contact_email||data.email||'',phone:data.contact_phone||data.phone||''};
  },
  getAdmin:async()=>company(await client.get('/settings',{requiresAuth:true})),
  save:async data=>company(await client.patch('/settings',{
    company_name:data.name,contact_email:data.email,contact_phone:data.phone,
  },{requiresAuth:true})),
};
