/**
 * Базовый класс для всех компонентов View
 */
export class BaseView {
  constructor(root = document) {
    this.root = typeof root === 'string' ? document.querySelector(root) : root;
  }

  $(selector) {
    return this.root ? this.root.querySelector(selector) : null;
  }

  $$(selector) {
    return this.root ? Array.from(this.root.querySelectorAll(selector)) : [];
  }

  on(element, event, handler, options = {}) {
    if (!element) return;
    element.addEventListener(event, handler, options);
  }
}
