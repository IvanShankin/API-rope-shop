import {apiClient} from './apiClient.js?v=20261106.1';
const auth = {requiresAuth: true};
export const settingsApi = {
  get: () => apiClient.get('/settings', auth),
  save: data => apiClient.patch('/settings', data, auth),
  changePassword: data => apiClient.post('/users/change-password', data, auth),
};
