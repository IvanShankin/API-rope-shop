// Only for text and quoted HTML attributes; URLs are built from validated IDs.
import { apiLocale } from '../i18n/locale.js?v=20261027.10';
export const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[char]));

export const displayName = (item) => item?.name || item?.translations?.find((t) => t.locale === apiLocale())?.name || item?.translations?.find((t) => t.locale === 'eng')?.name
  || item?.translations?.[0]?.name || item?.code || '';
