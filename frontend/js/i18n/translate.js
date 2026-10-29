import { dictionary, patterns } from './dictionary.js?v=20261027.10';
import { getLanguage } from './locale.js?v=20261027.10';

const normalize = text => String(text).replace(/\s+/g, ' ').trim();
const entries = new Map(dictionary.map(row => [normalize(row[0]), row]));
const escapePattern = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const templates = patterns.map(row => {
  const parts = row[0].split(/(\{\d+\})/);
  const ids = parts.filter(part => /^\{\d+\}$/.test(part));
  const regex = new RegExp('^' + parts.map(part => /^\{\d+\}$/.test(part) ? '(.+?)' : escapePattern(part)).join('') + '$');
  return { row, ids, regex, specificity: row[0].replace(/\{\d+\}/g,'').length };
}).sort((a,b) => b.specificity-a.specificity);

export function translate(text, language = getLanguage(), depth = 0) {
  if (language === 'ru' || !['en','de'].includes(language)) return String(text);
  const source = normalize(text);
  const index = language === 'en' ? 1 : 2;
  const exact = entries.get(source);
  let result = exact?.[index];
  const pricedLabel = source.match(/^(.+?) (\d+(?:[.,]\d+)?) EUR$/);
  if (!result && pricedLabel && !/[·:]/.test(pricedLabel[1]) && depth < 3) {
    result = `${translate(pricedLabel[1], language, depth + 1)} ${pricedLabel[2]} EUR`;
  }
  if (!result && depth < 3) {
    for (const template of templates) {
      const match = source.match(template.regex);
      if (!match) continue;
      const values = Object.fromEntries(template.ids.map((id,i) => [id,translate(match[i+1],language,depth+1)]));
      result = template.row[index].replace(/\{\d+\}/g, id => values[id]);
      break;
    }
  }
  if (!result) return String(text);
  return String(text).replace(/\S[\s\S]*\S|\S/, () => result);
}
