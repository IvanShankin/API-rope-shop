export function contactLinks(data){
  const phone=String(data.phone||'').trim();const email=String(data.email||'').trim();
  const digits=phone.replace(/[ ()\-.]/g,'');
  return {phone:/^\+?\d{5,20}$/.test(digits)?`tel:${digits}`:'',email:/^[^\s@?&#%]+@[^\s@?&#%]+\.[^\s@?&#%]+$/.test(email)?`mailto:${email}`:''};
}
export function contactPayload(v){
  const data={name:String(v.name||'').trim(),phone:String(v.phone||'').trim()||null,email:String(v.email||'').trim(),message:String(v.message||'').trim()||null};
  const links=contactLinks(data);
  if(!data.name||data.name.length>255)throw new Error('Укажите название (до 255 символов).');
  if(!links.email||data.email.length>255)throw new Error('Укажите корректный email.');
  if(data.phone&&!links.phone)throw new Error('Укажите телефон цифрами; допустимы +, пробелы, скобки и дефисы.');
  return data;
}
