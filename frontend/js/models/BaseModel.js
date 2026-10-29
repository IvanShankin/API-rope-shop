/**
 * Базовая модель с паттерном Observer (Event Emitter)
 * Позволяет View и Controller подписываться на изменения данных
 */
export class BaseModel {
  constructor() {
    this._listeners = new Map();
  }

  /**
   * Подписаться на событие
   * @param {string} event
   * @param {Function} callback
   */
  on(event, callback) {
    if (!this._listeners.has(event)) {
      this._listeners.set(event, new Set());
    }
    this._listeners.get(event).add(callback);
    return () => this.off(event, callback);
  }

  /**
   * Отписаться от события
   * @param {string} event
   * @param {Function} callback
   */
  off(event, callback) {
    if (this._listeners.has(event)) {
      this._listeners.get(event).delete(callback);
    }
  }

  /**
   * Оповестить подписчиков о событии
   * @param {string} event
   * @param {*} [data]
   */
  emit(event, data) {
    if (this._listeners.has(event)) {
      this._listeners.get(event).forEach((cb) => {
        try {
          cb(data);
        } catch (err) {
          console.error(`Ошибка в обработчике события ${event}:`, err);
        }
      });
    }
  }
}
