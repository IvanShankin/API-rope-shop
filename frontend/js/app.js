/**
 * ЕДИНАЯ ТОЧКА ВХОДА В ПРИЛОЖЕНИЕ (Application Bootstrap)
 * Связывает точку входа с архитектурным ядром Application и регистрирует контроллеры с ленивой загрузкой
 */

import { Application } from './core/Application.js?v=20261027.10';

// 1. Создаем экземпляр ядра приложения
const app = new Application();

// 2. Регистрируем контроллеры в реестре (модули будут скачиваться браузером ТОЛЬКО при наличии элементов в DOM)
app
  // Общий контроллер для всех страниц (шапка, меню, плавный скролл, кнопка "наверх")
  .register('common', () => import('./controllers/CommonController.js?v=20261028.17'), 'body')
  // Интерактивный 3D/SVG конфигуратор канатов и заделок
  .register('configurator', () => import('./controllers/ConfiguratorController.js?v=20261027.10'), '#configurator, .configurator')
  .register('services', () => import('./controllers/ServicesController.js?v=20261027.10'), '[data-service-mode]')
  // Каталог товаров и фильтрация
  .register('catalog', () => import('./controllers/CatalogController.js?v=20261027.10'), '[data-catalog]')
  // Форма авторизации в административную панель
  .register('login', () => import('./controllers/LoginController.js?v=20261027.10'), '#admin-login-form')
  // Панель управления администратора
  .register('admin', () => import('./controllers/AdminController.js?v=20261028.18'), '.admin');

// 3. Экспортируем в глобальную область для отладки в консоли браузера
window.RopeApp = app;

// 4. Запуск жизненного цикла приложения при готовности DOM дерева
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => app.start());
} else {
  app.start();
}

export default app;
