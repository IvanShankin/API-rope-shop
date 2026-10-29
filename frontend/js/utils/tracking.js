import {getLanguage} from '../i18n/locale.js?v=20261027.10';

export function trackingPath(quote) {
  if (!quote?.request_number || !quote?.tracking_token) return '';
  const params = new URLSearchParams({token: quote.tracking_token, lang: getLanguage()});
  return `/order-tracking/${encodeURIComponent(quote.request_number)}?${params}`;
}

export function appendTrackingLink(root, quote) {
  const path = trackingPath(quote);
  if (!root || !path) return;
  const link = document.createElement('a');
  link.href = path;
  link.className = 'button button--ghost';
  link.textContent = ({ru:'Посмотреть заявку',en:'View enquiry',de:'Anfrage ansehen'})[getLanguage()];
  const paragraph = document.createElement('p');
  paragraph.append(link);
  root.append(paragraph);
}
