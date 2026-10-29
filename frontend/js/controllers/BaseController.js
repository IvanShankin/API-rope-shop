/**
 * Базовый контроллер приложения
 */
export class BaseController {
  constructor() {
    this.isInitialized = false;
  }

  async init() {
    this.isInitialized = true;
  }

  destroy() {
    this.isInitialized = false;
  }
}
