/* SPLICE — панель управления.
   Только макет: переключаются вкладки, всё остальное без логики. */
(function () {
  'use strict';

  /* боковые вкладки: показывают нужный раздел; кнопка «Сохранить» — только там, где есть что сохранять */
  function initSidebar() {
    const tabs = document.querySelectorAll('.sidebar__tab');
    const savebar = document.querySelector('.savebar');

    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        const name = tab.dataset.panel;
        tabs.forEach((t) => t.classList.toggle('sidebar__tab--active', t === tab));
        document.querySelectorAll('.panel').forEach((panel) => {
          const on = panel.id === `panel-${name}`;
          panel.hidden = !on;
          if (on && savebar) savebar.hidden = !panel.hasAttribute('data-savable');
        });
        window.scrollTo(0, 0);
      });
    });

    // кнопки внутри разделов, которые ведут в другой раздел
    document.querySelectorAll('[data-open-panel]').forEach((button) => {
      button.addEventListener('click', () => {
        const tab = document.querySelector(`.sidebar__tab[data-panel="${button.dataset.openPanel}"]`);
        if (tab) tab.click();
      });
    });
  }

  /* фильтр отзывов: показывает нужный список */
  function initReviewFilters() {
    const tabs = document.querySelectorAll('.filters__tab');

    tabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        const name = tab.dataset.filter;
        tabs.forEach((t) => t.classList.toggle('filters__tab--active', t === tab));
        document.querySelectorAll('.reviews').forEach((list) => {
          list.hidden = list.dataset.list !== name;
        });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initReviewFilters();
  });
})();
