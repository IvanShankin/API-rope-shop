import { getLanguage } from '../i18n/locale.js?v=20261116.1';
import { translate } from '../i18n/translate.js?v=20261116.1';

/*
 * Лёгкая маска телефона для всех языков сайта (ru, en, de, cs).
 * Номер с «+» форматируется по коду страны. Для известных стран (RU/KZ, US/CA, CZ, SK, CH, PL, FR, BY, UA,
 * мобильные DE/AT/UK) используется шаблон, для остальных сохраняются пробелы и дефисы клиента.
 * Длина не больше 15 цифр (E.164). Номер без «+» (местный формат, например 0171…) не переделываем.
 */

// Коды стран из двух цифр (остальные, кроме 1 и 7, из трёх), по списку ITU E.164.
const TWO_DIGIT = new Set('20 27 30 31 32 33 34 36 39 40 41 43 44 45 46 47 48 49 51 52 53 54 55 56 57 58 60 61 62 63 64 65 66 81 82 84 86 90 91 92 93 94 95 98'.split(' '));
// Страны, где перед местным номером набирают 0. В международном формате этот 0 лишний: +49 (0) 171 → +49 171.
const TRUNK_ZERO = new Set('20 27 31 32 33 40 41 43 44 46 49 61 62 63 64 66 81 82 84 86 90 91 92 94 98 353 358 359 380 381 385 386 387 972'.split(' '));
const PLANS = {
  '1': () => ({ p: 'XXX XXX-XXXX' }),
  '7': () => ({ p: 'XXX XXX-XX-XX' }),
  '33': () => ({ p: 'X XX XX XX XX' }),
  '41': () => ({ p: 'XX XXX XX XX' }),
  '48': () => ({ p: 'XXX XXX XXX' }),
  '375': () => ({ p: 'XX XXX-XX-XX' }),
  '380': () => ({ p: 'XX XXX XX XX' }),
  '420': () => ({ p: 'XXX XXX XXX' }),
  '421': () => ({ p: 'XXX XXX XXX' }),
  '44': n => (n.startsWith('7') ? { p: 'XXXX XXXXXX' } : null),
  '49': n => (/^1[5-7]/.test(n) ? { p: 'XXX *', min: 10 } : null),
  '43': n => (n.startsWith('6') ? { p: 'XXX *', min: 9 } : null),
};
// Что подставляем в пустое поле при фокусе и что показываем в подсказке.
const PREFIX = { ru: '+7 ', de: '+49 ', cs: '+420 ', en: '+' };
const EXAMPLE = { ru: '+7 900 000-00-00', de: '+49 171 1234567', cs: '+420 601 123 456', en: '+44 7700 900123' };
const MAX_DIGITS = 15;
const SEPARATOR = /[\s()-]/;

const onlyDigits = text => String(text).replace(/\D/g, '');

export function countryCode(digits) {
  if (!digits) return null;
  if (digits[0] === '1' || digits[0] === '7') return digits[0];
  if (digits.length < 2) return null;
  if (TWO_DIGIT.has(digits.slice(0, 2))) return digits.slice(0, 2);
  return digits.length >= 3 ? digits.slice(0, 3) : null;
}

const planFor = (cc, national) => PLANS[cc]?.(national) || null;
const slots = pattern => (pattern.match(/X/g) || []).length;

// Убирает первую цифру и пустые скобки, которые от неё остались: «(0) 171» → « 171».
function dropFirstDigit(text) {
  const i = text.search(/\d/);
  if (i < 0) return text;
  return (text.slice(0, i) + text.slice(i + 1)).replace(/^[\s-]*\(\s*\)/, '');
}

function applyPattern(pattern, digits, limit) {
  let out = '';
  let i = 0;
  for (const ch of pattern) {
    if (i >= digits.length) break;
    if (ch === 'X') out += digits[i++];
    else if (ch === '*') { out += digits.slice(i, limit); i = digits.length; }
    else out += ch;
  }
  return out;
}

function formatNational(text) {
  let left = MAX_DIGITS;
  const kept = [...text].filter(ch => (/\d/.test(ch) ? left-- > 0 : true)).join('');
  return kept.replace(/\s+/g, ' ').replace(/-+/g, '-').replace(/^[\s-]+/, '');
}

export function formatPhone(raw, language = getLanguage()) {
  let text = String(raw ?? '').replace(/[./]/g, ' ').replace(/[^\d+\s()-]/g, '');
  // «+» бывает только в начале номера: если его ввели или вставили позже, номер начинается с него.
  const lastPlus = text.lastIndexOf('+');
  if (lastPlus > 0) text = text.slice(lastPlus);
  const firstDigit = text.search(/\d/);
  const firstPlus = text.indexOf('+');
  let plus = firstPlus >= 0 && (firstDigit < 0 || firstPlus < firstDigit);
  text = text.replace(/\+/g, '');
  let digits = onlyDigits(text);
  if (!digits) return plus ? '+' : '';

  if (!plus) {
    if (digits.startsWith('00')) { plus = true; text = dropFirstDigit(dropFirstDigit(text)); }
    else if (language === 'ru' && /^[78]/.test(digits)) { plus = true; text = text.replace(/\d/, '7'); }
    else if (language === 'ru' && digits[0] === '9') { plus = true; text = '7' + text; }
    else if (digits.length === 11 && /^[78]/.test(digits)) { plus = true; text = text.replace(/\d/, '7'); }
    else return formatNational(text);
    digits = onlyDigits(text);
    if (!digits) return '+';
  }

  const cc = countryCode(digits);
  if (!cc) return '+' + digits;
  // Отделяем код страны от остального текста клиента.
  let seen = 0;
  let cut = 0;
  while (seen < cc.length) if (/\d/.test(text[cut++])) seen++;
  let rest = text.slice(cut);
  let national = onlyDigits(rest);
  if ((cc === '7' && national.length === 11 && national[0] === '8') || (TRUNK_ZERO.has(cc) && national[0] === '0')) {
    rest = dropFirstDigit(rest);
    national = onlyDigits(rest);
  }
  const limit = MAX_DIGITS - cc.length;
  const plan = planFor(cc, national);
  let body;
  if (plan) body = applyPattern(plan.p, national, limit);
  else {
    let left = limit;
    body = [...rest].filter(ch => (/\d/.test(ch) ? left-- > 0 : true)).join('')
      .replace(/\s+/g, ' ').replace(/-+/g, '-').replace(/^[\s-]+/, '');
    if (!onlyDigits(body)) body = '';
  }
  return '+' + cc + (body ? ' ' + body : '');
}

// true, если номер заполнен, но выглядит неполным или слишком длинным.
export function isPhoneIncomplete(value) {
  const text = String(value || '').trim();
  if (!text) return false;
  const digits = onlyDigits(text);
  if (!text.startsWith('+')) return digits.length < 6 || digits.length > MAX_DIGITS;
  const cc = countryCode(digits);
  if (!cc || digits.length > MAX_DIGITS) return true;
  const national = digits.slice(cc.length);
  const plan = planFor(cc, national);
  if (plan && !plan.p.includes('*')) return national.length !== slots(plan.p);
  if (plan) return national.length < plan.min;
  return digits.length < 7 || national.length < 4;
}

// В поле только код страны (или один «+»): считаем, что телефон не указан.
function isPrefixOnly(value) {
  const digits = onlyDigits(value);
  return String(value).trim() === '+' || (String(value).trim().startsWith('+') && digits.length > 0 && countryCode(digits) === digits);
}

export function phoneValue(input) {
  const value = formatPhone(input.value);
  return isPrefixOnly(value) ? '' : value;
}

// Позиция в строке сразу после n-й цифры (n = 0 → после «+», если он есть).
function caretAfterDigits(value, n) {
  if (n <= 0) return value.startsWith('+') ? 1 : 0;
  let seen = 0;
  for (let i = 0; i < value.length; i++) if (/\d/.test(value[i]) && ++seen === n) return i + 1;
  return value.length;
}

export function attachPhoneMask(input) {
  if (!input || input.dataset.phoneMask) return;
  input.dataset.phoneMask = 'on';
  const language = getLanguage();
  input.type = 'tel';
  input.inputMode = 'tel';
  input.autocomplete = 'tel';
  input.maxLength = 40;
  input.spellcheck = false;
  if (!input.placeholder) input.placeholder = EXAMPLE[language] || EXAMPLE.en;

  const message = () => translate('Проверьте номер телефона: похоже, он указан не полностью.', language);
  const validate = () => input.setCustomValidity(isPhoneIncomplete(phoneValue(input)) ? message() : '');
  const setValue = (raw, digitsBeforeCaret, atEnd) => {
    const next = formatPhone(raw, language);
    if (input.value !== next) input.value = next;
    if (document.activeElement === input) {
      const pos = atEnd ? next.length : caretAfterDigits(next, digitsBeforeCaret);
      input.setSelectionRange(pos, pos);
    }
    validate();
  };

  // Удаление разделителя, который маска сразу вернёт, удаляет соседнюю цифру — иначе курсор «застревает».
  input.addEventListener('beforeinput', event => {
    const back = event.inputType === 'deleteContentBackward';
    if (!back && event.inputType !== 'deleteContentForward') return;
    const { value, selectionStart: start, selectionEnd: end } = input;
    if (start !== end) return;
    const index = back ? start - 1 : start;
    if (index < 0 || index >= value.length || !SEPARATOR.test(value[index])) return;
    if (formatPhone(value.slice(0, index) + value.slice(index + 1), language) !== value) return;
    let digit = index;
    while (digit >= 0 && digit < value.length && !/\d/.test(value[digit])) digit += back ? -1 : 1;
    if (digit < 0 || digit >= value.length) return;
    event.preventDefault();
    const raw = value.slice(0, digit) + value.slice(digit + 1);
    setValue(raw, onlyDigits(raw.slice(0, digit)).length, false);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });

  input.addEventListener('input', event => {
    if (event.isComposing) return;
    const { value, selectionStart } = input;
    const caret = selectionStart ?? value.length;
    setValue(value, onlyDigits(value.slice(0, caret)).length, caret >= value.length);
  });

  // Вставка полного номера (+… или 00…) заменяет код страны, подставленный при фокусе.
  input.addEventListener('paste', event => {
    const text = event.clipboardData?.getData('text') || '';
    const full = /^\s*(?:\+|00)/.test(text.replace(/^\s*tel:/i, '')) || (language === 'ru' && /^[78]\d{10}$/.test(onlyDigits(text)));
    if (!full || !(isPrefixOnly(input.value) || input.selectionStart === 0 && input.selectionEnd === input.value.length)) return;
    event.preventDefault();
    setValue(text, 0, true);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });

  input.addEventListener('focus', () => {
    if (input.value || input.readOnly || input.disabled) return;
    input.value = PREFIX[language] || '+';
    requestAnimationFrame(() => input.setSelectionRange(input.value.length, input.value.length));
  });

  input.addEventListener('blur', () => {
    input.value = phoneValue(input);
    validate();
  });

  // Перед отправкой: убираем «пустой» код страны и проверяем номер (срабатывает раньше обработчика формы).
  input.form?.addEventListener('submit', () => {
    input.value = phoneValue(input);
    validate();
  }, true);

  if (input.value) input.value = formatPhone(input.value, language);
  validate();
}

export function attachPhoneMasks(root = document) {
  root.querySelectorAll('input[type="tel"], input[data-phone]').forEach(attachPhoneMask);
}
