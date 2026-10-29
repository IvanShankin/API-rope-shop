import {getLanguage} from './i18n/locale.js?v=20261027.10';

// These are labels for unfinished templates, not final legal texts.
const labels = {
  de: {names:['Impressum','Datenschutzerklärung','Nutzungsbedingungen','Widerrufsbelehrung','Versand & Zahlung'], nav:'Rechtliche Dokumente', notice:'Vorlage — noch nicht veröffentlicht.', detail:'Die verbindlichen Texte und Angaben des Anbieters werden ergänzt. Diese Vorlage ist keine vollständige rechtliche Information.', placeholder:'Der abgestimmte Text wird hier ergänzt.', missing:'Dokument nicht gefunden', choose:'Bitte wählen Sie ein Dokument aus der Navigation.', sections:[
    ['Anbieter und Anschrift','Kontakt','Vertretung und Registerangaben','Umsatzsteuer-Identifikationsnummer','Verbraucherstreitbeilegung'],
    ['Verantwortlicher und Datenschutzkontakt','Hosting und Server-Protokolle','Kontaktanfragen und individuelle Angebote','Konfigurator und Anfragestatus','Bewertungen','Cookies und Browser-Speicher','Externe Dienste und Schriftarten','Empfänger und internationale Datenübermittlung','Speicherdauer und Löschung','Ihre Rechte und Beschwerdemöglichkeiten'],
    ['Anbieter und Geltungsbereich','Nutzung der Website und des Konfigurators','Anfrage, individuelles Angebot und Vereinbarung','Technische Angaben und bestimmungsgemäße Verwendung','Inhalte und Bewertungen','Gesetzliche Rechte und Kontakt'],
    ['Anwendungsbereich und Widerrufsrecht','Ausübung des Widerrufs','Folgen des Widerrufs','Individuell angefertigte Waren','Muster-Widerrufsformular'],
    ['Liefergebiet und Lieferzeiten','Versandkosten','Zahlungsarten und Fälligkeit']]},
  en: {names:['Legal notice','Privacy policy','Terms of use','Withdrawal information','Shipping & payment'], nav:'Legal documents', notice:'Draft — not yet published.', detail:'The provider’s final texts and details will be added. This draft is not complete legal information.', placeholder:'The agreed text will be added here.', missing:'Document not found', choose:'Please select a document from the navigation.', sections:[
    ['Provider and address','Contact','Representation and registration details','VAT identification number','Consumer dispute resolution'],
    ['Controller and data protection contact','Hosting and server logs','Contact enquiries and individual offers','Configurator and enquiry status','Reviews','Cookies and browser storage','External services and fonts','Recipients and international data transfers','Retention and deletion','Your rights and complaints'],
    ['Provider and scope','Use of the website and configurator','Enquiry, individual offer and agreement','Technical information and intended use','Content and reviews','Statutory rights and contact'],
    ['Scope and right of withdrawal','How to withdraw','Consequences of withdrawal','Custom-made goods','Sample withdrawal form'],
    ['Delivery area and delivery times','Shipping costs','Payment methods and due dates']]},
  ru: {names:['Сведения о компании','Политика конфиденциальности','Условия использования','Право на отказ','Доставка и оплата'], nav:'Правовые документы', notice:'Шаблон — ещё не опубликован.', detail:'Согласованные тексты и сведения о компании будут добавлены позднее. Это не полный юридический документ.', placeholder:'Здесь будет добавлен согласованный текст.', missing:'Документ не найден', choose:'Выберите документ в меню.', sections:[
    ['Компания и адрес','Контакты','Представительство и регистрационные сведения','Идентификационный номер НДС','Урегулирование потребительских споров'],
    ['Ответственный и контакт по защите данных','Хостинг и журналы сервера','Обращения и индивидуальные предложения','Конфигуратор и статус заявки','Отзывы','Cookies и хранилище браузера','Внешние сервисы и шрифты','Получатели и международная передача данных','Сроки хранения и удаление','Ваши права и подача жалоб'],
    ['Компания и область действия','Использование сайта и конфигуратора','Заявка, индивидуальное предложение и соглашение','Техническая информация и использование по назначению','Контент и отзывы','Законные права и контакты'],
    ['Область действия и право на отказ','Как воспользоваться правом на отказ','Последствия отказа','Изделия индивидуального изготовления','Образец формы отказа'],
    ['Регион и сроки доставки','Стоимость доставки','Способы и сроки оплаты']]},
};
const keys = ['imprint','privacy','terms','withdrawal','shipping'];
const language = getLanguage();
const copy = labels[language] || labels.de;
const root = document.querySelector('.legal-page');
const key = new URLSearchParams(location.search).get('document') || 'imprint';
const index = keys.indexOf(key);
const title = index < 0 ? copy.missing : copy.names[index];
root.lang = language;
document.querySelector('#page-title').textContent = title;
document.title = `${title} — Rope-Pro-Line`;
document.querySelector('.legal-nav').setAttribute('aria-label',copy.nav);
document.querySelector('.legal-notice strong').textContent = copy.notice;
document.querySelector('.legal-notice').lastChild.textContent = copy.detail;
document.querySelector('[data-legal-not-found]').textContent = copy.choose;
document.querySelector('[data-legal-not-found]').hidden = index >= 0;
document.querySelectorAll('[data-legal-link]').forEach(link => {
  const i = keys.indexOf(link.dataset.legalLink);
  if(i < 0) return;
  link.textContent = copy.names[i];
  const url = new URL('/legal/', location.origin);
  url.searchParams.set('document', keys[i]);
  if(language !== 'de') url.searchParams.set('lang',language);
  link.href = url.pathname + url.search;
  if(i === index) link.setAttribute('aria-current','page');
});
document.querySelectorAll('.footer__legal a[href]').forEach(link => {
  const i = keys.indexOf(new URL(link.href, location.href).searchParams.get('document'));
  if (i >= 0) link.textContent = copy.names[i];
});
document.querySelectorAll('[data-legal-document]').forEach(section => {
  const i=keys.indexOf(section.dataset.legalDocument);
  section.hidden = i !== index;
  if(i < 0) return;
  section.querySelector('h2').textContent=copy.names[i];
  section.querySelectorAll('h3').forEach((heading,n)=>{if(copy.sections[i][n]) heading.textContent=`${n+1}. ${copy.sections[i][n]}`;});
  section.querySelectorAll('section > p').forEach(p=>{if(p.textContent.trim()==='Der abgestimmte Text wird hier ergänzt.') p.textContent=copy.placeholder;});
});
