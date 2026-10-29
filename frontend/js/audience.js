import {contactsApi} from './api/contactsApi.js?v=20261027.10';
import {translate as t} from './i18n/translate.js?v=20261027.10';
/* Public inquiries use the existing contact_requests contract. */
(() => {
  'use strict';
  const tabs = document.querySelectorAll('[data-service-image]');
  const photo = document.querySelector('[data-service-photo]');
  tabs.forEach(button => button.addEventListener('click', () => {
    tabs.forEach(tab => {
      const active = tab === button;
      tab.classList.toggle('audience-service--active', active);
      tab.setAttribute('aria-pressed', String(active));
    });
    photo.src = button.dataset.serviceImage;
    photo.alt = 'Пример ручной работы с канатом';
  }));
  document.querySelectorAll('[data-preview-contact]').forEach(button => button.addEventListener('click', () => {
    document.querySelector('[data-channel-status]').textContent = 'Контакт будет подключён после добавления реквизитов. Сейчас открыт макет страницы.';
  }));
  document.querySelectorAll('.audience-form').forEach(form => {
    let busy=false,sent=false,uncertain=false;
    const submit=form.querySelector('[type=submit]');
    form.querySelectorAll('[name=name],[name=email],[name=company]').forEach(input=>input.maxLength=255);
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if(busy||sent||uncertain)return;
      if (!form.reportValidity()) return;
      let status = form.querySelector('[role="status"]');
      if (!status) {
        status = document.createElement('p');
        status.setAttribute('role', 'status');
        status.className = 'audience-form__status';
        form.append(status);
      }
      const values=Object.fromEntries(new FormData(form));
      const data={name:values.name.trim(),email:values.email.trim(),
        message:[location.pathname.includes('b2b')?'B2B':'B2C',values.company?.trim(),values.message.trim()].filter(Boolean).join('\n\n')};
      if(!data.name||!values.message.trim()){status.textContent=t('Заполните имя и описание задачи.');return;}
      busy=true;submit.disabled=true;form.setAttribute('aria-busy','true');status.textContent=t('Отправляем обращение…');
      try{
        const response=await contactsApi.submit(data);
        sent=true;
        status.textContent=response?.id?t('Обращение принято. Мы свяжемся с вами по указанному email.'):t('Ответ не подтверждён. Обращение могло сохраниться; уточните результат перед повторной отправкой.');
      }catch(error){
        uncertain=!error.status||error.status>=500;
        status.textContent=t(uncertain?'Ответ не подтверждён. Обращение могло сохраниться; уточните результат перед повторной отправкой.':'Не удалось отправить обращение. Проверьте поля и повторите позже.');
      }finally{busy=false;submit.disabled=sent||uncertain;form.setAttribute('aria-busy','false');}
    });
  });
})();
