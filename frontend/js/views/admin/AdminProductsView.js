import { AdminNotificationView } from './AdminNotificationView.js?v=20261027.10';
import { AdminRecordList } from './AdminRecordList.js?v=20261027.10';
import { escapeHtml as esc, displayName } from '../../utils/text.js?v=20261027.10';
import { API_CONFIG } from '../../api/config.js?v=20261027.10';
import { mediaUrl } from '../../utils/media.js?v=20261027.10';

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

export class AdminProductsView {
  constructor(root) {
    this.root = root;
    this.baselines = new Map();
    this.events = new AbortController();
    this.recordList = new AdminRecordList(root.querySelector('[data-product-select]'), this.events.signal);
    this.slugTouched = false;
    this.currentProduct = null;
  }

  bind({ refresh, select, create, save, remove, image }) {
    const options = { signal: this.events.signal };
    this.root.querySelector('[data-products-refresh]').addEventListener('click', refresh, options);
    this.recordList.onSelect = select;
    this.root.querySelector('[data-product-new]').addEventListener('click', create, options);

    this.root.addEventListener('submit', e => {
      if (!e.target.matches('[data-product-form], [data-variant-form], [data-product-colors-form], [data-color-order-form]')) return;
      e.preventDefault();
      save();
    }, options);

    this.root.addEventListener('click', e => {
      if (e.target.closest('[data-products-save]')) save();
    }, options);

    this.root.addEventListener('click', e => {
      const button = e.target.closest('[data-product-remove], [data-variant-remove]');
      if (button) remove(button.dataset.variantRemove ? Number(button.dataset.variantRemove) : null);
    }, options);

    this.root.addEventListener('click', e => {
      const button = e.target.closest('[data-product-image]');
      if (button) image(button.dataset.productImage, Number(button.dataset.imageId), this.root.querySelector('[data-product-file]')?.files[0]);
    }, options);

    // Вкладки языков
    this.root.addEventListener('click', e => {
      const tab = e.target.closest('[data-lang-tab]');
      if (!tab) return;
      const lang = tab.dataset.langTab;
      this.root.querySelectorAll('[data-lang-tab]').forEach(btn => {
        btn.classList.toggle('lang-switch__button--active', btn === tab);
      });
      this.root.querySelectorAll('[data-lang-panel]').forEach(panel => {
        panel.hidden = panel.dataset.langPanel !== lang;
      });
    }, options);

    // Копирование русского описания в EN и DE
    this.root.addEventListener('click', e => {
      if (!e.target.closest('[data-copy-translations]')) return;
      const form = this.root.querySelector('[data-product-form]');
      if (!form) return;
      const nameRu = form.querySelector('[name=name_rus]')?.value || '';
      const subRu = form.querySelector('[name=subtitle_rus]')?.value || '';
      const descRu = form.querySelector('[name=description_rus]')?.value || '';
      if (!nameRu.trim()) {
        this.message('Сначала введите русское название каната.', 'warning');
        return;
      }
      ['eng', 'ger'].forEach(locale => {
        const nameEl = form.querySelector(`[name=name_${locale}]`);
        const subEl = form.querySelector(`[name=subtitle_${locale}]`);
        const descEl = form.querySelector(`[name=description_${locale}]`);
        if (nameEl && !nameEl.value.trim()) nameEl.value = nameRu;
        if (subEl && !subEl.value.trim()) subEl.value = subRu;
        if (descEl && !descEl.value.trim()) descEl.value = descRu;
      });
      this.updateLangIndicators();
      this.message('Текст скопирован в английскую и немецкую версии.', 'success');
    }, options);

    // Добавление строки диаметра
    this.root.addEventListener('click', e => {
      if (!e.target.closest('[data-action="add-variant"]')) return;
      const container = this.root.querySelector('[data-variants-container]');
      if (!container) return;
      const index = container.querySelectorAll('[data-variant-form]').length;
      container.insertAdjacentHTML('beforeend', this.variantRow(null, index));
      const newRow = container.lastElementChild;
      const diamInput = newRow?.querySelector('[name=diameter_mm]');
      diamInput?.focus();
    }, options);

    // Удаление ещё не сохранённой новой строки диаметра
    this.root.addEventListener('click', e => {
      const btn = e.target.closest('[data-remove-new-row]');
      if (!btn) return;
      const row = btn.closest('[data-variant-form]');
      if (row) {
        this.baselines.delete(this.formKey(row));
        row.remove();
      }
    }, options);

    // Авто-название варианта при вводе диаметра
    this.root.addEventListener('input', e => {
      if (e.target.matches('[name=diameter_mm]')) {
        const row = e.target.closest('[data-variant-form]');
        const nameInput = row?.querySelector('[name=variant_name]');
        if (nameInput) {
          const val = e.target.value.trim();
          nameInput.value = val ? `${val} мм` : '';
        }
      }
    }, options);

    // Автогенерация ссылки (slug) и индикаторы языков
    this.root.addEventListener('input', e => {
      if (e.target.matches('[name=slug]')) {
        this.slugTouched = true;
      } else if (e.target.matches('[name=name_rus]')) {
        this.updateLangIndicators();
        if (!this.slugTouched && !this.currentProduct?.product_id) {
          const slugInput = this.root.querySelector('[name=slug]');
          if (slugInput) slugInput.value = transliterate(e.target.value);
        }
      } else if (e.target.matches('[name^="name_"]')) {
        this.updateLangIndicators();
      }
    }, options);

    // Drag-and-drop для фото
    this.root.addEventListener('dragover', e => {
      const dropzone = e.target.closest('[data-photo-dropzone]');
      if (dropzone) {
        e.preventDefault();
        dropzone.classList.add('admin-photo-dropzone--active');
      }
    }, options);

    this.root.addEventListener('dragleave', e => {
      const dropzone = e.target.closest('[data-photo-dropzone]');
      if (dropzone) {
        dropzone.classList.remove('admin-photo-dropzone--active');
      }
    }, options);

    this.root.addEventListener('drop', e => {
      const dropzone = e.target.closest('[data-photo-dropzone]');
      if (dropzone) {
        e.preventDefault();
        dropzone.classList.remove('admin-photo-dropzone--active');
        const files = e.dataTransfer?.files;
        if (files?.length) {
          const fileInput = this.root.querySelector('[data-product-file]');
          if (fileInput) {
            fileInput.files = files;
            const uploadBtn = this.root.querySelector('[data-product-image="upload"]');
            uploadBtn?.click();
          }
        }
      }
    }, options);

    // Быстрый выбор фото по клику на область
    this.root.addEventListener('change', e => {
      if (e.target.matches('[data-product-file]')) {
        if (e.target.files?.length && this.currentProduct) {
          const uploadBtn = this.root.querySelector('[data-product-image="upload"]');
          uploadBtn?.click();
        }
      }
    }, options);

    window.addEventListener('beforeunload', e => {
      if (this.hasChanges()) { e.preventDefault(); e.returnValue = ''; }
    }, options);
  }

  destroy() { this.events.abort(); }
  setBusy(value) {
    this.root.querySelectorAll('button, input, select, textarea').forEach(el => { el.disabled = value; });
    this.recordList.busy(value);
  }
  setSelection(id) { this.recordList.select(id); }
  clear() {
    this.root.querySelector('[data-product-editor]').replaceChildren();
    this.baselines.clear();
    this.recordList.select(null);
    this.currentProduct = null;
    this.slugTouched = false;
  }

  formKey(form) {
    if (form.matches('[data-color-order-form]')) return `color-order:${form.dataset.linkId}`;
    if (form.matches('[data-product-colors-form]')) return 'colors';
    if (form.matches('[data-product-splices-form]')) return 'splices';
    if (form.matches('[data-product-form]')) return 'product';
    return `variant:${form.dataset.id || form.dataset.tempId || 'new'}`;
  }

  readForm(form) {
    return Object.fromEntries(Array.from(form.elements).filter(el => el.name).map(el =>
      [el.name, el.type === 'checkbox' ? el.checked : el.value]));
  }

  remember() {
    this.baselines = new Map(Array.from(this.root.querySelectorAll('form')).map(form =>
      [this.formKey(form), JSON.stringify(this.readForm(form))]));
  }

  drafts(except) {
    return Array.from(this.root.querySelectorAll('form')).filter(form => form !== except)
      .filter(form => JSON.stringify(this.readForm(form)) !== this.baselines.get(this.formKey(form)))
      .map(form => ({ key: this.formKey(form), values: this.readForm(form) }));
  }

  hasChanges() { return this.drafts().length > 0; }
  allowDiscard() { return !this.hasChanges() || window.confirm('Есть несохранённые изменения. Отбросить их?'); }

  restoreDrafts(drafts) {
    for (const form of this.root.querySelectorAll('form')) {
      const draft = drafts.find(item => item.key === this.formKey(form));
      if (!draft) continue;
      for (const el of form.elements) if (el.name in draft.values) {
        if (el.type === 'checkbox') el.checked = draft.values[el.name];
        else el.value = draft.values[el.name];
      }
    }
  }

  markSaved(form, id) {
    const oldKey = this.formKey(form);
    if (form.matches('[data-variant-form]')) form.dataset.id = id;
    this.baselines.delete(oldKey);
    this.baselines.set(this.formKey(form), JSON.stringify(this.readForm(form)));
  }

  message(text, type = 'info') { AdminNotificationView.message(this.root.querySelector('[data-product-status]'), text, type); }

  renderList(products) {
    this.recordList.setItems(products.map(p => ({
      id: p.product_id,
      label: p.name || p.translations?.[0]?.name || p.construction || 'Без названия',
      detail: p.is_active === false ? 'Неактивен' : '',
      search: (p.translations || []).map(t => t.name).join(' ')
    })));
  }

  updateLangIndicators() {
    const form = this.root.querySelector('[data-product-form]');
    if (!form) return;
    ['rus', 'eng', 'ger'].forEach(locale => {
      const val = form.querySelector(`[name=name_${locale}]`)?.value || '';
      const dot = this.root.querySelector(`[data-lang-indicator="${locale}"]`);
      if (dot) dot.classList.toggle('lang-tab__indicator--filled', Boolean(val.trim()));
    });
  }

  renderProduct(product, groups, materials) {
    this.currentProduct = product;
    this.slugTouched = Boolean(product?.slug);
    this.recordList.select(product?.product_id);

    const options = (items, selected) => items.map(item =>
      `<option value="${Number(item.id)}" ${Number(item.id) === Number(selected) ? 'selected' : ''}>${esc(displayName(item))}</option>`).join('');
    const input = (name, label, value, attrs = '', hint = '') => `
      <label class="field">
        <span class="field__label">${label}</span>
        <input class="field__input" name="${name}" value="${esc(value ?? '')}" ${attrs}>
        ${hint ? `<span class="field__hint">${hint}</span>` : ''}
      </label>`;

    const p = product || {};
    const hasV2 = Boolean(API_CONFIG.CATALOG_V2);

    const translations = ['rus', 'eng', 'ger'].map(locale => {
      const t = p.translations?.find(item => item.locale === locale) || {};
      return { locale, name: t.name || '', subtitle: t.subtitle || '', description: t.description || '' };
    });

    const constructionOptions = [
      { code: 'hm_core', label: 'Сердечник в оплётке (Kern-Mantel / Dyneema)' },
      { code: 'hollow', label: 'Полое 12-прядное плетение (Hohlgeflecht)' },
      { code: 'polyester_core', label: 'Полиэстеровый сердечник в оплётке' },
    ];

    const currentConst = p.construction_type || '';
    const spliceTypes = this.spliceTypes || [];
    const selectedSplices = new Set((this.spliceLinks || []).map(link => Number(link.splice_type_id)));
    const knownIds = new Set(spliceTypes.map(type => Number(type.id)));
    const spliceChoices = [...spliceTypes, ...(this.spliceLinks || []).filter(link => !knownIds.has(Number(link.splice_type_id))).map(link => ({id: link.splice_type_id, name: `Заделка #${link.splice_type_id}`, is_active:false}))];

    this.root.querySelector('[data-product-editor]').innerHTML = `
      <div class="product-header">
        <h2 class="product-header__title">${product ? `Канат: ${esc(p.name || p.translations?.[0]?.name || `#${Number(p.product_id)}`)}` : 'Новый канат'}</h2>
        ${product ? `
          <div class="product-header__actions">
            <a class="btn btn--ghost btn--small" href="/configurator/?product=${Number(p.product_id)}" target="_blank" rel="noopener">
              Открыть в конфигураторе ↗
            </a>
            <button class="btn btn--danger btn--small" type="button" data-product-remove>
              Удалить канат
            </button>
          </div>
        ` : ''}
      </div>

      <!-- Основная форма каната -->
      <form data-product-form class="product-editor">
        <!-- Языковые вкладки: Название, подзаголовок и описание -->
        <div class="card card--static card--padded product-text-card">
          <h3 class="product-text-card__title">Название и описание</h3>
          <p class="product-text-card__hint">Заполните информацию для покупателей на нужных языках.</p>
          <div class="product-lang-bar">
            <div class="lang-switch" role="tablist" aria-label="Язык текста товара">
              <button class="lang-switch__button lang-switch__button--active" type="button" data-lang-tab="rus" role="tab">
                <span class="lang-tab__indicator ${translations.find(t => t.locale === 'rus')?.name ? 'lang-tab__indicator--filled' : ''}" data-lang-indicator="rus"></span> Русский
              </button>
              <button class="lang-switch__button" type="button" data-lang-tab="eng" role="tab">
                <span class="lang-tab__indicator ${translations.find(t => t.locale === 'eng')?.name ? 'lang-tab__indicator--filled' : ''}" data-lang-indicator="eng"></span> English
              </button>
              <button class="lang-switch__button" type="button" data-lang-tab="ger" role="tab">
                <span class="lang-tab__indicator ${translations.find(t => t.locale === 'ger')?.name ? 'lang-tab__indicator--filled' : ''}" data-lang-indicator="ger"></span> Deutsch
              </button>
            </div>
            <button class="btn btn--ghost btn--small" type="button" data-copy-translations title="Скопировать русский текст в английскую и немецкую версии">
               Скопировать из RU в EN и DE
            </button>
          </div>

          <!-- Вкладка RUS -->
          <div class="lang-tab-panel" data-lang-panel="rus">
            ${input('name_rus', 'Название каната (RU) *', translations.find(t => t.locale === 'rus')?.name, 'required maxlength="255"', 'Основное название, например: LIROS Control-XTR')}
            ${input('subtitle_rus', 'Короткий подзаголовок (RU)', translations.find(t => t.locale === 'rus')?.subtitle, 'maxlength="255"', 'Пояснение под названием, например: Для яхт и лебёдок')}
            <label class="field">
              <span class="field__label">Описание каната (RU)</span>
              <textarea class="field__input field__textarea" name="description_rus" rows="3">${esc(translations.find(t => t.locale === 'rus')?.description || '')}</textarea>
              <span class="field__hint">Свойства, конструкция и назначение каната</span>
            </label>
          </div>

          <!-- Вкладка ENG -->
          <div class="lang-tab-panel" data-lang-panel="eng" hidden>
            ${input('name_eng', 'Название каната (ENG)', translations.find(t => t.locale === 'eng')?.name, 'maxlength="255"', 'English product name')}
            ${input('subtitle_eng', 'Подзаголовок (ENG)', translations.find(t => t.locale === 'eng')?.subtitle, 'maxlength="255"', 'English subtitle')}
            <label class="field">
              <span class="field__label">Описание (ENG)</span>
              <textarea class="field__input field__textarea" name="description_eng" rows="3">${esc(translations.find(t => t.locale === 'eng')?.description || '')}</textarea>
            </label>
          </div>

          <!-- Вкладка GER -->
          <div class="lang-tab-panel" data-lang-panel="ger" hidden>
            ${input('name_ger', 'Название каната (GER)', translations.find(t => t.locale === 'ger')?.name, 'maxlength="255"', 'Deutscher Produktname')}
            ${input('subtitle_ger', 'Подзаголовок (GER)', translations.find(t => t.locale === 'ger')?.subtitle, 'maxlength="255"', 'Deutscher Untertitel')}
            <label class="field">
              <span class="field__label">Описание (GER)</span>
              <textarea class="field__input field__textarea" name="description_ger" rows="3">${esc(translations.find(t => t.locale === 'ger')?.description || '')}</textarea>
            </label>
          </div>
        </div>

        <!-- Параметры и разделы каталога -->
        <details class="admin-disclosure" open>
          <summary class="admin-disclosure__summary">
            <span>Категория и характеристики каната</span>
          </summary>
          <div class="admin-disclosure__body">
            <div class="fields fields--two">
              ${hasV2 ? `
                <label class="field">
                  <span class="field__label">Категория в каталоге *</span>
                  <select class="field__input" name="category_id" required>
                    <option value="">Выберите категорию</option>
                    ${options(this.categories || [], p.category_id)}
                  </select>
                  <span class="field__hint">Основной раздел сайта, в котором находится канат</span>
                </label>
              ` : ''}

              <label class="field">
                <span class="field__label">Группа материала *</span>
                <select class="field__input" name="material_group_id" required>
                  <option value="">Выберите группу</option>
                  ${options(groups, p.material_group_id)}
                </select>
                <span class="field__hint">Например: Dyneema или Polyester</span>
              </label>
            </div>

            <div class="fields fields--two">
              <label class="field">
                <span class="field__label">Материал для расчёта заделок *</span>
                <select class="field__input" name="splice_material_id" required>
                  <option value="">Выберите материал расчёта</option>
                  ${options(materials, p.splice_material_id)}
                </select>
                <span class="field__hint">Определяет тариф на заделки</span>
              </label>

              <label class="field">
                <span class="field__label">Тип конструкции (для фильтра каталога)</span>
                <select class="field__input" name="construction_type">
                  <option value="">Не указан (любой)</option>
                  ${constructionOptions.map(opt => `
                    <option value="${opt.code}" ${currentConst === opt.code ? 'selected' : ''}>${opt.label}</option>
                  `).join('')}
                  ${currentConst && !constructionOptions.some(o => o.code === currentConst) ? `
                    <option value="${esc(currentConst)}" selected>${esc(currentConst)}</option>
                  ` : ''}
                </select>
                <span class="field__hint">Используется в фильтре каталога</span>
              </label>
            </div>

            <div class="fields fields--two">
              ${hasV2 ? input('slug', 'Короткий адрес товара *', p.slug, 'required maxlength="150" pattern="[a-zA-Z0-9_-]+"', 'Только часть адреса, например liros-control-xtr. Без https:// и названия сайта') : ''}
              ${hasV2 ? input('index', 'Порядковый номер при выводе', p.index ?? 0, 'type="number" min="0" step="1" required', 'Чем меньше число, тем выше канат в каталоге') : ''}
            </div>

            <!-- Дополнительные свойства -->
            <div class="admin-checkboxes-row">
              <label class="tick">
                <input class="tick__input" name="is_active" type="checkbox" ${p.is_active !== false ? 'checked' : ''}>
                <span class="tick__box" aria-hidden="true"></span>
                <span class="tick__text">Товар активен (виден покупателям в каталоге)</span>
              </label>
              <label class="tick">
                <input class="tick__input" name="has_configurator" type="checkbox" ${p.has_configurator !== false ? 'checked' : ''}>
                <span class="tick__box" aria-hidden="true"></span>
                <span class="tick__text">Доступен заказ через конфигуратор</span>
              </label>
              <label class="tick">
                <input class="tick__input" name="can_be_spliced" type="checkbox" ${p.can_be_spliced !== false ? 'checked' : ''}>
                <span class="tick__box" aria-hidden="true"></span>
                <span class="tick__text">Допускается сращивание (сплайсинг)</span>
              </label>
            </div>

            <!-- Тексты конструкции -->
            <div class="fields fields--two" style="margin-top: 16px;">
              <label class="field">
                <span class="field__label">Сердечник</span>
                <textarea class="field__input field__textarea" name="core_description" rows="2">${esc(p.core_description || '')}</textarea>
                <span class="field__hint">Материал и строение сердечника</span>
              </label>
              <label class="field">
                <span class="field__label">Оплётка</span>
                <textarea class="field__input field__textarea" name="cover_description" rows="2">${esc(p.cover_description || '')}</textarea>
                <span class="field__hint">Материал и строение оплётки</span>
              </label>
            </div>
            <input type="hidden" name="construction" value="${esc(p.construction || '')}">
          </div>
        </details>
      </form>

      <!-- Доступные заделки сохраняются вместе с товаром отдельным запросом API. -->
      <details class="admin-disclosure" open>
        <summary class="admin-disclosure__summary"><span>Доступные заделки каната</span><span class="admin-disclosure__hint">Выберите варианты, которые можно заказать для этого каната</span></summary>
        <div class="admin-disclosure__body">
          <p class="field__hint">Если ничего не отмечено, ограничений по заделкам нет. Покупателю доступны подходящие активные заделки, если сращивание включено.</p>
          <form data-product-splices-form class="product-editor admin-card">
            ${spliceChoices.length ? `<div class="admin-checkbox-grid">${spliceChoices.map(type => `<label class="admin-toggle"><input type="checkbox" name="splice_${Number(type.id)}" ${selectedSplices.has(Number(type.id))?'checked':''}><span>${esc(displayName(type)||`Заделка #${type.id}`)}${type.is_active===false?' (отключена)':''}</span></label>`).join('')}</div>` : '<p>Виды заделок пока не добавлены. Добавьте их в разделе «Конфигуратор и цены».</p>'}
          </form>
        </div>
      </details>

      <!-- Диаметры и цены каната -->
      <details class="admin-disclosure" open>
        <summary class="admin-disclosure__summary">
          <span>Диаметры и цены каната</span>
          <span class="admin-disclosure__hint">Задайте диаметры, цены за 1 метр и разрывную нагрузку</span>
        </summary>
        <div class="admin-disclosure__body">
          <div class="variants-table-wrap">
            <div class="variants-table-header">
              <div class="col-diam">Диаметр, мм *</div>
              <div class="col-price">Цена/метр, € *</div>
              <div class="col-load">Разрыв, кг</div>
              <div class="col-weight">Вес, г/м</div>
              <div class="col-sku">Артикул</div>
              <div class="col-active">Активен</div>
              <div class="col-action"></div>
            </div>
            <div class="variants-table-body" data-variants-container>
              ${((p.variants || []).length > 0)
        ? [...p.variants].sort((a, b) => (Number(a.index) || 0) - (Number(b.index) || 0)).map((v, i) => this.variantRow(v, i)).join('')
        : this.variantRow(null, 0)
      }
            </div>
            <div class="variants-table-footer">
              <button class="btn btn--ghost btn--small" type="button" data-action="add-variant">
                + Добавить диаметр
              </button>
            </div>
          </div>
        </div>
      </details>

      <!-- Доступные цвета -->
      <details class="admin-disclosure" open>
        <summary class="admin-disclosure__summary">
          <span>Доступные цвета каната</span>
          <span class="admin-disclosure__hint">Отметьте цвета, в которых выпускается этот канат</span>
        </summary>
        <div class="admin-disclosure__body">
          <form data-product-colors-form class="product-editor">
            <div class="color-swatches-grid">
              ${(this.colors || []).map(c => `
                <label class="color-swatch-badge ${c.is_active === false ? 'color-swatch-badge--inactive' : ''}">
                  <input type="checkbox" name="color_${Number(c.id)}" ${(p.colors || []).some(link => Number(link.color_id) === Number(c.id)) ? 'checked' : ''}>
                  <span class="color-swatch-circle" style="background-color: ${esc(c.hex || '#666')}"></span>
                  <span class="color-swatch-name">${esc(displayName(c))}</span>
                </label>
              `).join('')}
            </div>
          </form>
          ${(p.colors || []).length ? `
            <details class="admin-disclosure" style="margin-top: 14px;">
              <summary class="admin-disclosure__summary"><span>Порядок цветов в списке</span></summary>
              <div class="admin-disclosure__body">
                ${[...(p.colors || [])].sort((a, b) => (Number(a.index) || 0) - (Number(b.index) || 0)).map(link => `
                  <form data-color-order-form data-link-id="${Number(link.id)}" class="product-editor" style="margin-bottom: 8px;">
                    ${input('index', esc(displayName(link.color) || `Цвет #${link.color_id}`), link.index, 'type="number" min="0" step="1" required')}
                  </form>
                `).join('')}
              </div>
            </details>
          ` : ''}
        </div>
      </details>

      <!-- Фотографии товара -->
      ${hasV2 ? `
        <details class="admin-disclosure" data-product-photos open>
          <summary class="admin-disclosure__summary">
            <span>Фотографии каната</span>
            <span class="admin-disclosure__hint">Главное фото показывается на обложке в каталоге</span>
          </summary>
          <div class="admin-disclosure__body">
            ${product ? `
              <div class="admin-photo-dropzone" data-photo-dropzone>
                <div class="admin-photo-dropzone__icon">📷</div>
                <div class="admin-photo-dropzone__text">
                  <strong>Перетащите фотографии сюда</strong> или нажмите для выбора файла на компьютере
                </div>
                <input type="file" accept="image/png,image/jpeg,image/webp,image/heic" data-product-file class="admin-photo-dropzone__input">
                <button class="btn btn--ghost btn--small" type="button" data-product-image="upload" hidden>Загрузить</button>
              </div>

              ${(p.images || []).length ? `
                <div class="admin-photos-grid">
                  ${(p.images || []).map(img => `
                    <div class="admin-photo-card ${img.is_main ? 'admin-photo-card--main' : ''}">
                      <img class="admin-photo-card__img" src="${esc(mediaUrl(img.image_url))}" alt="Фото каната #${Number(img.id)}">
                      <div class="admin-photo-card__meta">
                        ${img.is_main ? `
                          <span class="admin-photo-card__badge">★ Главное фото</span>
                        ` : `
                          <button class="btn btn--ghost btn--small" type="button" data-product-image="main" data-image-id="${Number(img.id)}">
                            Сделать главным
                          </button>
                        `}
                        <button class="btn-icon btn-icon--danger" type="button" data-product-image="remove" data-image-id="${Number(img.id)}" title="Удалить фото">
                          ✕
                        </button>
                      </div>
                    </div>
                  `).join('')}
                </div>
              ` : '<p class="field__hint" style="margin-top: 12px;">У этого каната пока нет фотографий.</p>'}
            ` : `
              <p class="field__hint">Фотографии можно будет загрузить сразу после сохранения нового каната.</p>
            `}
          </div>
        </details>
      ` : ''}

      <!-- Кнопка сохранения -->
      <div class="admin-product-save">
        <button class="btn btn--primary btn--large" type="button" data-products-save>
          ${product ? 'Сохранить все изменения' : 'Создать канат'}
        </button>
      </div>
    `;

    this.remember();
  }

  variantRow(variant, index = 0) {
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

  // Для обратной совместимости с тестами
  variantForm(variant, input) {
    return this.variantRow(variant);
  }
}
