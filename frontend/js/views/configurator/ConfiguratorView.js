import {appendTrackingLink} from '../../utils/tracking.js?v=20261027.10';
import { catalogLink, updateLoadState } from '../../ui/load-state.js?v=20261027.10';
import { BaseView } from '../BaseView.js?v=20261027.10';
import { RopeSvgRenderer } from './RopeSvgRenderer.js?v=20261027.10';
import { escapeHtml, displayName } from '../../utils/text.js?v=20261027.10';

export class ConfiguratorView extends BaseView {
  constructor(root = '#configurator') {
    super(root);
    if (!this.root) return;

    this.form = this.$('.configurator__layout');
    this.preview = this.$('.rope-preview');
    this.svg = this.$('.rope-preview__canvas');
    this.svgRenderer = new RopeSvgRenderer(this.svg);

    this.lengthInput = this.form?.elements['cfg-length'];
    this.range = this.$('[data-cfg-range]');
    this.qtyInput = this.form?.elements['cfg-qty'];
    this.linesContainer = this.$('[data-cfg-lines]');
    this.submitStatus = this.$('[data-cfg-submit-status]');
    this.selectionValid = false;
    this.isSubmitting = false;
    this.optionSignatures = new Map();
    this.dataStatus = 'loading';
    this.setSubmitLoading(false);

    this.notices = {};
    this.$$('[data-cfg-notice]').forEach((el) => {
      this.notices[el.dataset.cfgNotice] = el;
    });

    // Коллбэки событий для контроллера
    this.callbacks = {};
    if (this.form) {
      this.dataMessage = document.createElement('p');
      this.dataMessage.className = 'configurator__notice';
      this.dataMessage.setAttribute('role', 'status');
      this.retryButton = document.createElement('button');
      this.retryButton.type = 'button';
      this.retryButton.className = 'button button--ghost button--small';
      this.retryButton.textContent = 'Повторить загрузку';
      this.retryButton.hidden = true;
      this.retryButton.addEventListener('click', () => this.callbacks.onRetry?.());
      this.catalogLink = catalogLink();
      this.form.before(this.dataMessage, this.retryButton, this.catalogLink);
      this.priceMessage = document.createElement('p');
      this.priceMessage.className = 'configurator__notice';
      this.priceMessage.setAttribute('role', 'status');
      this.priceRetry = this.retryButton.cloneNode(true);
      this.priceRetry.textContent = 'Обновить цены';
      this.priceRetry.addEventListener('click', () => this.callbacks.onPriceRetry?.());
      this.$('.summary').prepend(this.priceMessage, this.priceRetry);
    }
  }

  onEvent(event, callback) {
    this.callbacks[event] = callback;
  }

  initListeners() {
    if (!this.form) return;

    // Смена радиокнопок
    this.form.addEventListener('change', (e) => {
      if (e.target === this.range || e.target.closest('.summary__contacts')) return;

      const name = e.target.name;
      if (name === 'cfg-material') {
        this.callbacks.onProductChange?.(e.target.value);
      } else if (name === 'cfg-diameter') {
        this.callbacks.onVariantChange?.(e.target.value);
      } else if (name === 'cfg-color') {
        this.callbacks.onColorChange?.(e.target.value);
      } else if (name === 'cfg-end-a') {
        this.callbacks.onEndAChange?.(e.target.value);
      } else if (name === 'cfg-end-b') {
        this.callbacks.onEndBChange?.(e.target.value);
      } else if (name === 'cfg-extra') {
        this.callbacks.onExtraChange?.(e.target.value);
      } else if (name === 'cfg-urgent') {
        this.callbacks.onUrgentChange?.(e.target.checked);
      }
    });

    this.form.addEventListener('input', (e) => {
      if (e.target.name === 'cfg-qty') this.callbacks.onQuantityChange?.(e.target.value);
      if (e.target.name === 'cfg-eye-a') this.callbacks.onEyeSizeChange?.('a', e.target.value);
      if (e.target.name === 'cfg-eye-b') this.callbacks.onEyeSizeChange?.('b', e.target.value);
    });

    // Длина каната
    if (this.lengthInput) {
      this.lengthInput.addEventListener('input', () => {
        this.callbacks.onLengthChange?.(this.lengthInput.value);
      });
    }

    // Ползунок длины
    if (this.range) {
      this.range.addEventListener('input', () => {
        const v = Number(this.range.value);
        const min = Number(this.lengthInput.min);
        const max = Number(this.lengthInput.max);
        const len = Math.min(max, Math.max(min, Math.round((min + (max - min) * (v / 1000) ** 2) * 100) / 100));
        if (this.lengthInput) this.lengthInput.value = len;
        this.range.style.setProperty('--fill', `${v / 10}%`);
        this.callbacks.onLengthChange?.(len);
      });
    }

    // Количество
    this.$$('.stepper__button').forEach((btn) => {
      btn.addEventListener('click', () => {
        if (!this.qtyInput) return;
        const cur = parseInt(this.qtyInput.value, 10) || 1;
        const next = Math.min(999, Math.max(1, cur + Number(btn.dataset.step)));
        this.qtyInput.value = next;
        this.callbacks.onQuantityChange?.(next);
      });
    });

    // Отправка формы заявки
    this.form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (!this.form.reportValidity()) return;

      const formData = new FormData(this.form);
      const customerData = {
        name: formData.get('cfg-name') || '',
        email: formData.get('cfg-email') || '',
        phone: formData.get('cfg-phone') || '',
        comment: formData.get('cfg-comment') || '',
      };

      this.callbacks.onSubmit?.(customerData);
    });
  }

  /**
   * Отрисовка состояния калькулятора
   */
  render(snapshot) {
    if (!this.root || !snapshot) return;

    const { state, calculation, currentProduct, currentVariant } = snapshot;
    this.renderSelections(snapshot);
    this.renderConfiguration(snapshot);
    this.priceMessage.textContent = snapshot.priceStatus === 'loading' ? 'Загружаем цены…'
      : snapshot.priceStatus === 'error' ? 'Не удалось загрузить цены. Повторите запрос.'
      : calculation.totalPrice === null ? 'Для выбранной обработки нет однозначного тарифа. Выберите другой вариант.'
      : state.isUrgent && !snapshot.selectionValid ? 'Проверьте поля и ограничение на срочность: не более ' + snapshot.settings.urgent_max_splices + ' сращиваний в заказе.' : '';
    this.priceRetry.hidden = snapshot.priceStatus !== 'error';
    this.priceMessage.hidden = !this.priceMessage.textContent;

    // 1. Текстовые выводы
    this.out('caption', `${currentProduct?.name || 'Канат'} · ${state.diameterMm ?? '—'} мм`);
    this.out('mbl', currentVariant?.breaking_load_dan != null ? `${currentVariant.breaking_load_dan} daN` : '—');
    this.out('weight', currentVariant?.weight_g_per_m != null ? `${calculation.weightG} г` : '—');
    this.out('total', calculation.totalPrice === null ? 'Расчёт недоступен' : `${calculation.totalPrice} ${calculation.currency}`);
    this.out('material', currentProduct?.name || '—');
    this.out('length', `${state.lengthM} м`);
    this.out('charged-length', `${calculation.totalLengthM} м`);
    this.out('allowance', `${calculation.ropeLengthAllowanceM} м`);
    this.out('qty', state.quantity === null ? 'Укажите количество' : `${state.quantity} шт.`);
    this.out('each', state.quantity > 1 && calculation.totalPrice !== null ? `${Math.round(calculation.totalPrice / state.quantity * 100) / 100} ${calculation.currency} за штуку в среднем` : '');

    // 2. Детализация стоимости
    if (this.linesContainer) {
      const rows = [
        [`Канат: ${calculation.totalLengthM} м × ${currentVariant?.price_per_meter || 0} €/м × ${state.quantity ?? '—'} шт.`, calculation.ropeCost * state.quantity],
        ['Конец A, все изделия', calculation.endACost === null ? null : calculation.endACost * state.quantity],
        ['Конец B, все изделия', calculation.endBCost === null ? null : calculation.endBCost * state.quantity],
      ];
      if (calculation.extrasCost > 0) {
        rows.push(['Дополнительные опции', calculation.extrasCost]);
      }
      if (calculation.urgentCost > 0) {
        rows.push(['Срочное изготовление', calculation.urgentCost]);
      }
      rows.push(['Предварительный итог', calculation.totalPrice, true]);

      this.linesContainer.innerHTML = rows.map(([label, sum, strong]) => (
        `<li class="summary__line${strong ? ' summary__line--strong' : ''}">
          <span>${escapeHtml(label)}</span>
          <span class="summary__line-sum">${sum === null ? 'Нет тарифа' : escapeHtml(`${Math.round(sum * 100) / 100} ${calculation.currency}`)}</span>
        </li>`
      )).join('');
    }

    // 3. Обновление векторной схемы
    this.svgRenderer.render({
      diameterMm: state.diameterMm,
      ends: [
        { type: state.endA.typeCode, eye: state.endA.eyeSizeCm },
        { type: state.endB.typeCode, eye: state.endB.eyeSizeCm },
      ],
      lengthM: state.lengthM,
      sleeve: snapshot.extras.some((extra) => extra.code === 'sleeve' && state.selectedExtraIds.has(extra.id)),
    });
  }

  renderConfiguration({ state, extras, ends, settings, currentProduct }) {
    this.out('min-length', `${settings.min_length_m} м`);
    this.out('max-length', `${settings.max_length_m} м`);
    this.out('allowance-hint', `Укажите конечную длину изделия. Запас на каждую петлю: ${settings.splice_allowance_until_m} м до ${settings.splice_allowance_until_mm} мм включительно; ${settings.splice_allowance_over_m} м при большем диаметре.`);
    if (currentProduct?.apiVersion === 2) {
      this.out('intro', 'Выберите канат, цвет, конечную длину и обработку концов A и B. Запас на каждый обработанный конец добавится к оплачиваемой длине.');
      this.out('allowance-label', 'Запас на обработку концов');
      this.out('allowance-hint', `Запас на каждый обработанный конец: ${settings.splice_allowance_until_m} м до ${settings.splice_allowance_until_mm} мм включительно; ${settings.splice_allowance_over_m} м при большем диаметре.`);
      this.out('price-note', 'Расчёт включает запас на обработку концов. После отправки покажем сумму сервера; окончательную стоимость подтвердит менеджер.');
    }
    if (this.lengthInput) {
      this.lengthInput.min = settings.min_length_m;
      this.lengthInput.max = settings.max_length_m;
      this.lengthInput.step = 'any';
      if (document.activeElement !== this.lengthInput) this.lengthInput.value = state.lengthM ?? '';
      const ratio = (state.lengthM - Number(settings.min_length_m)) / (Number(settings.max_length_m) - Number(settings.min_length_m));
      if (this.range) {
        this.range.value = Number.isFinite(ratio) ? Math.sqrt(Math.max(0, Math.min(1, ratio))) * 1000 : 0;
        this.range.style.setProperty('--fill', `${Number(this.range.value) / 10}%`);
      }
    }
    if (this.qtyInput && document.activeElement !== this.qtyInput) this.qtyInput.value = state.quantity ?? '';
    for (const side of ['a', 'b']) {
      const end = state[side === 'a' ? 'endA' : 'endB'];
      const hasEye = ['eye', 'thimble', 'shackle', 'soft'].includes(end.typeCode);
      this.renderOptions(`end-${side}`, `cfg-end-${side}`, 'card', ends.map((item) => ({
        id: item.id ?? 'cut', title: item.name,
        meta: item.price === null ? 'Нет тарифа' : `${item.price} ${settings.currency || 'EUR'}`,
      })), end.spliceTypeId ?? 'cut');
      const input = this.form?.elements[`cfg-eye-${side}`];
      if (input) {
        input.disabled = !hasEye;
        input.closest('.configurator__eye').hidden = !hasEye;
        if (document.activeElement !== input) input.value = end.eyeSizeCm ?? '';
      }
      const selected = this.$(`input[name="cfg-end-${side}"]:checked`);
      const title = selected?.closest('label').querySelector('.option__title')?.textContent || end.typeCode;
      this.out(`end-${side}`, title + (hasEye ? `, ${end.eyeSizeCm ?? '—'} см` : ''));
    }
    const urgent = this.form?.elements['cfg-urgent'];
    if (urgent) urgent.checked = state.isUrgent;
    const units = { fixed: 'за заказ', per_item: 'за штуку', per_meter: 'за метр' };
    this.renderOptions('extras', 'cfg-extra', 'card', extras.map((extra) => ({
      id: extra.id,
      title: displayName(extra),
      meta: `${extra.price} ${extra.currency || 'EUR'} ${units[extra.billing_type] || ''}`,
    })), state.selectedExtraIds);
  }

  out(key, text) {
    this.$$(`[data-cfg-out="${key}"]`).forEach((el) => {
      el.textContent = text;
    });
  }

  renderSelections({ state, products, currentProduct, availableColors, selectionValid }) {
    const colors = availableColors || [];
    const colorName = displayName;
    this.renderOptions('products', 'cfg-material', 'card', (products || []).map((product) => ({
      id: product.product_id,
      title: product.name || 'Канат',
      meta: product.variants.length ? `от ${Math.min(...product.variants.map((v) => Number(v.price_per_meter)))} €/м` : 'Нет доступных диаметров',
    })), state.selectedProductId);
    this.renderOptions('variants', 'cfg-diameter', 'chip', (currentProduct?.variants || []).map((variant) => ({
      id: variant.id,
      title: `${variant.diameter_mm} мм`,
      meta: `${variant.price_per_meter} €/м`,
    })), state.selectedVariantId);
    this.renderOptions('colors', 'cfg-color', 'swatch', colors.map((color) => ({
      id: color.id, title: colorName(color), code: color.code, hex: color.hex,
    })), state.selectedColorId);
    const color = colors.find((item) => item.id === state.selectedColorId);
    if (this.preview) this.applyColor(this.preview, color);
    this.out('color', color ? colorName(color) : '—');
    this.out('size', `${state.diameterMm ?? '—'} мм · ${color ? colorName(color) : '—'}`);
    this.selectionValid = selectionValid === true;
    this.setSubmitLoading(this.isSubmitting);
  }

  renderOptions(group, name, modifier, options, selectedId) {
    const container = this.$(`[data-cfg-options="${group}"]`);
    if (!container) return;
    const signature = JSON.stringify(options);
    if (this.optionSignatures.get(group) !== signature) {
      const fragment = document.createDocumentFragment();
      options.forEach((option) => {
        const label = document.createElement('label');
        label.className = `option option--${modifier}`;
        const input = document.createElement('input');
        input.className = 'option__input';
        input.type = selectedId instanceof Set ? 'checkbox' : 'radio';
        input.name = name;
        input.value = String(option.id);
        const body = document.createElement('span');
        body.className = 'option__body';
        if (modifier === 'swatch') {
          const swatch = document.createElement('span');
          swatch.className = 'option__swatch rope-color';
          this.applyColor(swatch, option);
          swatch.setAttribute('aria-hidden', 'true');
          body.append(swatch);
        }
        const title = document.createElement('span');
        title.className = 'option__title';
        title.textContent = option.title;
        body.append(title);
        if (option.meta) {
          const meta = document.createElement('span');
          meta.className = 'option__meta';
          meta.textContent = option.meta;
          body.append(meta);
        }
        label.append(input, body);
        fragment.append(label);
      });
      if (!options.length) {
        const empty = document.createElement('p');
        empty.className = 'configurator__hint';
        empty.textContent = 'Нет доступных вариантов';
        fragment.append(empty);
      }
      container.replaceChildren(fragment);
      this.optionSignatures.set(group, signature);
    }
    container.querySelectorAll('input').forEach((input) => {
      input.checked = selectedId instanceof Set ? selectedId.has(Number(input.value)) : input.value === String(selectedId);
    });
  }

  applyColor(element, color) {
    const codes = ['blue', 'red', 'orange', 'black', 'grey', 'white'];
    element.classList.remove(...codes.map((code) => `rope-color--${code}`));
    ['--rope-base', '--rope-dark', '--rope-light'].forEach((key) => element.style.removeProperty(key));
    const code = color?.code === 'silver' ? 'grey' : color?.code;
    element.classList.add(`rope-color--${codes.includes(code) ? code : 'grey'}`);
    if (/^#[\da-f]{6}$/i.test(color?.hex || '')) {
      element.style.setProperty('--rope-base', color.hex);
      if (!codes.includes(code)) {
        element.style.setProperty('--rope-dark', color.hex);
        element.style.setProperty('--rope-light', color.hex);
      }
    }
  }

  setSubmitLoading(isLoading) {
    this.isSubmitting = isLoading;
    this.form?.querySelectorAll('fieldset').forEach(fieldset => { fieldset.disabled = isLoading || Boolean(this.submitted); });
    const btn = this.$('button[type="submit"]');
    if (btn) {
      btn.disabled = isLoading || !this.selectionValid || this.dataStatus !== 'ready' || this.submitted;
      btn.textContent = this.submitted ? 'Заявка отправлена' : isLoading ? 'Отправка заявки...' : 'Отправить на проверку';
    }
  }

  setDataStatus(status, message) {
    this.dataStatus = status;
    this.dataMessage.textContent = message;
    this.dataMessage.hidden = !message;
    updateLoadState(this.root, this.dataMessage, status);
    this.catalogLink.hidden = !['empty', 'missing'].includes(status);
    this.retryButton.hidden = !['error', 'empty'].includes(status);
    // Keep the form's geometry while loading so the following contact block
    // does not jump into the viewport and back out when the API responds.
    this.form.hidden = !['ready','loading'].includes(status);
    this.form.inert = status !== 'ready';
    this.setSubmitLoading(this.isSubmitting);
  }

  showSubmitSuccess(response) {
    if (this.submitStatus) {
      this.submitStatus.innerHTML = `
        <div style="color: #4CAF50; font-weight: 600; margin-top: 12px; font-size: 15px;">
          Заявка принята! Номер: <strong>${escapeHtml(response.request_number)}</strong>.<br>
          ${response.total_price != null ? `Сумма в ответе сервера: ${escapeHtml(response.total_price)} ${escapeHtml(response.currency || 'EUR')}.` : ''}
          Окончательную стоимость и срок подтвердит менеджер.
        </div>
      `;
      appendTrackingLink(this.submitStatus, response);
    }
  }

  showSubmitError(errorMessage) {
    if (this.submitStatus) {
      this.submitStatus.innerHTML = `
        <div style="color: #FF5252; font-weight: 500; margin-top: 12px; font-size: 14px;">
          Ошибка отправки: ${escapeHtml(errorMessage)}
        </div>
      `;
    }
  }
}
