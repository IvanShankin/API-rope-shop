// Разметка для редактора каната (вынесено из AdminProductsView.js).
import { escapeHtml as esc } from '../../utils/text.js?v=20261106.1';

export function transliterate(text) {
  const map = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
    'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y',
    'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
  };
  return String(text || '')
    .toLowerCase()
    .split('')
    .map(ch => map[ch] !== undefined ? map[ch] : ch)
    .join('')
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 100);
}

export function variantRowMarkup(variant, index = 0) {
  const v = variant || {};
  const tempId = v.id ? '' : `temp_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
  const diam = v.diameter_mm != null ? v.diameter_mm : '';
  const name = v.variant_name || (diam ? `${diam} мм` : '');

  return `
    <form data-variant-form ${v.id ? `data-id="${Number(v.id)}"` : `data-temp-id="${tempId}"`} class="variant-row">
      <input type="hidden" name="variant_name" value="${esc(name)}">
      <input type="hidden" name="index" value="${v.index ?? index}">
      <div class="col-diam">
        <input class="field__input field__input--compact" name="diameter_mm" type="number" min="0.01" max="9999.99" step="0.01" required value="${esc(diam)}" placeholder="8">
      </div>
      <div class="col-price">
        <div class="field__affix">
          <input class="field__input field__input--compact" name="price_per_meter" type="number" min="0" max="99999999.99" step="0.01" required value="${esc(v.price_per_meter ?? '')}" placeholder="4.50">
          <span class="field__suffix">€</span>
        </div>
      </div>
      <div class="col-load">
        <div class="field__affix">
          <input class="field__input field__input--compact" name="breaking_load_dan" type="number" min="0" max="99999999.99" step="0.01" value="${esc(v.breaking_load_dan ?? '')}" placeholder="3500">
          <span class="field__suffix">кг</span>
        </div>
      </div>
      <div class="col-weight">
        <div class="field__affix">
          <input class="field__input field__input--compact" name="weight_g_per_m" type="number" min="0" max="99999999.99" step="0.01" value="${esc(v.weight_g_per_m ?? '')}" placeholder="45">
          <span class="field__suffix">г</span>
        </div>
      </div>
      <div class="col-sku">
        <input class="field__input field__input--compact" name="sku" type="text" maxlength="100" value="${esc(v.sku ?? '')}" placeholder="—">
      </div>
      <div class="col-active">
        <label class="tick tick--compact" title="Показывать этот диаметр покупателям">
          <input class="tick__input" name="is_active" type="checkbox" ${v.is_active !== false ? 'checked' : ''}>
          <span class="tick__box" aria-hidden="true"></span>
        </label>
      </div>
      <div class="col-action">
        ${v.id ? `
          <button class="btn-icon btn-icon--danger" type="button" data-variant-remove="${Number(v.id)}" title="Удалить диаметр">✕</button>
        ` : `
          <button class="btn-icon btn-icon--muted" type="button" data-remove-new-row title="Убрать строку">✕</button>
        `}
      </div>
    </form>
  `;
}
