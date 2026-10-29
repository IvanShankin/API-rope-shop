import {appendTrackingLink} from '../../utils/tracking.js?v=20261027.10';
import { catalogLink, updateLoadState } from '../../ui/load-state.js?v=20261027.10';
import { escapeHtml as esc, displayName } from '../../utils/text.js?v=20261027.10';

export class ServiceConfiguratorView {
  constructor(root) {
    this.root = root;
    this.form = root.querySelector('form');
    this.abort = new AbortController();
    this.form.innerHTML = `
      <fieldset class="service-configurator__steps" data-service-fields>
        <div class="configurator__step"><label class="configurator__step-title" for="${root.id}-material">Материал и конструкция вашего каната</label>
          <select class="field__input" id="${root.id}-material" name="material" required></select></div>
        <div class="configurator__step"><label class="configurator__step-title" for="${root.id}-service">Вид работы</label>
          <select class="field__input" id="${root.id}-service" name="service" required></select></div>
        <div class="configurator__step"><label class="configurator__step-title" for="${root.id}-diameter">Диаметр каната, мм</label>
          <input class="field__input" id="${root.id}-diameter" name="diameter" type="number" min="0.1" step="0.1" value="8" required></div>
        <div class="configurator__step" data-eye><label class="configurator__step-title" for="${root.id}-eye">Внутренний диаметр петли, см</label>
          <input class="field__input" id="${root.id}-eye" name="eye" type="number" min="0.1" step="0.1" value="10"></div>
        <div class="configurator__step"><label class="configurator__step-title" for="${root.id}-quantity">Количество работ</label>
          <input class="field__input" id="${root.id}-quantity" name="quantity" type="number" min="1" max="999" step="1" value="1" required>
          <p class="configurator__hint">Две петли — две работы. Замкнутое сращивание — одна работа на весь канат.</p></div>
        <fieldset class="configurator__step"><legend class="configurator__step-title">Дополнительные опции</legend><div data-extras></div></fieldset>
        <label class="check"><input class="check__input" name="urgent" type="checkbox"><span class="check__box"></span><span>Срочное изготовление</span></label>
      </fieldset>
      <aside class="service-summary">
        <p class="service-summary__label">Предварительная стоимость</p>
        <p class="service-summary__total" data-total>—</p><p data-breakdown></p>
        <p class="service-summary__note">Канат предоставляете вы — его стоимость не включена. Исполнение и окончательную цену подтвердим перед работой.</p>
        <fieldset class="summary__contacts" data-contact-fields><legend>Как с вами связаться</legend>
          <label class="field">Имя<input class="field__input" name="name" autocomplete="name" maxlength="255" required></label>
          <label class="field">E-mail<input class="field__input" name="email" type="email" autocomplete="email" required></label>
          <label class="field">Телефон<input class="field__input" name="phone" type="tel" autocomplete="tel" maxlength="100"></label>
          <label class="field">Пожелания к работе<textarea class="field__input" name="comment" rows="3"></textarea></label>
          <label class="check check--light"><input class="check__input" type="checkbox" name="consent" required><span class="check__box"></span><span>Согласен(-на) на обработку данных для ответа на заявку <a href="/legal/?document=privacy" lang="de">Datenschutz</a></span></label>
        </fieldset>
        <p data-validation role="status"></p>
        <button class="button button--dark" type="submit" disabled>Отправить на проверку</button>
        <p data-result role="status"></p>
      </aside>`;
    this.status = document.createElement('p');
    this.status.setAttribute('role', 'status');
    this.retry = document.createElement('button');
    this.retry.type = 'button';
    this.retry.className = 'button button--ghost button--small';
    this.retry.textContent = 'Повторить загрузку';
    this.form.before(this.status, this.retry);
    this.form.hidden = true;
    this.retry.hidden = true;
  }

  bind({ change, submit, retry }) {
    const options = { signal: this.abort.signal };
    this.form.addEventListener('input', event => {
      const el = event.target;
      if (['material', 'service', 'diameter', 'quantity', 'eye', 'urgent', 'extra'].includes(el.name)) change(el.name, el.type === 'checkbox' && el.name === 'urgent' ? el.checked : el.value);
    }, options);
    this.form.addEventListener('submit', event => {
      event.preventDefault();
      if (!this.form.reportValidity()) return;
      submit(Object.fromEntries(new FormData(this.form)));
    }, options);
    this.retry.addEventListener('click', retry, options);
  }

  statusMessage(state, message = '') {
    this.status.textContent = message;
    updateLoadState(this.root, this.status, state);
    this.retry.hidden = !['error', 'empty'].includes(state);
    this.form.hidden = state !== 'ready';
  }

  populate(model) {
    for (const [name, items] of [['material', model.materials], ['service', model.services]]) {
      this.form.elements[name].innerHTML = items.map(item => `<option value="${esc(item.id)}">${esc(displayName(item))}</option>`).join('');
      this.form.elements[name].value = model.state[name];
    }
    this.form.querySelector('[data-extras]').innerHTML = model.extras.map(extra => `<label class="check"><input class="check__input" type="checkbox" name="extra" value="${esc(extra.id)}" ${model.state.extras.has(Number(extra.id)) ? 'checked' : ''}><span class="check__box"></span><span>${esc(displayName(extra))} · ${esc(extra.price)} ${esc(extra.currency || model.settings.currency)} ${extra.billing_type === 'fixed' ? 'за заказ' : 'за работу'}</span></label>`).join('') || '<p>Нет доступных опций.</p>';
    this.render(model.calculate());
  }

  render(result) {
    this.valid = !result.error;
    this.form.querySelector('[data-eye]').hidden = !result.needsEye;
    this.form.elements.eye.disabled = !result.needsEye;
    this.form.elements.eye.required = result.needsEye;
    this.form.querySelector('[data-total]').textContent = result.total == null ? '—' : `${result.total.toFixed(2)} ${result.currency}`;
    this.form.querySelector('[data-breakdown]').textContent = result.error ? '' : `Работы: ${result.work.toFixed(2)} · Опции: ${result.extras.toFixed(2)} · Срочность: ${result.urgent.toFixed(2)} ${result.currency}`;
    this.form.querySelector('[data-validation]').textContent = result.error;
    this.setBusy(this.busy, this.sent);
  }

  setBusy(busy = false, sent = false) {
    this.busy = busy; this.sent = sent;
    this.form.querySelector('[data-service-fields]').disabled = busy || sent;
    this.form.querySelector('[data-contact-fields]').disabled = busy || sent;
    const button = this.form.querySelector('[type=submit]');
    button.disabled = busy || sent || !this.valid;
    button.textContent = sent ? 'Заявка отправлена' : busy ? 'Отправляем…' : 'Отправить на проверку';
  }

  result(message) { this.form.querySelector('[data-result]').textContent = message; }
  tracking(quote) { appendTrackingLink(this.form.querySelector('[data-result]'), quote); }
  destroy() { this.abort.abort(); }
}
