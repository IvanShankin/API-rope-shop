import {API_CONFIG} from './api/config.js?v=20261027.10';
import {getLanguage} from './i18n/locale.js?v=20261027.10';
import {escapeHtml as esc} from './utils/text.js?v=20261027.10';

const words = {
  ru: ['Ваша заявка','Сохраните ссылку. Она открывает доступ к вашей заявке — передавайте её только доверенным людям.','Загружаем заявку…','Повторить','К услугам и конфигуратору','Ссылка неполная. Откройте полную ссылку, полученную после отправки заявки.','Заявка недоступна. Проверьте ссылку или обратитесь к менеджеру.','Не удалось загрузить заявку. Попробуйте позже.','Номер','Статус','Сумма','Дата','Канаты','Услуги','Дополнительные опции','Комментарий','Стоимость и срок подтвердит менеджер.'],
  en: ['Your enquiry','Save this link. It gives access to your enquiry; share it only with people you trust.','Loading enquiry…','Retry','Services and configurator','This link is incomplete. Open the full link received after submitting your enquiry.','Enquiry unavailable. Check the link or contact our team.','Could not load the enquiry. Please try later.','Number','Status','Total','Date','Ropes','Services','Extra options','Comment','Our team will confirm the final price and delivery time.'],
  de: ['Ihre Anfrage','Speichern Sie diesen Link. Er ermöglicht den Zugriff auf Ihre Anfrage. Teilen Sie ihn nur mit vertrauenswürdigen Personen.','Anfrage wird geladen…','Erneut versuchen','Leistungen und Konfigurator','Dieser Link ist unvollständig. Öffnen Sie den vollständigen Link, den Sie nach dem Absenden erhalten haben.','Anfrage nicht verfügbar. Prüfen Sie den Link oder kontaktieren Sie uns.','Die Anfrage konnte nicht geladen werden. Bitte versuchen Sie es später.','Nummer','Status','Summe','Datum','Seile','Leistungen','Zusatzoptionen','Kommentar','Unser Team bestätigt den endgültigen Preis und den Liefertermin.'],
};
const language = getLanguage();
const t = words[language];
const statuses = {
  ru: {new:'Новая',in_progress:'В работе',confirmed:'Подтверждена',completed:'Завершена',cancelled:'Отменена'},
  en: {new:'New',in_progress:'In progress',confirmed:'Confirmed',completed:'Completed',cancelled:'Cancelled'},
  de: {new:'Neu',in_progress:'In Bearbeitung',confirmed:'Bestätigt',completed:'Abgeschlossen',cancelled:'Storniert'},
};
document.documentElement.lang = language;
document.title = `${t[0]} — Rope-Pro-Line`;
const select = name => document.querySelector(`[data-tracking-${name}]`);
for (const [key,index] of [['title',0],['note',1],['retry',3],['back',4]]) select(key).textContent = t[index];
const requestNumber = decodeURIComponent(location.pathname.split('/')[2] || '');
const token = new URLSearchParams(location.search).get('token');
let busy = false;

async function load() {
  if (busy) return;
  const status = select('status');
  select('content').hidden = true;
  select('retry').hidden = true;
  if (!requestNumber || !token) {status.textContent = t[5]; return;}
  busy = true; status.textContent = t[2];
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}/quote_requests/number/${encodeURIComponent(requestNumber)}?${new URLSearchParams({token})}`, {signal:controller.signal, cache:'no-store', referrerPolicy:'no-referrer'});
    if (!response.ok) throw Object.assign(new Error(), {status:response.status});
    const quote = await response.json();
    const money = value => `${Number(value).toFixed(2)} ${quote.currency}`;
    const list = (title,items,describe) => items?.length ? `<h2>${esc(title)}</h2><ul>${items.map(item=>`<li>${esc(describe(item))}</li>`).join('')}</ul>` : '';
    const summary = [[t[8],quote.request_number],[t[9],statuses[language][quote.status] || quote.status],[t[10],money(quote.total_price)],[t[11],new Date(quote.created_at).toLocaleDateString(language)]];
    select('content').innerHTML = `<dl class="tracking__summary">${summary.map(([key,value])=>`<dt>${esc(key)}</dt><dd>${esc(value)}</dd>`).join('')}</dl>
      ${list(t[12],quote.rope_items,item=>[item.product_name_snapshot,item.color_name_snapshot,`${item.diameter_mm} mm · ${item.length_m} m × ${item.quantity}`,item.end_a_name_snapshot,item.end_b_name_snapshot,money(item.total_cost)].filter(Boolean).join(' · '))}
      ${list(t[13],quote.service_items,item=>[item.service_name_snapshot,item.material_name_snapshot,`${item.diameter_mm} mm × ${item.quantity}`,money(item.total_cost)].filter(Boolean).join(' · '))}
      ${list(t[14],quote.extra_items,item=>`${item.name_snapshot} × ${item.quantity} · ${money(item.total_cost)}`)}
      ${quote.comment ? `<h2>${esc(t[15])}</h2><p>${esc(quote.comment)}</p>` : ''}<p>${esc(t[16])}</p>`;
    select('content').hidden = false; status.textContent = '';
  } catch (error) {
    status.textContent = [403,404].includes(error.status) ? t[6] : t[7];
    select('retry').hidden = [403,404].includes(error.status);
  } finally {clearTimeout(timer); busy = false;}
}
select('retry').addEventListener('click', load);
load();
