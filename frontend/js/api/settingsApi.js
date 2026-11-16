import {apiClient} from './apiClient.js?v=20261116.1';
const auth = {requiresAuth: true};
export const settingsApi = {
  get: () => apiClient.get('/settings', auth),
  save: data => apiClient.patch('/settings', data, auth),
  changePassword: data => apiClient.post('/users/change-password', data, auth),
  // Тестовая отправка: без адреса бэкенд берёт его из сохранённых настроек.
  testTelegram: chatId => apiClient.post('/notifications/test/telegram', chatId ? {chat_id: chatId} : {}, auth),
  testEmail: toEmail => apiClient.post('/notifications/test/email', toEmail ? {to_email: toEmail} : {}, auth),
};
