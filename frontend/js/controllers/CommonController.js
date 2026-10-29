import {initContacts} from '../views/common/ContactsView.js?v=20261027.10';
import {initReviews} from '../views/common/ReviewsView.js?v=20261027.10';
import { BaseController } from './BaseController.js?v=20261027.10';
import { HeaderView } from '../views/common/HeaderView.js?v=20261027.10';
import { WorkGalleryView } from '../views/common/WorkGalleryView.js?v=20261027.10';
import { API_CONFIG } from '../api/config.js?v=20261027.10';
import { initSiteContent } from '../views/common/SiteContentView.js?v=20261028.17';

export class CommonController extends BaseController {
  async init() {
    await super.init();

    // 1. Инициализация шапки сайта
    this.headerView = new HeaderView();

    // 2. Кнопка "Наверх"
    this.initToTop();

    // 3. Анимации появления при скролле
    this.initReveal();

    // 4. Галереи Swiper (если есть на странице)
    if(API_CONFIG.CATALOG_V2 && !document.querySelector('.admin')) {
      initContacts();
      initReviews();
      await initSiteContent({initWork:root=>new WorkGalleryView(root),initSwiper:root=>this.initSwipers(root)});
    } else {
      this.initSwipers();
      document.querySelectorAll('.work-gallery').forEach(root => new WorkGalleryView(root));
    }
  }

  initToTop() {
    const button = document.querySelector('.to-top');
    if (!button) return;

    const bar = button.querySelector('.to-top__bar');
    const configBar = document.querySelector('.configurator__bar');
    let raf = 0;

    const update = () => {
      raf = 0;
      const y = window.scrollY;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      button.classList.toggle('to-top--visible', y > window.innerHeight * 0.8);
      if (bar) {
        bar.style.strokeDashoffset = (1 - (max > 0 ? Math.min(1, y / max) : 0)).toFixed(4);
      }
      if (configBar) {
        const rect = configBar.getBoundingClientRect();
        const shown = getComputedStyle(configBar).display !== 'none';
        button.classList.toggle('to-top--raised', shown && rect.top < window.innerHeight && rect.bottom > 0);
      }
    };

    const request = () => { if (!raf) raf = requestAnimationFrame(update); };
    window.addEventListener('scroll', request, { passive: true });
    window.addEventListener('resize', request);
    button.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
    update();
  }

  initReveal() {
    const items = document.querySelectorAll('[data-reveal]');
    if (!items.length) return;

    const show = (el) => el.classList.add(...el.dataset.reveal.split(' '));

    if (!('IntersectionObserver' in window)) {
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

  initSwipers(root = null) {
    // Если на странице подключен глобальный Swiper и есть галереи
    if (typeof window.Swiper !== 'function') return;

    const galleries = root ? [root] : document.querySelectorAll('.gallery');
    galleries.forEach((gallery) => {
      const viewport = gallery.querySelector('.gallery__viewport');
      if (viewport) {
        new window.Swiper(viewport, {
          wrapperClass: 'gallery__track',
          slideClass: 'gallery__slide',
          slideActiveClass: 'gallery__slide--active',
          slideNextClass: 'gallery__slide--next',
          slidePrevClass: 'gallery__slide--prev',
          containerModifierClass: 'gallery__viewport--',
          slidesPerView: 1,
          spaceBetween: 24,
          speed: 800,
          rewind: true,
          grabCursor: true,
          navigation: {
            prevEl: gallery.querySelector('.gallery__button--prev'),
            nextEl: gallery.querySelector('.gallery__button--next'),
          },
        });
      }
    });
  }
}
