/**
 * Мобильное меню админки (ширина ≤ 1000px).
 *
 * На узких экранах боковая панель `.sidebar` превращается в выдвижное меню
 * на весь экран: кнопка `.admin-burger` в правом верхнем углу открывает её
 * поверх контента, подложка `.admin-nav-backdrop`, клавиша Escape и выбор
 * любого таба (в том числе программный `tab.click()`) закрывают меню.
 * Пока меню открыто, страница не прокручивается — прокручивается только
 * сама панель. На десктопе кнопка и подложка скрыты, панель остаётся колонкой.
 *
 * Пока модуль не выполнился, у `.admin` нет класса `.admin-nav-ready`,
 * поэтому CSS-правила меню не действуют и панель показывается как раньше.
 * Обработчики табов здесь не дублируются: меню закрывает собственная
 * делегированная проверка клика, поэтому работают и AdminView/AdminNavigation,
 * и необязательный js/admin.js.
 */
const MOBILE_QUERY = '(max-width: 1000px)';
const LABEL_OPEN = 'Открыть меню разделов';
const LABEL_CLOSE = 'Закрыть меню разделов';

function initAdminMobileNav() {
  const root = document.querySelector('.admin');
  const burger = root?.querySelector('.admin-burger');
  const sidebar = root?.querySelector('#admin-sidebar') || root?.querySelector('.sidebar');
  const backdrop = root?.querySelector('.admin-nav-backdrop');
  const body = document.body;
  if (!root || !burger || !sidebar) return;

  const mobile = window.matchMedia(MOBILE_QUERY);
  let opened = false;

  const firstTab = () => {
    const tabs = [...sidebar.querySelectorAll('.sidebar__tab')];
    return tabs.find(tab => !tab.hidden && tab.offsetWidth > 0) || tabs[0] || null;
  };

  const focus = (element) => {
    if (!element) return;
    try { element.focus({ preventScroll: true }); } catch { element.focus(); }
  };

  const sync = () => {
    root.classList.toggle('admin-nav-open', opened);
    // Пока меню открыто, страница не прокручивается: html и body заблокированы,
    // прокручивается только сама панель (у неё overflow-y: auto).
    document.documentElement.classList.toggle('admin-nav-lock', opened);
    body.classList.toggle('admin-nav-lock', opened);
    burger.setAttribute('aria-expanded', String(opened));
    burger.setAttribute('aria-label', opened ? LABEL_CLOSE : LABEL_OPEN);
    if (backdrop) backdrop.setAttribute('aria-hidden', String(!opened));
  };

  const openNav = () => {
    if (opened || !mobile.matches) return;
    opened = true;
    sync();
    requestAnimationFrame(() => focus(firstTab()));
  };

  const closeNav = ({ restoreFocus = true } = {}) => {
    if (!opened) return;
    opened = false;
    sync();
    if (restoreFocus) focus(burger);
  };

  burger.addEventListener('click', () => {
    if (opened) closeNav();
    else openNav();
  });

  backdrop?.addEventListener('click', () => closeNav());

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && opened) closeNav();
  });

  // Любой выбор таба (клик мышью, Tab+Enter или программный tab.click())
  // закрывает ящик. Ссылки и выход тоже закрывают меню.
  sidebar.addEventListener('click', (event) => {
    if (!opened) return;
    if (event.target.closest('.sidebar__tab, .sidebar__link, .sidebar__logout')) closeNav();
  });

  const onViewportChange = () => {
    if (!mobile.matches) closeNav({ restoreFocus: false });
  };
  if (typeof mobile.addEventListener === 'function') mobile.addEventListener('change', onViewportChange);
  else mobile.addListener(onViewportChange);

  sync();
  root.classList.add('admin-nav-ready');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAdminMobileNav, { once: true });
} else {
  initAdminMobileNav();
}
