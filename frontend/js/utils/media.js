import { API_CONFIG } from '../api/config.js?v=20261027.10';

// Relative media paths use the same proxy prefix as the API.
export function mediaUrl(value) {
  if (!value) return '';
  try {
    const base = new URL(API_CONFIG.BASE_URL, window.location.href);
    const relative = String(value).replace(/^\/+/, '');
    const url = relative.startsWith('media/') ? new URL(`${base.pathname.replace(/\/$/, '')}/${relative}`, base.origin) : new URL(value, base.origin);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
  } catch { return ''; }
}
