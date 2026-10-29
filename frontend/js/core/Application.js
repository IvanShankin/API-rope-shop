/**
 * ЕДИНОЕ ЯДРО ПРИЛОЖЕНИЯ (Application Core)
 * Архитектура: Micro-Kernel / Registry Pattern с ленивой загрузкой контроллеров
 * 
 * Обязанности:
 * 1. Регистрация контроллеров (реестр).
 * 2. Обнаружение элементов в DOM (декларативные data-controller и fallback-селекторы).
 * 3. Ленивая асинхронная подгрузка модулей (Code Splitting через динамический import).
 * 4. Изоляция ошибок (Error Boundary) — сбой в одном контроллере не ломает остальные.
 * 5. Управление жизненным циклом (init / destroy).
 */

export class Application {
  constructor() {
    /** @type {Map<string, { loader: Function, fallbackSelector: ?string }>} */
    this.registry = new Map();

    /** @type {Map<string, Object>} */
    this.activeControllers = new Map();

    /** @type {boolean} */
    this.isStarted = false;
  }

  /**
   * Регистрирует контроллер в реестре приложения
   * @param {string} name - Уникальное имя контроллера (используется в [data-controller="name"])
   * @param {() => Promise<any>} loader - Фабрика динамического импорта () => import('./...')
   * @param {string|null} [fallbackSelector=null] - Селектор для обратной совместимости
   * @returns {Application} this (для чейнинга)
   */
  register(name, loader, fallbackSelector = null) {
    if (typeof loader !== 'function') {
      throw new TypeError(`[Application.register] Загрузчик для "${name}" должен быть функцией динамического импорта.`);
    }

    this.registry.set(name, { loader, fallbackSelector });
    return this;
  }

  /**
   * Запуск приложения и инициализация контроллеров для элементов текущей страницы
   * @returns {Promise<void>}
   */
  async start() {
    if (this.isStarted) {
      console.warn('[Application] Приложение уже запущено. Повторный запуск проигнорирован.');
      return;
    }

    this.isStarted = true;
    console.groupCollapsed('Инициализация клиентского приложения');

    const mountTasks = [];

    for (const [name, config] of this.registry.entries()) {
      const elements = this._findControllerElements(name, config.fallbackSelector);

      if (elements.length > 0) {
        mountTasks.push(this._mountController(name, config.loader, elements));
      }
    }

    // Параллельный запуск всех подходящих контроллеров с гарантией изоляции ошибок
    const results = await Promise.allSettled(mountTasks);

    let successCount = 0;
    results.forEach((res) => {
      if (res.status === 'fulfilled') {
        successCount++;
      }
    });

    console.info(`Успешно активировано контроллеров: ${successCount} из ${mountTasks.length}`);
    console.groupEnd();
  }

  /**
   * Поиск элементов для контроллера по декларативному data-controller или fallback-селектору
   * @private
   * @param {string} name
   * @param {?string} fallbackSelector
   * @returns {NodeList|Array<Element>}
   */
  _findControllerElements(name, fallbackSelector) {
    // 1. Приоритетный поиск по строгому стандарту data-controller (поддержка списков через пробел: data-controller="common auth")
    const strictSelector = `[data-controller~="${name}"]`;
    let elements = document.querySelectorAll(strictSelector);

    // 2. Если по data-controller не найдено, но задан fallback-селектор (для обратной совместимости)
    if (!elements.length && fallbackSelector) {
      try {
        elements = document.querySelectorAll(fallbackSelector);
      } catch (err) {
        console.warn(`[Application] Некорректный fallback-селектор "${fallbackSelector}" для контроллера "${name}":`, err);
        return [];
      }
    }

    return elements;
  }

  /**
   * Ленивая загрузка модуля, создание инстанса и запуск контроллера
   * @private
   * @param {string} name
   * @param {Function} loader
   * @param {NodeList|Array<Element>} elements
   * @returns {Promise<Object>}
   */
  async _mountController(name, loader, elements) {
    try {
      console.info(`📦 [Application] Загрузка модуля контроллера: [${name}]...`);

      // Динамический импорт — файл скачивается браузером ТОЛЬКО в этот момент!
      const module = await loader();

      // Определение класса контроллера (именованный экспорт, default или первый найденный класс)
      const ControllerClass = this._resolveControllerClass(name, module);

      if (!ControllerClass) {
        throw new Error(`Модуль для "${name}" не содержит подходящего конструктора контроллера.`);
      }

      // Создаем экземпляр контроллера, передавая корневой элемент (или список элементов)
      const rootElement = elements.length === 1 ? elements[0] : elements;
      const instance = new ControllerClass(rootElement);

      // Запуск асинхронного init(), если метод определен
      if (typeof instance.init === 'function') {
        await instance.init();
      }

      this.activeControllers.set(name, instance);
      console.info(`✅ Контроллер [${name}] успешно запущен.`);
      return instance;
    } catch (error) {
      console.error(`❌ Ошибка при монтировании контроллера [${name}]:`, error);
      throw error;
    }
  }

  /**
   * Разрешение класса контроллера из экспортов модуля
   * @private
   * @param {string} name
   * @param {Object} module
   * @returns {Function|null}
   */
  _resolveControllerClass(name, module) {
    // 1. Именованный экспорт вида FooController (например, ConfiguratorController)
    const pascalName = `${name.charAt(0).toUpperCase() + name.slice(1)}Controller`;
    if (typeof module[pascalName] === 'function') {
      return module[pascalName];
    }

    // 2. Именованный экспорт с точным именем (например, Configurator)
    if (typeof module[name] === 'function') {
      return module[name];
    }

    // 3. Default экспорт
    if (typeof module.default === 'function') {
      return module.default;
    }

    // 4. Первый экспортированный класс / функция
    const firstExport = Object.values(module).find((exp) => typeof exp === 'function');
    return firstExport || null;
  }

  /**
   * Получение активного экземпляра контроллера по имени
   * @param {string} name
   * @returns {Object|undefined}
   */
  getController(name) {
    return this.activeControllers.get(name);
  }

  /**
   * Словарь всех активных контроллеров (для обратной совместимости с app.controllers.name)
   * @returns {Object<string, Object>}
   */
  get controllers() {
    return Object.fromEntries(this.activeControllers);
  }

  /**
   * Корректная остановка и очистка контроллеров (деструктор)
   */
  destroy() {
    for (const [name, controller] of this.activeControllers.entries()) {
      if (typeof controller.destroy === 'function') {
        try {
          controller.destroy();
        } catch (err) {
          console.warn(`[Application] Ошибка при вызове destroy() у [${name}]:`, err);
        }
      }
    }

    this.activeControllers.clear();
    this.isStarted = false;
    console.info('[Application] Все контроллеры остановлены.');
  }
}
