// Плашка «Не показывается на сайте» в редакторах админки.
// Работает сама по себе: находит в открытой форме галочку показа (is_active или is_published)
// и показывает над формой заметное предупреждение, когда галочка снята.
// Строки списков (диаметры каната и т.п.) не трогаем — только главная галочка формы.

const BOX = 'input[type="checkbox"][name="is_active"], input[type="checkbox"][name="is_published"]';
const SKIP = '.tick--compact, .col-active, tr';
const EYE_OFF = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M3 3l18 18"/><path d="M10.6 5.1A10.4 10.4 0 0 1 12 5c6 0 9.5 7 9.5 7a17 17 0 0 1-3.2 4.2M6.1 6.6C3.9 8.2 2.5 12 2.5 12S6 19 12 19c1.6 0 3-.4 4.3-1"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>';
const EYE = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M2.5 12S6 5 12 5s9.5 7 9.5 7-3.5 7-9.5 7S2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/></svg>';

const labelOf = box => (box.closest('label')?.textContent || '').replace(/\s+/g, ' ').trim() || 'Показывать на сайте';

function findBox(form) {
  return [...form.querySelectorAll(BOX)].find(box => !box.closest(SKIP) && box.form === form) || null;
}

// Отзыв виден, только если он одобрен и отмечен к показу.
function state(form, box) {
  if (box.name !== 'is_published') return { visible: box.checked };
  const status = form.elements.namedItem('status');
  const approved = !status || status.value === 'confirmed';
  return { visible: box.checked && approved, approved, status: status?.value };
}

function texts(form, box, now) {
  const label = labelOf(box);
  if (/текст/i.test(label)) return {
    hidden: 'Ваши тексты не используются',
    hiddenNote: `На сайте показан исходный текст страницы. Чтобы показать тексты отсюда, отметьте «${label}» и сохраните.`,
    willHide: 'Тексты отсюда пропадут с сайта после сохранения',
    willHideNote: 'Вместо них на сайте будет исходный текст страницы.',
    show: 'Включить тексты',
  };
  if (/галере/i.test(label)) return {
    hidden: 'Фото не показывается в галерее',
    hiddenNote: `Посетители сайта его не видят: снята галочка «${label}».`,
    willHide: 'Фото пропадёт из галереи после сохранения',
    willHideNote: 'Посетители сайта перестанут его видеть.',
    show: 'Показать в галерее',
  };
  if (box.name === 'is_published') {
    const reason = now.approved === false
      ? (now.status === 'rejected' ? 'отзыв отклонён.' : 'отзыв ещё не одобрен (выберите «Одобрен» в поле «Проверка отзыва»).')
      : `снята галочка «${label}».`;
    return {
      hidden: 'Отзыв не показывается на сайте',
      hiddenNote: `Посетители сайта его не видят: ${reason}`,
      willHide: 'Отзыв пропадёт с сайта после сохранения',
      willHideNote: 'Посетители сайта перестанут его видеть.',
      show: now.approved === false ? 'Одобрить и показать' : 'Показать на сайте',
    };
  }
  return {
    hidden: 'Не показывается на сайте',
    hiddenNote: `Посетители сайта это не видят: снята галочка «${label}».`,
    willHide: 'Пропадёт с сайта после сохранения',
    willHideNote: 'Посетители сайта перестанут это видеть.',
    show: 'Показать на сайте',
  };
}

function update(form) {
  const banner = form.querySelector(':scope > .admin-hidden-banner');
  const box = banner && findBox(form);
  if (!box) { banner?.remove(); return; }
  const now = state(form, box);
  const wasVisible = banner.dataset.initial === '1';
  let mode = '';
  if (!now.visible) mode = wasVisible ? 'will-hide' : 'hidden';
  else if (!wasVisible) mode = 'will-show';
  banner.hidden = !mode;
  banner.dataset.mode = mode;
  if (!mode) return;
  const t = texts(form, box, now);
  const title = { hidden: t.hidden, 'will-hide': t.willHide, 'will-show': 'Появится на сайте после сохранения' }[mode];
  const note = { hidden: t.hiddenNote, 'will-hide': t.willHideNote, 'will-show': 'Нажмите «Сохранить», чтобы изменения вступили в силу.' }[mode];
  banner.querySelector('.admin-hidden-banner__icon').innerHTML = mode === 'will-show' ? EYE : EYE_OFF;
  banner.querySelector('.admin-hidden-banner__title').textContent = title;
  banner.querySelector('.admin-hidden-banner__note').textContent = note;
  const button = banner.querySelector('.admin-hidden-banner__action');
  button.hidden = mode === 'will-show';
  button.textContent = t.show;
}

function setup(form) {
  const box = findBox(form);
  const existing = form.querySelector(':scope > .admin-hidden-banner');
  if (!box) { existing?.remove(); return; }
  if (existing) return;
  const banner = document.createElement('div');
  banner.className = 'admin-hidden-banner';
  banner.setAttribute('role', 'status');
  banner.dataset.initial = state(form, box).visible ? '1' : '0';
  banner.innerHTML = '<span class="admin-hidden-banner__icon"></span>'
    + '<div class="admin-hidden-banner__body"><p class="admin-hidden-banner__title"></p><p class="admin-hidden-banner__note"></p></div>'
    + '<button class="btn admin-hidden-banner__action" type="button"></button>';
  banner.querySelector('.admin-hidden-banner__action').addEventListener('click', () => {
    const target = findBox(form);
    if (!target) return;
    if (target.name === 'is_published') {
      const status = form.elements.namedItem('status');
      if (status && status.value !== 'confirmed') {
        status.value = 'confirmed';
        status.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
    target.checked = true;
    target.dispatchEvent(new Event('input', { bubbles: true }));
    target.dispatchEvent(new Event('change', { bubbles: true }));
    target.focus({ preventScroll: true });
  });
  form.prepend(banner);
  update(form);
}

let pending = 0;
const scan = () => {
  pending = 0;
  document.querySelectorAll('.admin form').forEach(setup);
};
const schedule = () => { if (!pending) pending = requestAnimationFrame(scan); };

function init() {
  scan();
  new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true });
  const onChange = event => {
    const form = event.target.closest?.('form');
    if (form?.querySelector(':scope > .admin-hidden-banner')) update(form);
  };
  document.addEventListener('change', onChange);
  document.addEventListener('input', onChange);
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
else init();
