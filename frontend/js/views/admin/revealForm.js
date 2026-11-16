// Плавно прокручивает страницу к форме добавления и ставит курсор в нужное поле.
// Используется всеми кнопками «Добавить» в админке.
export function revealForm(target, focusSelector = 'input:not([type=hidden]):not([type=checkbox]):not([disabled]), select:not([disabled]), textarea:not([disabled])', block = 'start') {
  if (!target) return;
  const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  // Ждём, пока форма появится на странице, затем прокручиваем.
  requestAnimationFrame(() => {
    target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block });
    const field = focusSelector ? target.querySelector(focusSelector) : null;
    field?.focus({ preventScroll: true });
  });
}
