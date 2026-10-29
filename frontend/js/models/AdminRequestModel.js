export const requestStatuses = {new:'Новая',in_progress:'В работе',confirmed:'Подтверждена',completed:'Завершена',cancelled:'Отменена'};

export class AdminRequestModel {
  static payload(values, original = {}) {
    const data = {};
    for(const key of ['name','email','phone','comment'])data[key]=String(values[key]??'').trim();
    if(!data.name||data.name.length>255)throw new Error('Укажите имя длиной до 255 символов.');
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email))throw new Error('Проверьте email.');
    if(data.phone.length>100)throw new Error('Телефон длиннее 100 символов.');
    data.phone=data.phone||null;data.comment=data.comment||null;
    if (Object.hasOwn(values, 'status')) {
      data.status=values.status;
      if(!Object.hasOwn(requestStatuses,data.status))throw new Error('Выберите статус заявки.');
    }
    if(String(values.total_price??'').trim()==='')throw new Error('Укажите итоговую сумму.');
    data.total_price=Number(values.total_price);
    if(!Number.isFinite(data.total_price)||data.total_price<0)throw new Error('Сумма должна быть неотрицательным числом.');
    data.is_urgent=Boolean(values.is_urgent);
    // Send only edited fields; omitted fields remain unchanged on the server.
    return Object.fromEntries(Object.entries(data).filter(([key,value])=>key==='total_price'?value!==Number(original[key]):value!==(original[key]??null)));
  }
}
