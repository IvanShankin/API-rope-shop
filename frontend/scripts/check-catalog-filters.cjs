const assert = require('node:assert/strict');

(async () => {
  const { CatalogModel } = await import('../js/models/CatalogModel.js');
  const model = new CatalogModel();
  const variants = [{ diameter_mm: '8', is_active: true }, { diameter_mm: 14, is_active: false }];
  model.setData({ materialGroups: [], products: [
    { product_id: 1, material_group_id: 1, construction_type: 'hollow', has_configurator: true, variants },
    { product_id: 2, material_group_id: 1, construction_type: 'hm_core', has_configurator: false, variants: [{ diameter_mm: 10 }] },
    { product_id: 3, material_group_id: 2, construction_type: 'hollow', has_configurator: true, variants: [{ diameter_mm: 12 }] },
    { product_id: 4, material_group_id: 1, construction_type: 'hollow', has_configurator: true, variants: [] },
  ] });
  const ids = () => model.getFilteredProducts().map(p => p.product_id);
  model.setFilterGroup(1);
  assert.deepEqual(model.getFilterOptions().diameters, [8, 10]);
  model.setFilters({ construction: 'hollow', diameter: '8', configurator: true });
  assert.deepEqual(ids(), [1]);
  model.setFilters({ diameter: 14 });
  assert.deepEqual(ids(), [], 'Inactive variant cannot satisfy diameter filter');
  model.setFilters({ construction: 'hm_core', configurator: '1' });
  assert.deepEqual(ids(), []);
  model.setFilters({ configurator: true });
  assert.deepEqual(ids(), [1], 'A configurator needs an available variant');
  model.setFilters({ diameter: 'Infinity' });
  assert.equal(model.filters.diameter, '');
  model.setFilters({ diameter: '-8' });
  assert.equal(model.filters.diameter, '');
  model.setFilters({});
  assert.deepEqual(ids(), [1, 2, 4], 'Reset preserves category');
  assert.equal(variants.length, 2, 'Filtering does not mutate API data');
  console.log('PASS: category, combined filters, unavailable variants, empty results, URL values, reset and immutable data');
})().catch(error => { console.error(error); process.exitCode = 1; });
