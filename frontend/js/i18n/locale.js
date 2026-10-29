export const languages = ['ru', 'en', 'de'];
export function getLanguage() {
  if (typeof window === 'undefined') return 'ru';
  try {
    const query = new URLSearchParams(window.location.search).get('lang');
    if (languages.includes(query)) return query;
    // Public URLs have a stable language regardless of cookies/browser history.
    return /^\/(?:admin|login)(?:\/|\.html|$)/.test(window.location.pathname || '') ? 'ru' : 'de';
  } catch { return 'de'; }
}
export const apiLocale = () => ({ru:'rus',en:'eng',de:'ger'}[getLanguage()]);
