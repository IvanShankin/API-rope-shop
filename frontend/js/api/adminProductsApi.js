import { apiClient } from './apiClient.js?v=20261106.1';
import { adminCatalogApi } from './adminCatalogApi.js?v=20261106.1';

// Товары, фото и категории — через общий каталог (/products), здесь только
// справочники и варианты диаметров.
export const adminProductsApi = {
  ...adminCatalogApi,
  // Админке нужны и скрытые записи, поэтому запросы идут с токеном.
  groups: () => apiClient.get('/material_groups', { params: { locale: 'eng' }, requiresAuth: true }),
  materials: () => apiClient.get('/splice_materials', { requiresAuth: true }),
  removeVariant: id => apiClient.delete(`/rope_variants/${Number(id)}`, { requiresAuth: true }),
  orderVariant: (id, index) => apiClient.patch(`/rope_variants/${Number(id)}/index`, { new_index: index }, { requiresAuth: true }),
  saveVariant: (productId, id, data) => id
    ? apiClient.patch(`/rope_variants/${Number(id)}`, data, { requiresAuth: true })
    : apiClient.post(`/rope_products/${Number(productId)}/variants`, data, { requiresAuth: true }),
};
