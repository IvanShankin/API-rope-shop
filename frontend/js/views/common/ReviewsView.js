import {reviewsApi as api} from '../../api/reviewsApi.js?v=20261027.10';
import {apiLocale} from '../../i18n/locale.js?v=20261027.10';
import {translate as t} from '../../i18n/translate.js?v=20261027.10';
import {escapeHtml as esc} from '../../utils/text.js?v=20261027.10';
export function reviewMarkup(items){
  return items.filter(r=>(r.status===undefined||r.status==='confirmed')&&r.is_published!==false).sort((a,b)=>a.index-b.index||a.id-b.id).map(r=>`<article class="review-card" data-no-translate>
    ${r.rating?`<p class="review-card__rating" aria-label="${r.rating} / 5">${'★'.repeat(r.rating)}${'☆'.repeat(5-r.rating)} <span>${r.rating} / 5</span></p>`:''}
    <p class="review-card__text">${esc(r.text||'')}</p><p class="review-card__meta">${esc(r.author_name)}</p></article>`).join('');
}
export function initReviews(){
  const root=document.querySelector('#reviews');if(!root)return;
  const list=root.querySelector('.reviews__list');list.replaceChildren();
  const status=document.createElement('p');status.setAttribute('role','status');list.before(status);
  let loading=false;
  async function load(){
    if(loading)return;loading=true;list.setAttribute('aria-busy','true');
    try{
      const result=await api.list(apiLocale());
      list.innerHTML=reviewMarkup(result.items);
      list.hidden=!list.children.length;
      status.textContent='';
    }
    catch{
      list.hidden=true;
      status.textContent='';
    }
    finally{loading=false;list.setAttribute('aria-busy','false');}
  }
  const box=document.createElement('section');box.className='review-form';box.setAttribute('aria-labelledby','review-form-title');
  box.innerHTML=`<h3 id="review-form-title" class="review-form__title">${esc(t('Оставить отзыв'))}</h3><form>
    <label>${esc(t('Ваше имя'))}<input name="author_name" autocomplete="name" maxlength="255" required></label>
    <fieldset class="review-rating"><legend>${esc(t('Оценка'))}</legend><div class="review-rating__stars">${[1,2,3,4,5].map(n=>`<label class="review-rating__star"><input type="radio" name="rating" value="${n}" aria-label="${n} / 5" required><span aria-hidden="true">★</span></label>`).join('')}</div></fieldset>
    <label>${esc(t('Текст отзыва'))}<textarea name="text" rows="5" required></textarea></label>
    <label class="review-form__consent"><input type="checkbox" name="consent" required> <span>${esc(t('Согласен на публикацию имени и отзыва и обработку данных.'))} <a href="/legal/?document=privacy">Datenschutz</a></span></label>
    <button class="button button--primary" type="submit">${esc(t('Отправить отзыв'))}</button><p role="status" data-review-status></p></form>`;
  list.after(box);const form=box.querySelector('form');const message=form.querySelector('[data-review-status]');let sending=false;let sent=false;
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(sending||sent||!form.reportValidity())return;
    const values=new FormData(form);const data={author_name:values.get('author_name').trim(),text:values.get('text').trim(),rating:Number(values.get('rating')),locale:apiLocale()};
    if(!data.author_name||!data.text){message.textContent=t('Заполните имя и текст отзыва.');return;}
    sending=true;const button=form.querySelector('button');button.disabled=true;message.textContent=t('Отправляем отзыв…');
    try{await api.create(data);sent=true;form.querySelectorAll('input,textarea,select').forEach(el=>el.disabled=true);message.dataset.state='success';message.textContent=t('Спасибо! Ваш отзыв будет опубликован только после модерации.');}
    catch(e){message.textContent=t(!e.status||e.status>=500?'Не удалось подтвердить отправку. Отзыв мог быть получен. Данные сохранены в форме; не отправляйте повторно сразу.':'Не удалось отправить отзыв. Проверьте поля и попробуйте снова.');}
    finally{sending=false;button.disabled=sent;}
  });
  load();
}
