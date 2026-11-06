/* SPLICE — макет, БЭМ */
(function () {
  'use strict';

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function loadFonts() {
    if (!document.fonts || !document.fonts.load) return Promise.resolve();
    return Promise.all([
      document.fonts.load('500 100px "Inter Tight"'),
      document.fonts.load('400 16px "Manrope"')
    ]).catch(() => {});
  }

  /* шапка */
  function initHeader() {
    const header = document.querySelector('.header');
    const burger = header.querySelector('.burger');
    const menu = document.getElementById('mobile-menu');

    const updateHeaderHeight = () => {
      document.documentElement.style.setProperty('--header-height', `${header.getBoundingClientRect().height}px`);
    };
    new ResizeObserver(updateHeaderHeight).observe(header);
    updateHeaderHeight();

    function toggle(open) {
      burger.setAttribute('aria-expanded', String(open));
      burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
      burger.classList.toggle('burger--active', open);
      header.classList.toggle('header--menu-open', open);
      document.body.classList.toggle('page__body--locked', open);
      menu.hidden = !open;
    }

    burger.addEventListener('click', () => toggle(burger.getAttribute('aria-expanded') !== 'true'));
    menu.addEventListener('click', (e) => {
      if (e.target.closest('a')) toggle(false);
    });
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && burger.getAttribute('aria-expanded') === 'true') toggle(false);
    });
    window.addEventListener('resize', () => {
      if (window.innerWidth > 1180) toggle(false);
    });

    const onScroll = () => header.classList.toggle('header--scrolled', window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* первый экран */
  function initHero(section) {
    const images = section.querySelectorAll('.hero-stage__rope img');

    const imagesReady = Promise.all(Array.from(images, (img) => (
      img.complete ? Promise.resolve() : new Promise((resolve) => {
        img.addEventListener('load', resolve, { once: true });
        img.addEventListener('error', resolve, { once: true });
      })
    )));

    loadFonts().then(() => {
      return imagesReady;
    }).then(() => {
      requestAnimationFrame(() => section.classList.add('hero--ready'));
    });
  }

  /* кнопка «наверх»: появляется после первого экрана, кольцо — прогресс прокрутки */
  function initToTop() {
    const button = document.querySelector('.to-top');
    if (!button) return;
    const bar = button.querySelector('.to-top__bar');
    const configBar = document.querySelector('.configurator__bar');
    let raf = 0;

    function update() {
      raf = 0;
      const y = window.scrollY;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      button.classList.toggle('to-top--visible', y > window.innerHeight * 0.8);
      bar.style.strokeDashoffset = (1 - (max > 0 ? Math.min(1, y / max) : 0)).toFixed(4);

      // плашка с итогом конфигуратора видна только на планшете и телефоне — не перекрываем её
      if (configBar) {
        const rect = configBar.getBoundingClientRect();
        const shown = getComputedStyle(configBar).display !== 'none';
        button.classList.toggle('to-top--raised', shown && rect.top < window.innerHeight && rect.bottom > 0);
      }
    }

    const request = () => { if (!raf) raf = requestAnimationFrame(update); };
    window.addEventListener('scroll', request, { passive: true });
    window.addEventListener('resize', request);
    button.addEventListener('click', () => window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' }));
    update();
  }

  /* появление при прокрутке: data-reveal="класс-модификатор" */
  function initReveal() {
    const items = document.querySelectorAll('[data-reveal]');
    const show = (el) => el.classList.add(...el.dataset.reveal.split(' '));

    if (reduceMotion || !('IntersectionObserver' in window)) {
      items.forEach(show);
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        show(entry.target);
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -15% 0px' });

    items.forEach((el) => observer.observe(el));
  }

  /* витрина: пункты списка переключают фото (Swiper, классы переименованы в БЭМ) */
  function initShowcase(root) {
    const tabs = Array.from(root.querySelectorAll('.showcase__tab'));
    const media = root.querySelector('.showcase__media');
    if (typeof window.Swiper !== 'function' || !tabs.length) return;

    function setActive(index) {
      tabs.forEach((tab, i) => {
        const on = i === index;
        tab.classList.toggle('showcase__tab--active', on);
        tab.setAttribute('aria-pressed', String(on));
      });
    }

    const swiper = new window.Swiper(media, {
      wrapperClass: 'showcase__track',
      slideClass: 'showcase__slide',
      slideActiveClass: 'showcase__slide--active',
      slideNextClass: 'showcase__slide--next',
      slidePrevClass: 'showcase__slide--prev',
      slideVisibleClass: 'showcase__slide--visible',
      slideFullyVisibleClass: 'showcase__slide--fully-visible',
      containerModifierClass: 'showcase__media--',

      effect: 'fade',
      fadeEffect: { crossFade: true },
      speed: reduceMotion ? 0 : 700,
      rewind: true,

      a11y: {
        notificationClass: 'showcase__notification',
        containerMessage: 'Мои работы',
        containerRoleDescriptionMessage: 'карусель',
        itemRoleDescriptionMessage: 'слайд',
        slideLabelMessage: '{{index}} из {{slidesLength}}'
      },

      on: {
        slideChange: (sw) => setActive(sw.activeIndex)
      }
    });

    const canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => swiper.slideTo(i));
      if (canHover) tab.addEventListener('mouseenter', () => swiper.slideTo(i));
    });

    setActive(swiper.activeIndex);
  }

  /* галерея: слайд во всю ширину контейнера (Swiper, классы переименованы в БЭМ) */
  function initGallery(root) {
    if (typeof window.Swiper !== 'function') return;

    new window.Swiper(root.querySelector('.gallery__viewport'), {
      wrapperClass: 'gallery__track',
      slideClass: 'gallery__slide',
      slideActiveClass: 'gallery__slide--active',
      slideNextClass: 'gallery__slide--next',
      slidePrevClass: 'gallery__slide--prev',
      slideVisibleClass: 'gallery__slide--visible',
      slideFullyVisibleClass: 'gallery__slide--fully-visible',
      containerModifierClass: 'gallery__viewport--',

      slidesPerView: 1,
      spaceBetween: 24,
      speed: reduceMotion ? 0 : 900,
      rewind: true,
      grabCursor: true,

      navigation: {
        prevEl: root.querySelector('.gallery__button--prev'),
        nextEl: root.querySelector('.gallery__button--next'),
        disabledClass: 'gallery__button--disabled',
        hiddenClass: 'gallery__button--hidden',
        lockClass: 'gallery__button--lock'
      },

      keyboard: { enabled: true, onlyInViewport: true },

      a11y: {
        notificationClass: 'gallery__notification',
        containerMessage: 'Фото благотворительности',
        containerRoleDescriptionMessage: 'карусель',
        itemRoleDescriptionMessage: 'слайд',
        slideLabelMessage: '{{index}} из {{slidesLength}}',
        prevSlideMessage: 'Предыдущее фото',
        nextSlideMessage: 'Следующее фото',
        firstSlideMessage: 'Первое фото',
        lastSlideMessage: 'Последнее фото'
      }
    });
  }

  /* старт */
  document.addEventListener('DOMContentLoaded', async () => {
    initHeader();
    const hero = document.querySelector('.hero');
    if (hero) initHero(hero);
    document.querySelectorAll('.showcase').forEach(initShowcase);
    initReveal();
    initToTop();
    const {initContacts}=await import('./views/common/ContactsView.js?v=20261106.1');initContacts();
    const {initReviews}=await import('./views/common/ReviewsView.js?v=20261106.1');initReviews();
    const [{initSiteContent},{WorkGalleryView}]=await Promise.all([
      import('./views/common/SiteContentView.js?v=20261106.1'),
      import('./views/common/WorkGalleryView.js?v=20261106.1'),
    ]);
    await initSiteContent({initSwiper:initGallery,initWork:root=>new WorkGalleryView(root)});
  });
})();
