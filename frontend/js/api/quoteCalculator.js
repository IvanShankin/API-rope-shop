import { quoteApi } from './quoteApi.js?v=20261106.1';

// Понятный текст ошибки расчёта. Бекенд отвечает 400 с английским detail,
// поэтому узнаём частые случаи по тексту и не показываем покупателю сырой ответ.
export function calculationErrorMessage(error) {
  const detail = String(error?.data?.detail || '');
  if (error?.network) return { text: `${error.message}. Цена не пересчитана.`, retry: true };
  if (error?.status === 429) return { text: 'Слишком много пересчётов подряд. Подождите минуту и обновите цену.', retry: true };
  if (error?.status >= 500 || !error?.status) return { text: 'Сервер не смог посчитать стоимость. Попробуйте обновить цену.', retry: true };
  if (/pricing rule/i.test(detail)) return { text: 'Для выбранной обработки и диаметра нет тарифа. Выберите другой вариант.', retry: false };
  if (/urgent/i.test(detail)) return { text: 'Срочное изготовление недоступно для такого количества сращиваний.', retry: false };
  if (/per-loop/i.test(detail)) return { text: 'Выбранная опция доступна только при заказе с петлёй.', retry: false };
  if (/length/i.test(detail)) return { text: 'Длина вне допустимого диапазона.', retry: false };
  if (/color/i.test(detail)) return { text: 'Этот цвет недоступен для выбранного каната.', retry: false };
  if (/splic/i.test(detail)) return { text: 'Выбранная обработка недоступна для этого каната.', retry: false };
  if (error?.status === 404) return { text: 'Часть выбранных вариантов больше недоступна. Обновите страницу.', retry: false };
  return { text: 'Эту комбинацию нельзя рассчитать. Измените параметры или опишите задачу в заявке.', retry: false };
}

/**
 * Пересчёт цены на сервере (POST /quote_requests/calculate) с задержкой после ввода.
 * Ответы на устаревшие параметры отбрасываются, одинаковые запросы берутся из кеша,
 * чтобы не упираться в лимит бекенда (60 расчётов в минуту).
 */
export class QuoteCalculator {
  constructor({ onStart, onResult, onError, delay = 400 } = {}) {
    Object.assign(this, { onStart, onResult, onError, delay });
    this.cache = new Map();
    this.seq = 0;
  }

  schedule(payload) {
    clearTimeout(this.timer);
    const seq = ++this.seq;
    if (!payload) return;
    const key = JSON.stringify(payload);
    if (this.cache.has(key)) { this.onResult?.(this.cache.get(key), key); return; }
    this.onStart?.(key);
    this.timer = setTimeout(() => this.run(payload, key, seq), this.delay);
  }

  // Повторить сразу, без кеша (кнопка «Обновить цену»).
  retry(payload) {
    clearTimeout(this.timer);
    if (!payload) return;
    const key = JSON.stringify(payload);
    this.cache.delete(key);
    this.onStart?.(key);
    this.run(payload, key, ++this.seq);
  }

  cancel() { clearTimeout(this.timer); this.seq += 1; }

  async run(payload, key, seq) {
    try {
      const result = await quoteApi.calculate(payload);
      if (seq !== this.seq) return;
      if (!result || !Number.isFinite(Number(result.total_price))) throw new Error('Сервер вернул неполный расчёт.');
      if (this.cache.size > 50) this.cache.delete(this.cache.keys().next().value);
      this.cache.set(key, result);
      this.onResult?.(result, key);
    } catch (error) {
      if (seq === this.seq) this.onError?.(calculationErrorMessage(error), key);
    }
  }
}
