import { getLanguage, languages } from './locale.js?v=20261027.10';
import { translate } from './translate.js?v=20261027.10';
import '../seo/public.js?v=20261027.10';

// Public pages only. Admin keeps its own Russian interface.
export function initPublicLanguage() {
  const language = getLanguage();
  try { localStorage.setItem('rope_lang', language); } catch { /* Storage may be unavailable. */ }
  document.documentElement.lang = language;
  const legalPages = {Impressum:'imprint',Datenschutz:'privacy',AGB:'terms',Widerrufsbelehrung:'withdrawal','Versand & Zahlung':'shipping'};
  document.querySelectorAll('a[href="#"]').forEach(link=>{
    const text=link.textContent.trim();
    if(legalPages[text]) link.href=`/legal/?document=${legalPages[text]}`;
    else if(link.matches('[data-lang]')) return;
    else if(link.matches('.header__button,.mobile-menu__button')) link.href='/configurator/';
    else {link.removeAttribute('href');link.setAttribute('aria-disabled','true');link.title='Ссылка появится после добавления контактов.';}
  });
  // Keep keyboard focus inside the expanded mobile menu.
  document.addEventListener('keydown',event=>{
    const burger=document.querySelector('.burger[aria-expanded="true"]');
    const menu=document.getElementById('mobile-menu');
    if(!burger||!menu||menu.hidden)return;
    if(event.key==='Escape'){burger.focus();return;}
    if(event.key!=='Tab')return;
    const focusable=[burger,...menu.querySelectorAll('a[href],button:not(:disabled)')].filter(el=>el.getClientRects().length);
    const first=focusable[0],last=focusable.at(-1);
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}
    else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}
  },true);
  let dirty = false;
  document.addEventListener('input', event => { if(event.target.closest('form')) dirty = true; });
  document.querySelectorAll('.lang').forEach(list => {
    if (!list.querySelector('[data-lang="ru"]')) {
      const item = document.createElement('li');item.className='lang__item';
      item.innerHTML='<a class="lang__link" href="?lang=ru" hreflang="ru" lang="ru" data-lang="ru">RU</a>';
      list.prepend(item);
    }
  });
  document.querySelectorAll('[data-lang]').forEach(link => {
    const target = link.dataset.lang;
    if (!languages.includes(target)) return;
    const url = new URL(location.href);
    if(target==='de') url.searchParams.delete('lang'); else url.searchParams.set('lang',target);
    link.href = url.href;
    if(target===language) link.setAttribute('aria-current','true'); else link.removeAttribute('aria-current');
    link.addEventListener('click',event => {
      if(event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      if(target===language){event.preventDefault();return;}
      if(dirty && !window.confirm(translate('Сменить язык и сбросить заполненную форму?',language))) {event.preventDefault();return;}
      // Persist only after the new page opens. Cancelling beforeunload must not change the preference.
    });
  });
  const blocked = 'script,style,[data-no-translate],[translate="no"]';
  const attributes = ['aria-label','placeholder','title','alt'];
  const visit = node => {
    if(node.nodeType===Node.TEXT_NODE) {
      if(!node.parentElement || node.parentElement.closest(blocked+',textarea')) return;
      const translated=translate(node.nodeValue,language);
      if(translated!==node.nodeValue) node.nodeValue=translated;
      return;
    }
    if(node.nodeType!==Node.ELEMENT_NODE || node.matches(blocked)) return;
    for(const attribute of attributes) {
      if(!node.hasAttribute(attribute)) continue;
      const value=node.getAttribute(attribute), next=translate(value,language);
      if(next!==value) node.setAttribute(attribute,next);
    }
    if(node.matches('meta[name="description"]')) node.content=translate(node.content,language);
    if(node.matches('a[href]') && !node.matches('[data-lang]')) {
      const href=node.getAttribute('href');
      if(href && !href.startsWith('#')) {
        const url=new URL(href,location.href);
        if(url.origin===location.origin && /^\/(?:$|(?:catalog|category|configurator|b2b|b2c|legal)\/$)/.test(url.pathname)) {
          if(language==='de') url.searchParams.delete('lang'); else url.searchParams.set('lang',language);
          const next=url.pathname+url.search+url.hash;
          if(href!==next) node.setAttribute('href',next);
        }
      }
    }
    for(const child of node.childNodes) visit(child);
  };
  visit(document.documentElement);
  // Dynamic views replace their text nodes after API responses. Translate those nodes only.
  const observer = new MutationObserver(records => {
    const pending=new Set();
    for(const record of records) {
      if(record.type==='childList') record.addedNodes.forEach(node=>pending.add(node));
      else pending.add(record.target);
    }
    pending.forEach(visit);
  });
  observer.observe(document.documentElement,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:attributes});
}

if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',initPublicLanguage,{once:true});
else initPublicLanguage();
