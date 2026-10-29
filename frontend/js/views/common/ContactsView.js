import {contactsApi as api} from '../../api/contactsApi.js?v=20261027.10';
import {contactLinks} from '../../models/ContactsModel.js?v=20261027.10';
import {translate as t} from '../../i18n/translate.js?v=20261027.10';
export function renderContacts(data,root=document){
  const links=contactLinks(data);
  for(const kind of ['phone','email'])for(const el of root.querySelectorAll(`[data-site-contact="${kind}"]`)){
    el.textContent=data[kind]||'';el.setAttribute('data-no-translate','');
    el.hidden=!links[kind];
    if(links[kind]){el.setAttribute('href',links[kind]);el.removeAttribute('aria-disabled');el.removeAttribute('title');}
    else el.removeAttribute('href');
  }
  for(const el of root.querySelectorAll('[data-site-contact="message"]')){el.textContent=data.message||'';el.hidden=!data.message;el.setAttribute('data-no-translate','');}
  for(const el of root.querySelectorAll('[data-site-contact="name"]')){el.textContent=data.name||'';el.hidden=!data.name;el.setAttribute('data-no-translate','');}
}
export function initContacts(){
  if(document.querySelector('.admin')||document.querySelector('[data-contacts-status]'))return;
  document.querySelectorAll('a[href^="tel:"],a[href^="mailto:"]').forEach(el=>{
    el.dataset.siteContact=el.getAttribute('href').startsWith('tel:')?'phone':'email';el.hidden=true;el.removeAttribute('href');
  });
  const footer=document.querySelector('.footer__title')?.closest('.footer')||document.querySelector('footer');
  const mail=document.querySelector('.footer [data-site-contact="email"]');
  const target=mail?.closest('.footer__col')||mail?.closest('ul')?.parentElement||footer;
  if(target){
    for(const kind of ['name','message']){const p=document.createElement('p');p.className='site-contact-text';p.dataset.siteContact=kind;p.hidden=true;target.append(p);}
  }
  const channels=document.querySelector('.audience-contact__channels');
  if(channels){
    channels.replaceChildren();
    for(const kind of ['phone','email']){const a=document.createElement('a');a.dataset.siteContact=kind;a.hidden=true;channels.append(a);}
    const text=document.createElement('p');text.dataset.siteContact='message';text.className='site-contact-text';text.hidden=true;channels.before(text);
  }
  const status=document.createElement('p');status.dataset.contactsStatus='';status.className='site-contact-status';status.setAttribute('role','status');(target||document.body).append(status);
  let busy=false;
  const load=async()=>{
    if(busy)return;busy=true;status.textContent=t('Загружаем контакты…');
    try{const contacts=await api.get();if(contacts)renderContacts(contacts);status.textContent='';}
    catch{status.textContent=t('Не удалось загрузить контакты.');const retry=document.createElement('button');retry.type='button';retry.className='button button--ghost button--small';retry.textContent=t('Повторить');retry.addEventListener('click',load);status.append(' ',retry);}
    finally{busy=false;}
  };
  return load();
}
