import {contentSlots} from '../../models/SiteContentModel.js?v=20261116.1';
import {siteContentApi as api} from '../../api/siteContentApi.js?v=20261116.1';
import {apiLocale} from '../../i18n/locale.js?v=20261116.1';
import {escapeHtml as esc} from '../../utils/text.js?v=20261116.1';
import {mediaUrl} from '../../utils/media.js?v=20261116.1';
import {translate as t} from '../../i18n/translate.js?v=20261116.1';

export function renderBlocks(page,blocks,root=document) {
  for(const slot of contentSlots.filter(s=>s.page===page)) {
    const block=blocks.find(b=>b.block_code===slot.code&&b.is_active!==false);
    if(!block)continue;
    for(const field of ['title','content']) {
      const target=slot[field]&&root.querySelector(slot[field]);
      if(target&&block[field]!=null) {target.setAttribute('data-no-translate','');target.textContent=block[field];target.style.whiteSpace='pre-line';}
    }
  }
}
export function photoMarkup(photos,kind,layout=kind==='work_photos'?'grid':'slider') {
  return photos.filter(p=>p.is_active!==false && mediaUrl(p.image_url)).sort((a,b)=>a.index-b.index).map(p=>{
    const title=p.title||t('Фотография');const url=esc(mediaUrl(p.image_url));
    return layout==='grid'
      ? `<button class="work-gallery__photo" type="button" data-no-translate aria-label="${esc(title)}" data-description="${esc(p.description||'')}"><img src="${url}" alt="${esc(title)}" loading="lazy" width="1280" height="960"><span class="work-gallery__caption">${esc(title)}</span></button>`
      : `<figure class="gallery__slide" data-no-translate><img class="gallery__image" src="${url}" alt="${esc(title)}" loading="lazy"><figcaption class="gallery__caption"><span class="gallery__caption-title">${esc(title)}</span><span class="gallery__caption-meta">${esc(p.description||'')}</span></figcaption></figure>`;
  }).join('');
}
export async function initSiteContent({initWork,initSwiper}) {
  const path=location.pathname.replace(/\.html$/,'').replace(/\/$/,'');
  // Тексты благотворительности хранятся в блоках главной (home_charity*), поэтому /charity/ берёт их оттуда.
  const page=({'':'home','/index':'home','/b2b':'b2b','/b2c':'b2c','/catalog':'catalog','/charity':'home','/charity/index':'home'})[path];
  const jobs=[];
  if(page)jobs.push(api.blocks(page,apiLocale()).then(blocks=>renderBlocks(page,blocks)).catch(()=>{
    // Keep the existing translated layout when the text service is unavailable.
    console.warn('Тексты из API не загружены; показан текст макета.');
  }));
  // Плитки с просмотром (.work-gallery) — раздел из data-gallery-section (по умолчанию «Галерея работ»);
  // карусель .charity__gallery осталась для совместимости со старой главной.
  for(const [selector,defaultKind,layout] of [['.work-gallery','work_photos','grid'],['.charity__gallery','charity_photos','slider']]) {
    const root=document.querySelector(selector);if(!root)continue;
    const kind=root.dataset.gallerySection||defaultKind;
    const grid=root.querySelector(layout==='grid'?'.work-gallery__grid':'.gallery__track');
    grid.replaceChildren();
    const status=document.createElement('p');status.className='content-load-status';status.setAttribute('role','status');root.append(status);
    const controls=[...root.querySelectorAll('[data-gallery-more],.gallery__button')];controls.forEach(el=>el.hidden=true);
    const load=async()=>{
      status.textContent=t('Загружаем фотографии…');
      try {
        const photos=await api.photos(kind,apiLocale());
        grid.innerHTML=photoMarkup(photos,kind,layout);
        if(!grid.children.length){status.remove();root.hidden=true;return;}
        status.remove();
        if(layout==='grid'){controls.forEach(el=>el.hidden=false);initWork(root);}
        else {controls.forEach(el=>el.hidden=grid.children.length<2);initSwiper(root);}
      }catch{
        status.textContent=t('Не удалось загрузить фотографии.');
        const retry=document.createElement('button');retry.type='button';retry.className='button button--ghost';retry.textContent=t('Повторить');retry.addEventListener('click',load,{once:true});status.append(' ',retry);
      }
    };
    jobs.push(load());
  }
  await Promise.allSettled(jobs);
}
