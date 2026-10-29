const sections = ['catalog', 'groups', 'colors', 'configurator', 'requests', 'content', 'gallery', 'reviews', 'contacts', 'settings'];
const idValue = value => /^\d+$/.test(String(value || '')) && Number(value) > 0 ? String(value) : '';

export function readAdminRoute(url) {
  const params = new URL(url).searchParams;
  const section = sections.includes(params.get('section')) ? params.get('section') : 'catalog';
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
              this.restoring = true;
              try { await this.restore(); }
              finally {
                this.restoring = false;
                if (this.pending) { const next = this.pending; this.pending = null; this.go(next.route, next.mode); }
              }
            }
          }
        };
      }
    }
  }
  routeFor(section = this.section) {
    const controller = this.controllers[section];
    if(!controller&&section!=='requests')return this.routeFor('catalog');
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
  async restore() {
    const state = this.states[this.currentKey];
    if (state?.blocks) for (const {block, key} of this.details()) {
      if (typeof state.blocks[key] === 'boolean') block.open = state.blocks[key];
    }
    // Background tabs can suspend animation frames; navigation must still finish.
    await new Promise(resolve => {
      const timer = setTimeout(resolve, 150);
      requestAnimationFrame(() => requestAnimationFrame(() => { clearTimeout(timer); resolve(); }));
    });
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
      }
    }, options);
    this.root.addEventListener('admin:request-open', () => this.sync('push'), options);
    this.root.addEventListener('admin:product-new', () => this.sync('push'), options);
    window.addEventListener('popstate', () => this.go(readAdminRoute(location.href), 'pop'), options);
    this.go(readAdminRoute(location.href), 'replace');
  }
  async go(route, mode = 'push') {
    if (this.restoring) { this.pending = { route, mode }; return; }
    if (Object.values(this.controllers).some(controller => controller.busy) || this.admin.view.requestBusy) {
      this.sync(); return;
    }
    this.capture();
    this.restoring = true;
    try {
      this.section = sections.includes(route.section) && (route.section==='requests'||this.controllers[route.section]) ? route.section : 'catalog';
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
      await this.restore();
    } finally {
      this.restoring = false;
      if (this.pending) { const next = this.pending; this.pending = null; this.go(next.route, next.mode); }
    }
  }
  destroy() { this.capture(); clearTimeout(this.timer); this.events.abort(); history.scrollRestoration = 'auto'; }
}
