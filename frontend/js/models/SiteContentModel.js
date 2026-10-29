// Stable block codes are shared by the public renderer and the admin editor.
export const contentPages = { home:'Главная', b2b:'Бизнесу', b2c:'Частным клиентам', catalog:'Каталог' };
export const contentSlots = [
  {page:'home',code:'home_about',label:'О нас — заголовок и подзаголовок',title:'#about-title',content:'.about__subtitle'},
  ...['home','b2b'].flatMap(page=>[1,2,3,4].map(i=>({page,code:`${page}_service_${i}`,label:`Преимущество ${i}`,title:`.showcase__item:nth-child(${i}) .showcase__title`,content:`.showcase__item:nth-child(${i}) .showcase__text`}))),
  {page:'home',code:'home_charity',label:'Благотворительность — вступление',title:'.charity__lead',content:'.charity__text'},
  {page:'home',code:'home_charity_detail',label:'Благотворительность — пояснение',content:'.charity__text + .charity__text'},
  {page:'b2b',code:'b2b_heading',label:'Заголовок страницы',title:'.page-head__title'},
  {page:'b2b',code:'b2b_services',label:'Заголовок услуг',title:'#services-title'},
  {page:'b2c',code:'b2c_heading',label:'Заголовок страницы',title:'.page-head__title'},
  {page:'b2c',code:'b2c_selection',label:'Заголовок выбора изделия',title:'#selection h2'},
  ...[1,2,3].map(i=>({page:'b2c',code:`b2c_choice_${i}`,label:`Вариант изделия ${i}`,title:`.audience-choice:nth-child(${i}) h3`,content:`.audience-choice:nth-child(${i}) p`})),
  {page:'catalog',code:'catalog_heading',label:'Заголовок каталога',title:'#page-title'},
  {page:'catalog',code:'catalog_gallery',label:'Заголовок галереи',title:'#work-gallery-title'},
  {page:'b2b',code:'b2b_works',label:'Заголовок примеров работ',title:'section:has(.audience-works) h2'},
  {page:'b2b',code:'b2b_cooperation',label:'Сотрудничество — вступление',title:'.audience-cooperation h2',content:'.audience-cooperation > div > p'},
  ...[1,2,3].map(i=>({page:'b2b',code:`b2b_cooperation_${i}`,label:`Сотрудничество — вариант ${i}`,title:`.audience-cooperation__list article:nth-child(${i}) h3`,content:`.audience-cooperation__list article:nth-child(${i}) p`})),
  {page:'b2b',code:'b2b_catalog',label:'Переход в каталог — заголовок',title:'.audience-catalog-link h2'},
  ...['b2b','b2c'].map(page=>({page,code:`${page}_contact_intro`,label:'Контактный блок — вступление',title:'.audience-contact h2',content:'.audience-contact > div > p:not([data-channel-status])'})),
  {page:'b2c',code:'b2c_details',label:'Детали изделий — заголовок',title:'section:has(.audience-details) h2'},
  ...[1,2].map(i=>({page:'b2c',code:`b2c_detail_${i}`,label:`Детали изделий — пример ${i}`,title:`.audience-details figure:nth-child(${i}) h3`,content:`.audience-details figure:nth-child(${i}) p`})),
  {page:'b2c',code:'b2c_help',label:'Помощь с выбором',title:'.audience-details__help h3',content:'.audience-details__help p'},
  {page:'b2c',code:'b2c_process',label:'Порядок заказа — заголовок',title:'section:has(.audience-process) h2'},
  ...[1,2,3,4].map(i=>({page:'b2c',code:`b2c_process_${i}`,label:`Порядок заказа — шаг ${i}`,title:`.audience-process li:nth-child(${i}) h3`,content:`.audience-process li:nth-child(${i}) p`})),
];
export const gallerySections = {work_photos:'Галерея работ',charity_photos:'Благотворительность'};
export function contentPayload(slot,values) {
  return {page_code:slot.page,is_active:Boolean(values.is_active),translations:['rus','eng','ger'].map(locale=>({locale,
    ...(slot.title ? {title:String(values[`title_${locale}`]||'').trim()} : {}),
    ...(slot.content ? {content:String(values[`content_${locale}`]||'').trim()} : {}),
  }))};
}
export function galleryPayload(values) {
  const index=Number(values.index);
  if(values.index===''||!Number.isInteger(index)||index<0)throw new Error('Укажите целый неотрицательный порядок фотографии.');
  return {index,is_active:Boolean(values.is_active),translations:['rus','eng','ger'].map(locale=>({locale,
    title:String(values[`title_${locale}`]||'').trim(),description:String(values[`content_${locale}`]||'').trim(),
  }))};
}
