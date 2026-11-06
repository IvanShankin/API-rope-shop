const sections = ['requests', 'catalog', 'groups', 'colors', 'configurator', 'content', 'gallery', 'reviews', 'contacts', 'settings'];
// Раздел по умолчанию: админка открывается на заявках покупателей.
const DEFAULT_SECTION = 'requests';
const idValue = value => /^\d+$/.test(String(value || '')) && Number(value) > 0 ? String(value) : '';

export function readAdminRoute(url) {
  const params = new URL(url).searchParams;
  const section = sections.includes(params.get('section')) ? params.get('section') : DEFAULT_SECTION;
  if (section === 'configurator' && params.get('type') === 'links') {
    return { section: 'catalog', type: '', record: idValue(params.get('record')) };
  }
  return { section, type: params.get('type') || '', record: idValue(params.get(section === 'catalog' ? 'product' : 'record')) };
}

export function adminRouteUrl(route, base) {
  const url = new URL(base);
  ['section', 'type', 'product', 'record'].forEach(key => url.searchParams.delete(key));
  url.searchParams.set('section', route.section);
  if (route.type) url.searchParams.set('type', route.type);
  if (idValue(route.record)) url.searchParams.set(route.section === 'catalog' ? 'product' : 'record', route.record);
  return url.pathname + url.search + url.hash;
}

export class AdminNavigation {
  constructor(admin) {
    this.admin = admin;
    this.root = admin.view.root;
    this.controllers = { catalog: admin.productsController, groups: admin.groupsController,
      colors: admin.colorsController, configurator: admin.configController,
      ...(admin.contentController?{content:admin.contentController,gallery:admin.galleryController,reviews:admin.reviewsController,contacts:admin.contactsController,settings:admin.settingsController}:{}) };
    this.events = new AbortController();
    this.section = null;
    this.restoring = false;
    this.depth = 0;
    this.states = {};
    try { this.states = JSON.parse(sessionStorage.getItem('rope-admin-view') || '{}') || {}; } catch {}
    for (const [section, controller] of Object.entries(this.controllers)) {
      for (const name of ['load', 'select', 'save', 'remove']) {
        const original = controller[name].bind(controller);
        controller[name] = async (...args) => {
          const track = !this.restoring && this.section === section && this.depth === 0;
          if (track) this.capture();
          const previousKey = this.currentKey;
          this.depth++;
          try { return await original(...args); }
          finally {
            this.depth--;
            if (track) {
              this.sync(name === 'select' || name === 'load' ? 'push' : 'replace');
              if (name === 'save' && previousKey !== this.currentKey && this.states[previousKey]) {
                this.states[this.currentKey] = this.states[previousKey];
              }
              this.applyDefaultDisclosures();
              this.restoring = true;
              try {
                await this.restore({ editor: name === 'select' && this.mobileLayout() && Boolean(this.routeFor().record) });
              }
              finally {
                this.restoring = false;
                this.refreshSavebar();
                if (this.pending) { const next = this.pending; this.pending = null; this.go(next.route, next.mode); }
              }
            }
          }
        };
      }
    }
    this.admin.view.initSavebar?.({ isDirty: () => this.currentDirty(), save: () => this.saveCurrent() });
  }
  currentDirty() {
    if (this.section === 'requests') return Boolean(this.admin.view.requestDirty?.());
    const controller = this.controllers[this.section];
    if (!controller) return false;
    const view = controller.view;
    if (typeof view?.dirty === 'function') return view.dirty();
    if (typeof view?.hasChanges === 'function') return view.hasChanges();
    if (typeof controller.dirty === 'function') return controller.dirty();
    return false;
  }
  submitForm(form) {
    if (typeof form.requestSubmit === 'function') form.requestSubmit();
    else form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  }
  saveCurrent() {
    if (this.restoring) return;
    const panel = this.panel();
    if (!panel) return;
    if (this.section === 'requests') {
      const form = panel.querySelector('[data-request-edit]');
      if (form) this.submitForm(form);
      return;
    }
    if (this.section === 'catalog') {
      const button = panel.querySelector('[data-products-save]');
      if (button) { button.click(); return; }
    }
    const view = this.controllers[this.section]?.view;
    const priceSave = panel.querySelector('[data-tariff-save]');
    if (priceSave && !priceSave.disabled && view?.recordList?.priceDrafts?.size && !view.editorDirty?.()) {
      priceSave.click();
      return;
    }
    const form = panel.querySelector('[data-settings-form]')
      || panel.querySelector('[data-color-form]')
      || panel.querySelector('[data-contacts-form]')
      || panel.querySelector('[data-config-editor] form')
      || panel.querySelector('[data-content-editor] form')
      || panel.querySelector('[data-product-form]')
      || panel.querySelector('form');
    if (form) this.submitForm(form);
  }
  applyDefaultDisclosures() {
    if (this.section !== 'catalog') return;
    const editor = this.panel()?.querySelector('[data-product-editor]');
    if (!editor) return;
    editor.querySelectorAll(':scope > details.admin-disclosure').forEach(block => { block.open = false; });
  }
  editorTarget() {
    const panel = this.panel();
    if (!panel) return null;
    for (const selector of ['[data-product-editor]', '[data-color-editor]', '[data-config-editor]', '[data-content-editor]', '[data-request-content]']) {
      const target = panel.querySelector(selector);
      if (target && !target.hidden && target.children.length) return target;
    }
    return null;
  }
  mobileLayout() { return window.matchMedia('(max-width: 1000px)').matches; }
  scrollToEditor() {
    const target = this.editorTarget();
    if (!target) return false;
    const top = Math.max(0, window.scrollY + target.getBoundingClientRect().top - 88);
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top, behavior: reduceMotion ? 'auto' : 'smooth' });
    return true;
  }
  scrollToEditorWhenReady() {
    if (!this.mobileLayout()) return;
    clearInterval(this.editorScrollTimer);
    let tries = 0;
    this.editorScrollTimer = setInterval(() => {
      if (this.editorTarget()) {
        clearInterval(this.editorScrollTimer);
        this.scrollToEditor();
      } else if (++tries > 30) {
        clearInterval(this.editorScrollTimer);
      }
    }, 120);
  }
  refreshSavebar() { this.admin.view.refreshSavebar?.(); }
  routeFor(section = this.section) {
    const controller = this.controllers[section];
    if(!controller&&section!=='requests')return this.routeFor(DEFAULT_SECTION);
    if (section === 'catalog') return { section, record: idValue(controller.product?.product_id) };
    if (section === 'colors') return { section, record: idValue(controller.color?.id) };
    if (section === 'requests') return { section, record: idValue(this.admin.view.requestId) };
    return { section, type: controller.section, record: idValue(controller.item?.product_id ?? controller.item?.id) };
  }
  key(route = this.routeFor()) { return `${route.section}:${route.type || ''}:${route.record || ''}`; }
  panel() { return this.root.querySelector(`#panel-${this.section}`); }
  details() {
    const counts = new Map();
    return [...(this.panel()?.querySelectorAll('details') || [])].map(block => {
      const ancestors = [];
      let parent = block;
      while (parent?.tagName === 'DETAILS') {
        const variant = parent.querySelector(':scope > form[data-variant-form]');
        ancestors.unshift(variant ? `variant:${variant.dataset.id || 'new'}` : parent.querySelector(':scope > summary')?.textContent.trim() || 'block');
        parent = parent.parentElement.closest('details');
      }
      const label = ancestors.join('/');
      const index = counts.get(label) || 0;
      counts.set(label, index + 1);
      return { block, key: `${label}:${index}` };
    });
  }
  capture() {
    if (!this.section || this.restoring || this.depth) return;
    this.states[this.currentKey] = { scroll: window.scrollY, blocks: Object.fromEntries(this.details().map(({block, key}) => [key, block.open])) };
    const keys = Object.keys(this.states);
    if (keys.length > 60) delete this.states[keys[0]];
    try { sessionStorage.setItem('rope-admin-view', JSON.stringify(this.states)); } catch {}
  }
  sync(mode = 'replace') {
    if (!this.section || this.restoring) return;
    const route = this.routeFor();
    const url = adminRouteUrl(route, location.href);
    if (url !== location.pathname + location.search + location.hash) history[mode === 'push' ? 'pushState' : 'replaceState']({}, '', url);
    this.currentKey = this.key(route);
  }
  async restore({ editor = false } = {}) {
    const state = this.states[this.currentKey];
    if (state?.blocks) for (const {block, key} of this.details()) {
      if (typeof state.blocks[key] === 'boolean') block.open = state.blocks[key];
    }
    // Background tabs can suspend animation frames; navigation must still finish.
    await new Promise(resolve => {
      const timer = setTimeout(resolve, 150);
      requestAnimationFrame(() => requestAnimationFrame(() => { clearTimeout(timer); resolve(); }));
    });
    if (editor && this.scrollToEditor()) return;
    window.scrollTo({ top: Math.max(0, Number(state?.scroll) || 0), behavior: 'instant' });
  }
  start() {
    const options = { signal: this.events.signal };
    history.scrollRestoration = 'manual';
    window.addEventListener('pagehide', () => this.capture(), options);
    window.addEventListener('beforeunload', () => this.capture(), options);
    window.addEventListener('scroll', () => { clearTimeout(this.timer); this.timer = setTimeout(() => this.capture(), 120); }, options);
    this.root.addEventListener('toggle', () => { if (!this.restoring) this.capture(); }, { ...options, capture: true });
    this.root.addEventListener('click', event => {
      if (event.target.closest('[data-product-new], [data-config-new], [data-color-new]')) {
        this.capture(); queueMicrotask(() => this.sync('push'));
        this.scrollToEditorWhenReady();
      }
    }, options);
    this.root.addEventListener('admin:request-open', () => this.sync('push'), options);
    this.root.addEventListener('admin:product-new', () => {
      this.sync('push');
      this.applyDefaultDisclosures();
      if (this.mobileLayout()) this.scrollToEditor();
    }, options);
    window.addEventListener('popstate', () => this.go(readAdminRoute(location.href), 'pop'), options);
    this.go(readAdminRoute(location.href), 'replace');
  }
  async go(route, mode = 'push') {
    if (this.restoring) { this.pending = { route, mode }; return; }
    clearInterval(this.editorScrollTimer);
    if (Object.values(this.controllers).some(controller => controller.busy) || this.admin.view.requestBusy) {
      this.sync(); return;
    }
    this.capture();
    this.restoring = true;
    try {
      this.section = sections.includes(route.section) && (route.section==='requests'||this.controllers[route.section]) ? route.section : DEFAULT_SECTION;
      this.admin.view.showPanel(this.section);
      const controller = this.controllers[this.section];
      if (controller) {
        if (['groups', 'configurator', 'content', 'gallery'].includes(this.section)) {
          const choices = [...controller.view.root.querySelector('[data-config-section]').options].map(option => option.value);
          const type = choices.includes(route.type) ? route.type : choices[0];
          if (!controller.ready || controller.section !== type) await controller.load(type);
        } else if (!controller.ready) await controller.load();
        if (controller.ready) {
          const current = this.routeFor().record;
          if (current !== idValue(route.record)) await controller.select(idValue(route.record));
          const select = controller.view.root.querySelector('[data-product-select], [data-color-select], [data-config-record]');
          if (controller.view.recordList) controller.view.recordList.select(this.routeFor().record);
          else if (select) select.value = this.routeFor().record;
        }
      } else {
        await this.admin.loadRequests();
        if (route.record && this.admin.view.openRequest) await this.admin.view.openRequest(route.record);
      }
      const actual = this.routeFor();
      const url = adminRouteUrl(actual, location.href);
      if (url !== location.pathname + location.search + location.hash) history[mode === 'push' ? 'pushState' : 'replaceState']({}, '', url);
      this.currentKey = this.key(actual);
      this.applyDefaultDisclosures();
      await this.restore({ editor: this.mobileLayout() && Boolean(actual.record) });
    } finally {
      this.restoring = false;
      this.refreshSavebar();
      if (this.pending) { const next = this.pending; this.pending = null; this.go(next.route, next.mode); }
    }
  }
  destroy() { this.capture(); clearTimeout(this.timer); clearInterval(this.editorScrollTimer); this.events.abort(); history.scrollRestoration = 'auto'; }
}
