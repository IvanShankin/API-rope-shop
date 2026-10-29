import { BaseView } from '../BaseView.js?v=20261027.10';

export class HeaderView extends BaseView {
  constructor() {
    super('.header');
    this.init();
  }

  init() {
    if (!this.root) return;

    this.burger = this.$('.burger');
    this.menu = document.getElementById('mobile-menu');

    if (this.burger && this.menu) {
      this.initBurger();
    }

    this.initHeaderHeight();
    this.initScrollEffect();
  }

  initHeaderHeight() {
    const updateHeaderHeight = () => {
      document.documentElement.style.setProperty('--header-height', `${this.root.getBoundingClientRect().height}px`);
    };
    new ResizeObserver(updateHeaderHeight).observe(this.root);
    updateHeaderHeight();
  }

  initBurger() {
    const toggle = (open) => {
      this.burger.setAttribute('aria-expanded', String(open));
      this.burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
      this.burger.classList.toggle('burger--active', open);
      this.root.classList.toggle('header--menu-open', open);
      document.body.classList.toggle('page__body--locked', open);
      this.menu.hidden = !open;
    };

    this.burger.addEventListener('click', () => {
      const isOpen = this.burger.getAttribute('aria-expanded') === 'true';
      toggle(!isOpen);
    });

    this.menu.addEventListener('click', (e) => {
      if (e.target.closest('a')) toggle(false);
    });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.burger.getAttribute('aria-expanded') === 'true') toggle(false);
    });

    window.addEventListener('resize', () => {
      if (window.innerWidth > 1180) toggle(false);
    });
  }

  initScrollEffect() {
    const onScroll = () => this.root.classList.toggle('header--scrolled', window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

}
