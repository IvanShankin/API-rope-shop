/* SPLICE — макет, БЭМ */
(function () {
  'use strict';

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function debounce(fn, ms) {
    let id = 0;
    return function () {
      clearTimeout(id);
      id = setTimeout(fn, ms);
    };
  }

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

  /* карточка товара: миниатюра меняет большое фото */
  function initProduct(root) {
    const image = root.querySelector('.product__image');
    const thumbs = root.querySelectorAll('.product__thumb');

    thumbs.forEach((thumb) => {
      thumb.addEventListener('click', () => {
        const source = thumb.querySelector('.product__thumb-image');
        if (image.getAttribute('src') === source.getAttribute('src')) return;
        image.src = source.src;
        image.alt = source.alt;
        image.setAttribute('width', source.getAttribute('width'));
        image.setAttribute('height', source.getAttribute('height'));
        // перезапуск плавного появления
        image.style.animation = 'none';
        void image.offsetWidth;
        image.style.animation = '';
        thumbs.forEach((t) => {
          const active = t === thumb;
          t.classList.toggle('product__thumb--active', active);
          t.setAttribute('aria-pressed', String(active));
        });
      });
    });
  }

  /* конфигуратор: данные (цены и нагрузки — заглушки, уточнить у мастера) */
  const ROPE = {
    currency: '€',
    materials: {
      sk78: {
        name: 'Dyneema SK78',
        // конструкция понадобится для будущей проверки совместимости видов сращивания
        // hollow — полое плетение Dyneema / Vectran / Zylon (Hohlgeflecht)
        // hm — сердечник Dyneema / Vectran / Zylon в оплётке (Kern-Mantel)
        // core — сердечник и оплётка из полиэстера (Kern-Mantel)
        construction: 'hollow',
        splice: 0.9, // доля прочности, которая остаётся после сплайса
        soft: true, // можно ли сделать мягкую скобу
        weave: 1, // крупность плетения на схеме
        // диаметр, мм: [разрывная нагрузка, кг; цена за метр, €]
        sizes: {
          3: [950, 1.1], 4: [1600, 1.5], 5: [2500, 2.1], 6: [3500, 2.8], 8: [6000, 4.4],
          10: [9000, 6.9], 12: [12800, 9.8], 14: [16000, 13.5], 16: [19200, 17.9]
        }
      },
      covered: {
        name: 'Dyneema в оплётке',
        construction: 'hm',
        splice: 0.85,
        soft: true,
        weave: 0.7,
        sizes: {
          5: [1800, 2.6], 6: [2600, 3.4], 8: [4500, 5.2], 10: [7000, 7.9], 12: [9500, 11.2], 14: [12500, 15]
        }
      },
      polyester: {
        name: 'Полиэстер двойного плетения',
        construction: 'core',
        splice: 0.85,
        soft: false,
        weave: 0.7,
        sizes: {
          6: [800, 0.9], 8: [1450, 1.3], 10: [2250, 1.9], 12: [3200, 2.6], 14: [4300, 3.4], 16: [5500, 4.3]
        }
      }
    },
    ends: {
      cut: { label: 'оплавленный торец' },
      whip: { label: 'такелажная обмотка' },
      eye: { label: 'огон', loop: true },
      thimble: { label: 'огон с коушем', loop: true },
      shackle: { label: 'огон с коушем и скобой', loop: true },
      soft: { label: 'огон с мягкой скобой', loop: true }
    },
    // Услуги и цены за одну работу. null означает, что для этого диаметра
    // цена не была предоставлена и должна быть согласована отдельно.
    splices: {
      'locking-eye': { label: 'Augspleiß Kern-Mantel', prices: [{ upTo: 14, price: 15 }, { upTo: 22, price: 20 }, { upTo: null, price: 35 }] },
      'dyneema-double': { label: 'Augspleiß Kern-Mantel Dyneema/Vectran/Zylon', prices: [{ upTo: 14, price: 30 }, { upTo: null, price: 40 }] },
      'hollow-eye': { label: 'Augspleiß Kern-Mantel Dyneema/Vectran/Zylon-Hohlgeflecht', prices: [{ upTo: null, price: 12 }] },
      endless: { label: 'Endlosspleiß Kern-Mantel', prices: [{ upTo: null, price: 33 }] },
      'double-braid-eye': { label: 'Takling', prices: [{ upTo: 12, price: 1.5 }, { upTo: 14, price: null }, { upTo: null, price: 2.5 }] },
      'single-braid-cover': { label: 'Pilotauge', prices: [{ upTo: null, price: 4 }] }
    },
    // Работа без сращивания, € за один конец. Ступени и цены позже заменит заказчик.
    work: {
      cut: 0,
      whip: [{ upTo: 12, price: 1.5 }, { upTo: 14, price: null }, { upTo: null, price: 2.5 }]
    },
    // фурнитура по диаметру, €; нет цифры — для этого диаметра вариант недоступен
    hardware: {
      thimble: { 3: 7, 4: 8, 5: 9, 6: 9, 8: 11, 10: 13, 12: 15, 14: 17, 16: 18 },
      shackle: { 3: 15, 4: 17, 5: 19, 6: 21, 8: 26, 10: 30, 12: 34, 14: 39, 16: 43 },
      soft: { 3: 33, 4: 34, 5: 36, 6: 37, 8: 40, 10: 43 }
    },
    sleeve: 9, // за каждый огон
    tag: 5,
    rush: 10, // за каждое сращивание, не более 10 сращиваний в заказе
    safety: 5,
    length: { min: 1, max: 200 }
  };

  const SPLICE_GROUPS = {
    core: { name: 'Полиэстер · сердечник + оплётка', service: 'locking-eye', soft: false },
    hm: { name: 'Dyneema / Vectran / Zylon · в оплётке', service: 'dyneema-double', soft: true },
    hollow: { name: 'Dyneema / Vectran / Zylon · полое плетение', service: 'hollow-eye', soft: true }
  };

  const fmtNum = (n, digits = 0) => n.toLocaleString('ru-RU', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  });
  // центы показываем, только если они есть: 15 €, 1,50 €
  const cents = (n) => Math.round(n * 100) / 100;
  const fmtMoney = (n) => `${fmtNum(cents(n), cents(n) % 1 ? 2 : 0)} ${ROPE.currency}`;
  const fmtLength = (m) => `${fmtNum(m, m % 1 ? 1 : 0)} м`;
  const fmtKg = (kg) => `${fmtNum(kg)} кг`;
  const capitalize = (s) => s.charAt(0).toUpperCase() + s.slice(1);

  function endLabel(end) {
    return ROPE.ends[end.type].label + (ROPE.ends[end.type].loop ? (end.eye > 0 ? `, петля ${end.eye} см` : ', укажите размер петли') : '');
  }

  // цена по ступеням диаметра: первая ступень, в которую попадает диаметр
  function tierPrice(tiers, d) {
    return tiers.find((t) => t.upTo === null || d <= t.upTo).price;
  }

  function endExtraPrice(end, d) {
    const { work, hardware } = ROPE;
    switch (end.type) {
      case 'whip': return tierPrice(work.whip, d);
      case 'thimble': return hardware.thimble[d];
      case 'shackle': return hardware.thimble[d] + hardware.shackle[d];
      case 'soft': return hardware.soft[d];
      default: return work.cut;
    }
  }

  function endPrice(end, d, splicePrice) {
    const extra = endExtraPrice(end, d);
    if (!Number.isFinite(extra) || (ROPE.ends[end.type].loop && !Number.isFinite(splicePrice))) return null;
    return cents(extra + (ROPE.ends[end.type].loop ? splicePrice : 0));
  }

  function loopPrice(construction, d) {
    return tierPrice(ROPE.splices[SPLICE_GROUPS[construction].service].prices, d);
  }

  // почему конец недоступен; пустая строка — доступен
  function endReason(type, d, mat) {
    const { hardware } = ROPE;
    if (type === 'soft' && !mat.soft) return 'Не делаем из этого троса';
    if ((type === 'thimble' || type === 'shackle') && hardware.thimble[d] == null) return `Нет коуша на ${d} мм`;
    if (type === 'shackle' && hardware.shackle[d] == null) return `Нет скобы на ${d} мм`;
    if (type === 'soft' && hardware.soft[d] == null) {
      const max = Math.max(...Object.keys(hardware.soft).map(Number));
      return d > max ? `Только до ${max} мм` : `Нет на ${d} мм`;
    }
    return '';
  }

  // Подтверждённый технологический запас на одно сращивание:
  // до 12 мм включительно — 0,6 м, свыше 12 мм — 1 м.
  function endAllowance(end, d) {
    return ROPE.ends[end.type].loop ? (d <= 12 ? 0.6 : 1) : 0;
  }

  /* схема троса: концы рисуются в общей системе координат, чтобы плетение не разрывалось на стыках */
  const eyePixels = (cm) => Math.min(146, Math.max(60, 46 + Number(cm || 1) * 2));

  function endShape(end, w) {
    const half = w / 2;
    const bury = 34 + w * 1.4;
    switch (end.type) {
      case 'cut': return { width: 18 + half };
      case 'whip': return { width: 48 };
      case 'eye': {
        const L = eyePixels(end.eye);
        return { width: bury + L + half, bury, L, h: 14 + L * 0.2 + half };
      }
      case 'thimble': {
        const L = 46 + w * 1.4;
        return { width: bury + L + half, bury, L, h: 12 + w * 0.9 };
      }
      case 'shackle': {
        const L = 46 + w * 1.4;
        const r = 10 + half;
        const pin = bury + L + half + 12 + w * 0.4;
        return { width: pin + 7, bury, L, h: 12 + w * 0.9, r, pin };
      }
      case 'soft': {
        const L = 54;
        const rx = 24 + w * 0.8;
        const ry = 12 + w * 0.6;
        const cx = bury + L + rx * 0.5;
        const knob = 3 + w * 0.62;
        return { width: cx + rx + knob, bury, L, h: 14 + L * 0.2 + half, rx, ry, cx, knob };
      }
      default: return { width: 0 };
    }
  }

  // dir: 1 — конец справа, -1 — слева (зеркально)
  function drawEnd(end, geo, w, x0, cy, dir, sleeve) {
    const half = w / 2;
    const r1 = (v) => Math.round(v * 10) / 10;
    const X = (x) => r1(x0 + dir * x);
    const Y = (y) => r1(cy + y);
    const P = (x, y) => `${X(x)} ${Y(y)}`;
    const sweep = (flag) => (dir === 1 ? flag : 1 - flag);
    const minX = (a, b) => Math.min(X(a), X(b));

    const strand = (d, width = w, cap = 'butt') => (
      `<path class="rope-preview__edge" d="${d}" stroke-width="${r1(width + 2.5)}" stroke-linecap="${cap}"/>` +
      `<path class="rope-preview__strand" d="${d}" stroke-width="${r1(width)}" stroke-linecap="${cap}"/>`
    );
    const shade = (a, b) => `<rect class="rope-preview__shade" x="${minX(a, b)}" y="${Y(-half)}" width="${r1(Math.abs(b - a))}" height="${r1(w)}"/>`;
    const loop = (b, L, h) => {
      const q = half * 0.5;
      return `M${P(b - 6, -q)} C${P(b + L * 0.3, -h)} ${P(b + L, -h * 0.95)} ${P(b + L, 0)} ` +
        `C${P(b + L, h * 0.95)} ${P(b + L * 0.3, h)} ${P(b - 6, q)}`;
    };
    // зона сплайса: хвост спрятан внутри троса, поэтому здесь он толще
    const taper = (b) => {
      const t = half * 1.45;
      const top = `M${P(-1, -half)} C${P(b * 0.5, -half)} ${P(b * 0.6, -t)} ${P(b, -t)}`;
      const bottom = `M${P(-1, half)} C${P(b * 0.5, half)} ${P(b * 0.6, t)} ${P(b, t)}`;
      const body = `${top} L${P(b + 2, 0)} L${P(b, t)} C${P(b * 0.6, t)} ${P(b * 0.5, half)} ${P(-1, half)} Z`;
      // контур только сверху и снизу: справа зона сплайса перетекает в огон без шва
      return `<path class="rope-preview__fill" d="${body}"/><path class="rope-preview__shade" d="${body}"/>` +
        `<path class="rope-preview__outline" d="${top} ${bottom}"/>`;
    };
    const thimble = (b, L, h) => {
      const hi = h - half;
      const tip = b + L - half;
      const d = `M${P(b + 8, 0)} C${P(b + L * 0.35, -hi)} ${P(tip, -hi * 0.95)} ${P(tip, 0)} ` +
        `C${P(tip, hi * 0.95)} ${P(b + L * 0.35, hi)} ${P(b + 8, 0)}`;
      return `<path class="rope-preview__metal-edge" d="${d}" stroke-width="5.5"/>` +
        `<path class="rope-preview__metal" d="${d}" stroke-width="3.2"/>`;
    };
    const sleeveOn = (d) => (sleeve
      ? `<path class="rope-preview__sleeve-edge" d="${d}" pathLength="100" stroke-width="${r1(w * 1.3 + 2.5)}"/>` +
        `<path class="rope-preview__sleeve" d="${d}" pathLength="100" stroke-width="${r1(w * 1.3)}"/>`
      : '');

    switch (end.type) {
      case 'cut': {
        const len = 18;
        return strand(`M${P(-2, 0)} L${P(len, 0)}`, w, 'round') + shade(-2, len - half * 0.2) +
          `<ellipse class="rope-preview__melt" cx="${X(len + half * 0.35)}" cy="${Y(0)}" rx="${r1(half * 0.55)}" ry="${r1(half * 0.9)}"/>`;
      }
      case 'whip': {
        const len = 48 - half;
        return strand(`M${P(-2, 0)} L${P(len, 0)}`, w, 'round') + shade(-2, len) +
          `<rect class="rope-preview__whip" x="${minX(14, 36)}" y="${Y(-half - 1.5)}" width="22" height="${r1(w + 3)}" rx="2"/>`;
      }
      case 'eye': {
        const d = loop(geo.bury, geo.L, geo.h);
        return strand(d) + sleeveOn(d) + taper(geo.bury);
      }
      case 'thimble': {
        const d = loop(geo.bury, geo.L, geo.h);
        return strand(d) + thimble(geo.bury, geo.L, geo.h) + taper(geo.bury);
      }
      case 'shackle': {
        const { bury: b, L, h, r, pin } = geo;
        const e = b + L;
        const bow = `M${P(pin, -r)} L${P(e - r * 0.35, -r)} A${r1(r)} ${r1(r)} 0 0 ${sweep(0)} ${P(e - r * 0.35, r)} L${P(pin, r)}`;
        return `<path class="rope-preview__metal-edge" d="${bow}" stroke-width="8"/>` +
          `<path class="rope-preview__metal" d="${bow}" stroke-width="5.4"/>` +
          strand(loop(b, L, h)) + thimble(b, L, h) + taper(b) +
          `<rect class="rope-preview__metal-part" x="${r1(X(pin) - 3.5)}" y="${Y(-r - 7)}" width="7" height="${r1(2 * r + 14)}" rx="3.5"/>` +
          `<circle class="rope-preview__metal-part" cx="${X(pin)}" cy="${Y(-r - 7)}" r="5.5"/>` +
          `<rect class="rope-preview__metal-part" x="${r1(X(pin) - 5)}" y="${Y(r + 4)}" width="10" height="7" rx="1.5"/>`;
      }
      case 'soft': {
        const { bury: b, L, h, rx, ry, cx, knob } = geo;
        const rw = w * 0.8;
        const ring = `M${P(cx - rx, 0)} A${r1(rx)} ${r1(ry)} 0 1 ${sweep(1)} ${P(cx + rx, 0)} ` +
          `A${r1(rx)} ${r1(ry)} 0 1 ${sweep(1)} ${P(cx - rx, 0)}`;
        const top = `M${P(cx - rx, 0)} A${r1(rx)} ${r1(ry)} 0 0 ${sweep(1)} ${P(cx + rx, 0)}`;
        const d = loop(b, L, h);
        const kx = cx + rx;
        // верхняя половина кольца поверх огона — скоба продета в петлю
        return strand(ring, rw) + strand(d) + sleeveOn(d) + taper(b) + strand(top, rw) +
          `<circle class="rope-preview__body" cx="${X(kx)}" cy="${Y(0)}" r="${r1(knob)}"/>` +
          `<path class="rope-preview__knot" d="M${P(kx - knob * 0.5, -knob * 0.8)} Q${P(kx + knob * 0.3, 0)} ${P(kx - knob * 0.5, knob * 0.8)} ` +
          `M${P(kx + knob * 0.2, -knob * 0.9)} Q${P(kx + knob, 0)} ${P(kx + knob * 0.2, knob * 0.9)}"/>`;
      }
      default: return '';
    }
  }

  function initConfigurator(root) {
    const form = root.querySelector('.configurator__layout');
    const preview = root.querySelector('.rope-preview');
    const svg = preview.querySelector('.rope-preview__canvas');
    const drawing = svg.querySelector('[data-cfg-drawing]');
    const lengthInput = form.elements['cfg-length'];
    const range = form.querySelector('[data-cfg-range]');
    const qtyInput = form.elements['cfg-qty'];
    const lines = root.querySelector('[data-cfg-lines]');
    const notices = {};
    root.querySelectorAll('[data-cfg-notice]').forEach((el) => { notices[el.dataset.cfgNotice] = el; });

    const radios = (name) => Array.from(form.querySelectorAll(`input[name="${name}"]`));
    const value = (name) => {
      const field = form.elements[name];
      return field ? field.value : null;
    };
    const pick = (name, val) => {
      const el = form.querySelector(`input[name="${name}"][value="${val}"]`);
      if (el) el.checked = true;
    };
    const out = (key, text) => root.querySelectorAll(`[data-cfg-out="${key}"]`).forEach((el) => { el.textContent = text; });

    // ползунок нелинейный: короткие длины выбирать точнее
    const { min: LEN_MIN, max: LEN_MAX } = ROPE.length;
    const toRange = (m) => Math.round(Math.sqrt((m - LEN_MIN) / (LEN_MAX - LEN_MIN)) * 1000);
    const fromRange = (v) => Math.round((LEN_MIN + (LEN_MAX - LEN_MIN) * (v / 1000) ** 2) * 2) / 2;

    let last = null;
    let prevEnds = [];

    function update(opts = {}) {
      const msgs = {};
      const mat = ROPE.materials[value('cfg-material')];

      // цены «от» у тросов
      root.querySelectorAll('[data-cfg-from]').forEach((el) => {
        const sizes = Object.values(ROPE.materials[el.dataset.cfgFrom].sizes);
        el.textContent = `от ${fmtNum(sizes[0][1], 1)} ${ROPE.currency}/м`;
      });

      // диаметр: недоступные гасим, выбранный при необходимости меняем на ближайший
      radios('cfg-diameter').forEach((input) => {
        const size = mat.sizes[input.value];
        const option = input.closest('.option');
        input.disabled = !size;
        option.title = size ? '' : `У троса «${mat.name}» нет такого диаметра`;
        option.querySelector('.option__meta').textContent = size ? `${fmtNum(size[0] / 1000, 1)} т` : '—';
      });
      let d = Number(value('cfg-diameter'));
      if (!mat.sizes[d]) {
        const nearest = Object.keys(mat.sizes).map(Number)
          .reduce((a, b) => (Math.abs(b - d) < Math.abs(a - d) ? b : a));
        msgs.diameter = `У троса «${mat.name}» нет ${d} мм — поставили ближайший: ${nearest} мм.`;
        d = nearest;
        pick('cfg-diameter', d);
      }

      const splicePrice = loopPrice(mat.construction, d);
      const ends = ['a', 'b'].map((side) => {
        const name = `cfg-end-${side}`;
        radios(name).forEach((input) => {
          const reason = endReason(input.value, d, mat);
          input.disabled = Boolean(reason);
          const option = input.closest('.option');
          const price = endPrice({ type: input.value }, d, splicePrice);
          option.querySelector('.option__price').textContent = reason || (price === null ? 'По запросу' : fmtMoney(price));
        });
        let type = value(name);
        if (endReason(type, d, mat)) {
          pick(name, 'eye');
          type = 'eye';
          msgs[`end-${side}`] = 'Выбранное оснащение недоступно для этого каната — установлена обычная петля.';
        }
        const eyeInput = form.elements[`cfg-eye-${side}`];
        const hasLoop = Boolean(ROPE.ends[type].loop);
        eyeInput.disabled = !hasLoop;
        eyeInput.closest('.configurator__eye').hidden = !hasLoop;
        const eye = Number(eyeInput.value);
        return { type, eye: hasLoop && Number.isFinite(eye) && eye > 0 ? eye : null };
      });

      // Размер петли сохраняется для согласования; пока используем подтверждённый запас по диаметру.
      let length = parseFloat(String(lengthInput.value).replace(',', '.'));
      if (opts.source === range) length = fromRange(Number(range.value));
      if (!Number.isFinite(length)) length = last ? last.length : 10;
      length = Math.min(LEN_MAX, Math.max(LEN_MIN, Math.round(length * 2) / 2));
      if (!opts.typing) lengthInput.value = length;
      if (opts.source !== range) range.value = toRange(length);
      range.style.setProperty('--fill', `${range.value / 10}%`);

      let qty = parseInt(qtyInput.value, 10);
      qty = Number.isFinite(qty) ? Math.min(999, Math.max(1, qty)) : 1;
      if (!opts.typing) qtyInput.value = qty;

      // цена
      const [mbl, perMetre] = mat.sizes[d];
      const allowance = cents(ends.reduce((sum, end) => sum + endAllowance(end, d), 0));
      const chargedLength = cents(length + allowance);
      const ropeCost = cents(chargedLength * perMetre);
      const endPrices = ends.map((end) => endPrice(end, d, splicePrice));
      const hasPrice = endPrices.every(Number.isFinite);
      const each = hasPrice ? cents(ropeCost + endPrices[0] + endPrices[1]) : null;
      const total = hasPrice ? cents(each * qty) : null;

      // нагрузки
      const wll = Math.round(mbl / ROPE.safety / 10) * 10;

      // вывод
      const colorInput = form.querySelector('input[name="cfg-color"]:checked');
      const colorName = colorInput.closest('.option').querySelector('.option__title').textContent;
      preview.className = preview.className.replace(/\brope-color--\S+/g, '').trim();
      preview.classList.add(`rope-color--${colorInput.value}`);

      out('caption', `${mat.name} · ${d} мм · ${colorName.toLowerCase()}`);
      out('mbl', fmtKg(mbl));
      out('wll', fmtKg(wll));
      out('total', hasPrice ? fmtMoney(total) : 'По запросу');
      out('material', mat.name);
      out('size', `${d} мм, ${colorName.toLowerCase()}`);
      out('length', fmtLength(length));
      out('charged-length', fmtLength(chargedLength));
      out('allowance', fmtLength(allowance));
      ends.forEach((end, i) => out(`end-${i ? 'b' : 'a'}`, capitalize(endLabel(end))));
      out('qty', `${qty} шт.`);
      out('each', qty > 1 && hasPrice ? `${fmtMoney(each)} за штуку` : '');
      out('time', qty > 10 || length * qty > 200 ? '7–10 рабочих дней' : '3–5 рабочих дней');

      const rows = [
        [`Канат: ${fmtLength(chargedLength)} × ${fmtMoney(perMetre)}/м`, ropeCost],
        ['Конец A', endPrices[0]],
        ['Конец B', endPrices[1]]
      ];
      rows.push(['За 1 шт.', each, true]);
      if (qty > 1) rows.push([`× ${qty} шт.`, total, true]);
      lines.innerHTML = rows.map(([label, sum, strong]) => (
        `<li class="summary__line${strong ? ' summary__line--strong' : ''}"><span>${label}</span><span class="summary__line-sum">${sum === null ? 'По запросу' : fmtMoney(sum)}</span></li>`
      )).join('');

      Object.keys(notices).forEach((key) => {
        if (opts.keepNotices && !msgs[key]) return;
        notices[key].textContent = msgs[key] || '';
        notices[key].hidden = !msgs[key];
      });

      form.dataset.configuration = JSON.stringify({ type: 'ROPE_WITH_SPLICE', material: value('cfg-material'), diameter: d,
        color: colorInput.value, length, allowance, chargedLength, ends, qty, ropeCost, endPrices, each, total });
      last = { mat, d, ends, length, sleeve: false };
      drawRope();
    }

    function drawRope() {
      if (!last) return;
      const { mat, d, ends, length, sleeve } = last;
      const box = svg.getBoundingClientRect().width || 800;
      const vbW = Math.round(Math.min(1000, Math.max(620, box)));
      const vbH = 250;
      const cy = 112;
      const pad = 30;
      const k = vbW / box; // во сколько раз схема ужата — чтобы подписи не мельчали
      const w = 5 + d * 1.15;
      const half = w / 2;
      const geo = ends.map((e) => endShape(e, w));
      const xA = pad + geo[0].width;
      const xB = vbW - pad - geo[1].width;
      const xm = (xA + xB) / 2;
      const r1 = (v) => Math.round(v * 10) / 10;

      svg.setAttribute('viewBox', `0 0 ${vbW} ${vbH}`);
      const changed = ends.map((e, i) => !prevEnds[i] || prevEnds[i].type !== e.type || prevEnds[i].eye !== e.eye);
      prevEnds = ends;
      const endGroup = (i, markup) => `<g class="rope-preview__end${changed[i] ? ' rope-preview__end--enter' : ''}">${markup}</g>`;

      let s = `<path class="rope-preview__edge" d="M${r1(xA)} ${cy}H${r1(xB)}" stroke-width="${r1(w + 2.5)}"/>`;
      s += endGroup(0, drawEnd(ends[0], geo[0], w, xA, cy, -1, sleeve));
      s += endGroup(1, drawEnd(ends[1], geo[1], w, xB, cy, 1, sleeve));
      s += `<rect class="rope-preview__fill" x="${r1(xA)}" y="${r1(cy - half)}" width="${r1(xB - xA)}" height="${r1(w)}"/>`;
      s += `<rect class="rope-preview__shade" x="${r1(xA)}" y="${r1(cy - half)}" width="${r1(xB - xA)}" height="${r1(w)}"/>`;

      // разрыв посередине: длина условная
      if (xB - xA > 120) {
        const t = cy - half - 7;
        const b = cy + half + 7;
        s += `<path class="rope-preview__gap" d="M${r1(xm - 3)} ${r1(t)}H${r1(xm + 7)}L${r1(xm + 3)} ${r1(b)}H${r1(xm - 7)}Z"/>`;
        s += `<path class="rope-preview__gap-line" d="M${r1(xm - 3)} ${r1(t)}L${r1(xm - 7)} ${r1(b)}M${r1(xm + 7)} ${r1(t)}L${r1(xm + 3)} ${r1(b)}"/>`;
      }

      // метки концов
      const markR = r1(12 * Math.min(k, 1.6));
      [[pad + geo[0].width / 2, 'A'], [vbW - pad - geo[1].width / 2, 'B']].forEach(([x, letter]) => {
        s += `<circle class="rope-preview__mark" cx="${r1(x)}" cy="${markR + 2}" r="${markR}"/>`;
        s += `<text class="rope-preview__mark-text" x="${r1(x)}" y="${r1(markR + 2 + markR * 0.36)}" font-size="${r1(markR)}">${letter}</text>`;
      });

      // размерная линия: рабочая длина от края до края
      const dy = vbH - 24;
      const fs = r1(15 * Math.min(k, 1.7));
      const gap = fs * 3.6;
      const x1 = pad;
      const x2 = vbW - pad;
      s += `<path class="rope-preview__dim-guide" d="M${x1} ${r1(cy + half + 8)}V${dy - 8}M${x2} ${r1(cy + half + 8)}V${dy - 8}"/>`;
      s += `<path class="rope-preview__dim" d="M${x1} ${dy}H${r1(xm - gap)}M${r1(xm + gap)} ${dy}H${x2}` +
        `M${x1 - 4} ${dy + 4}L${x1 + 4} ${dy - 4}M${x2 - 4} ${dy + 4}L${x2 + 4} ${dy - 4}"/>`;
      s += `<text class="rope-preview__dim-text" x="${r1(xm)}" y="${r1(dy + fs * 0.36)}" font-size="${fs}">${fmtLength(length)}</text>`;

      drawing.innerHTML = s;
      svg.setAttribute('aria-label', `Схема троса: ${endLabel(ends[0])}, ${fmtLength(length)}, ${endLabel(ends[1])}`);
    }

    form.addEventListener('change', (e) => {
      // контакты клиента на цену не влияют
      if (e.target === range || e.target.closest('.summary__contacts')) return;
      update({ source: e.target });
    });
    lengthInput.addEventListener('input', () => update({ typing: true, keepNotices: true }));
    qtyInput.addEventListener('input', () => update({ typing: true, keepNotices: true }));
    ['a', 'b'].forEach((side) => form.elements[`cfg-eye-${side}`].addEventListener('input', () => update({ typing: true })));
    range.addEventListener('input', () => update({ source: range }));

    root.querySelectorAll('.stepper__button').forEach((button) => {
      button.addEventListener('click', () => {
        qtyInput.value = Math.max(1, (parseInt(qtyInput.value, 10) || 1) + Number(button.dataset.step));
        update();
      });
    });

    // макет: заявка пока никуда не отправляется
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (!form.reportValidity()) return;
      update();
      root.querySelector('[data-cfg-submit-status]').textContent = 'Конфигурация рассчитана. Это макет: заявка не отправлена.';
    });

    window.addEventListener('resize', debounce(drawRope, 120));
    update();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(drawRope);
  }

  /* отдельный расчёт услуг: для клиента со своей верёвкой */
  function initServiceConfigurator(root) {
    const form = root.querySelector('.service-configurator__layout');
    const isLoop = root.dataset.serviceMode === 'loops';
    const qtyInput = form.elements['svc-qty'];
    const lines = root.querySelector('[data-service-lines]');
    const value = (name) => form.elements[name].value;
    const out = (key, text) => root.querySelectorAll(`[data-service-out="${key}"]`).forEach((el) => {
      el.textContent = text;
    });

    function update(opts = {}) {
      const diameter = Number(value('svc-diameter'));
      const construction = value('svc-material');
      const group = SPLICE_GROUPS[construction];
      let each, label, eye = null, notice = '';
      if (isLoop) {
        const splicePrice = loopPrice(construction, diameter);
        form.querySelectorAll('[name="svc-type"]').forEach((input) => {
          const reason = endReason(input.value, diameter, group);
          input.disabled = Boolean(reason);
          const price = endPrice({ type: input.value }, diameter, splicePrice);
          input.closest('.option').querySelector('.option__price').textContent = reason || (price === null ? 'По запросу' : fmtMoney(price));
        });
        if (endReason(value('svc-type'), diameter, group)) {
          form.querySelector('[name="svc-type"][value="eye"]').checked = true;
          notice = 'Для этого каната выбрана обычная петля: прежнее оснащение недоступно.';
        }
        eye = Number(form.elements['svc-eye'].value);
        const end = { type: value('svc-type'), eye: eye > 0 ? eye : null };
        each = endPrice(end, diameter, splicePrice);
        label = capitalize(ROPE.ends[end.type].label);
        out('eye', eye > 0 ? `${fmtNum(eye, 1)} см` : 'Укажите размер');
      } else {
        const service = ROPE.splices[value('svc-type')];
        label = service.label;
        each = tierPrice(service.prices, diameter);
        if (value('svc-type') === 'endless' && construction === 'hollow') {
          each = null;
          notice = 'Для замкнутого сращивания полого плетения стоимость и совместимость согласуем отдельно.';
        } else if (each === null) {
          notice = 'Для этого диаметра в прайсе нет цены. Уточним стоимость перед выполнением.';
        }
      }
      const diameterLabel = form.querySelector('input[name="svc-diameter"]:checked')
        .closest('.option').querySelector('.option__title').textContent;
      const hasPrice = Number.isFinite(each);
      let qty = parseInt(qtyInput.value, 10);

      qty = Number.isFinite(qty) ? Math.min(999, Math.max(1, qty)) : 1;
      if (!opts.typing) qtyInput.value = qty;

      const total = hasPrice ? cents(each * qty) : null;
      out('type', label);
      out('material', group.name);
      out('diameter', diameterLabel);
      out('qty', `${qty} шт.`);
      out('each', hasPrice ? fmtMoney(each) : 'По запросу');
      out('total', hasPrice ? fmtMoney(total) : 'По запросу');
      lines.innerHTML = hasPrice
        ? [
          `<li><span>${isLoop ? 'Одна петля с выбранным оснащением' : label}</span><strong>${fmtMoney(each)}</strong></li>`,
          ...(qty > 1 ? [`<li><span>Количество</span><strong>× ${qty}</strong></li>`] : [])
        ].join('')
        : '<li><span>Стоимость выбранного исполнения уточним.</span><strong>По запросу</strong></li>';
      const noticeElement = root.querySelector('[data-service-notice]');
      noticeElement.textContent = notice;
      noticeElement.hidden = !notice;
      form.dataset.configuration = JSON.stringify({ type: isLoop ? 'LOOP_ONLY' : 'SPLICE_ONLY',
        material: construction, diameter, service: value('svc-type'), eye, qty, ropeCost: 0, each, total });
    }

    form.addEventListener('change', (e) => {
      if (e.target.matches('[name="svc-comment"]')) return;
      update({ source: e.target });
    });
    qtyInput.addEventListener('input', () => update({ typing: true }));
    if (isLoop) form.elements['svc-eye'].addEventListener('input', () => update({ typing: true }));
    root.querySelectorAll('[data-service-step]').forEach((button) => {
      button.addEventListener('click', () => {
        qtyInput.value = Math.max(1, (parseInt(qtyInput.value, 10) || 1) + Number(button.dataset.serviceStep));
        update();
      });
    });
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (!form.reportValidity()) return;
      update();
      root.querySelector('[data-service-submit-status]').textContent = 'Параметры рассчитаны. Это макет: заявка не отправлена.';
    });
    update();
  }

  function initWorkGallery(root) {
    const photos = Array.from(root.querySelectorAll('.work-gallery__photo'));
    const dialog = root.querySelector('dialog');
    const image = dialog.querySelector('.work-gallery__full-image');
    const caption = dialog.querySelector('.work-gallery__current');
    const more = root.querySelector('[data-gallery-more]');
    const pageSize = Number(root.dataset.galleryPageSize) || 10;
    let visible = pageSize;
    let current = 0;

    function updateVisible() {
      photos.forEach((photo, index) => { photo.hidden = index >= visible; });
      more.hidden = visible >= photos.length;
    }
    more.addEventListener('click', () => {
      const firstNew = photos[visible];
      visible += pageSize;
      updateVisible();
      if (firstNew) firstNew.focus({ preventScroll: true });
    });
    updateVisible();

    function show(index) {
      current = (index + photos.length) % photos.length;
      const source = photos[current].querySelector('img');
      image.src = source.src;
      image.alt = source.alt;
      caption.textContent = `${current + 1} / ${photos.length}`;
    }

    photos.forEach((photo, index) => photo.addEventListener('click', () => {
      show(index);
      dialog.showModal();
    }));
    dialog.querySelector('.work-gallery__close').addEventListener('click', () => dialog.close());
    dialog.querySelector('[data-photo-prev]').addEventListener('click', () => show(current - 1));
    dialog.querySelector('[data-photo-next]').addEventListener('click', () => show(current + 1));
    dialog.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        show(current + (event.key === 'ArrowLeft' ? -1 : 1));
      }
    });
    dialog.addEventListener('click', (event) => {
      if (event.target !== dialog) return;
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    });
  }

  /* старт */
  document.addEventListener('DOMContentLoaded', async () => {
    initHeader();
    const hero = document.querySelector('.hero');
    if (hero) initHero(hero);
    document.querySelectorAll('.configurator').forEach(initConfigurator);
    document.querySelectorAll('.service-configurator').forEach(initServiceConfigurator);
    document.querySelectorAll('.showcase').forEach(initShowcase);
    document.querySelectorAll('.product').forEach(initProduct);
    initReveal();
    initToTop();
    const {API_CONFIG}=await import('./api/config.js?v=20261027.10');
    if(API_CONFIG.CATALOG_V2) {
      const {initContacts}=await import('./views/common/ContactsView.js?v=20261027.10');initContacts();
      const {initReviews}=await import('./views/common/ReviewsView.js?v=20261027.10');initReviews();
      const [{initSiteContent},{WorkGalleryView}]=await Promise.all([
        import('./views/common/SiteContentView.js?v=20261028.17'),
        import('./views/common/WorkGalleryView.js?v=20261027.10'),
      ]);
      await initSiteContent({initSwiper:initGallery,initWork:root=>new WorkGalleryView(root)});
    } else {
      document.querySelectorAll('.gallery').forEach(initGallery);
      document.querySelectorAll('.work-gallery').forEach(initWorkGallery);
    }
  });
})();
