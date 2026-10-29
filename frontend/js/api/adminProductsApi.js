import { apiClient } from './apiClient.js?v=20261027.10';
import { API_CONFIG } from './config.js?v=20261027.10';
import { adminCatalogApi } from './adminCatalogApi.js?v=20261027.10';

export const adminProductsApi = {
  list: () => apiClient.get('/rope_products'),
  detail: id => apiClient.get(`/rope_products/${Number(id)}`),
  groups: () => apiClient.get('/material_groups', { params: { locale: 'eng' } }),
  materials: () => apiClient.get('/splice_materials'),
  removeProduct: id => apiClient.delete(`/rope_products/${Number(id)}`, { requiresAuth: true }),
  removeVariant: id => apiClient.delete(`/rope_variants/${Number(id)}`, { requiresAuth: true }),
  orderVariant: (id, index) => apiClient.patch(`/rope_variants/${Number(id)}/index`, { new_index: index }, { requiresAuth: true }),
  saveProduct: (id, data) => id
    ? apiClient.patch(`/rope_products/${Number(id)}`, data, { requiresAuth: true })
    : apiClient.post('/rope_products', data, { requiresAuth: true }),
  saveVariant: (productId, id, data) => id
    ? apiClient.patch(`/rope_variants/${Number(id)}`, data, { requiresAuth: true })
    : apiClient.post(`/rope_products/${Number(productId)}/variants`, data, { requiresAuth: true }),
};
if (API_CONFIG.CATALOG_V2) Object.assign(adminProductsApi, adminCatalogApi);
