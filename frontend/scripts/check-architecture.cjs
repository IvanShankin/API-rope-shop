const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const path = require('node:path');

(async () => {
  const moduleAt = file => import(pathToFileURL(path.resolve(__dirname, '../js', file)));
  const { AdminProductModel: Model } = await moduleAt('models/AdminProductModel.js');
  const { AdminColorModel: Colors } = await moduleAt('models/AdminColorModel.js');
  const color = { code: ' green ', hex: '#aabbcc', eng: 'Green', ger: 'Gruen', is_active: true };
  assert.equal(Colors.payload(color).hex, '#AABBCC');
  assert.throws(() => Colors.payload({ ...color, hex: 'red' }));
  assert.doesNotThrow(() => Colors.payload({ ...color, eng: '' }));
  assert.throws(() => Colors.payload({ ...color, eng: '', ger: '', rus: '' }));
  assert.deepEqual(Colors.linkChanges([{ id: 20, color_id: 1 }, { id: 21, color_id: 2 }], [2, 3, 3]), { add: [3], remove: [20] });
  assert.deepEqual(Colors.linkChanges([{ id: 21, color_id: 2 }, { id: 22, color_id: 3 }], [2, 3]), { add: [], remove: [] });
  const variant = { diameter_mm: '6', price_per_meter: '0', breaking_load_dan: '', weight_g_per_m: '', is_active: false };
  assert.deepEqual(Model.variant(variant), { diameter_mm: 6, price_per_meter: 0, breaking_load_dan: null, weight_g_per_m: null, is_active: false });
  for (const value of ['', '-1', 'Infinity', 'bad']) assert.throws(() => Model.variant({ ...variant, price_per_meter: value }));
  assert.throws(() => Model.variant({ ...variant, diameter_mm: '0' }));
  const product = { material_group_id: '1', splice_material_id: '2', construction: ' test ', can_be_spliced: true };
  assert.equal(Model.product(product).construction, 'test');
  assert.throws(() => Model.product({ ...product, material_group_id: '1.5' }));
  assert.throws(() => Model.product({ ...product, working_stretch_percent: '101' }));

  global.window = { location: { hostname: 'localhost' } };
  const { authApi } = await require('./frontend-module.cjs')('api/authApi.js');
  const { AuthModel } = await moduleAt('models/AuthModel.js');
  let cleared = 0;
  authApi.isAuthenticated = () => true;
  authApi.clearSession = () => { cleared++; };
  for (const status of [undefined, 500]) {
    authApi.getMe = async () => { throw Object.assign(new Error('temporary'), { status }); };
    const model = new AuthModel();
    await assert.rejects(model.checkSession());
    assert.equal(cleared, 0);
    assert.equal(model.isLoading, false);
    assert.equal(model.user, null);
  }
  authApi.getMe = async () => { throw Object.assign(new Error('expired'), { status: 401 }); };
  assert.equal(await new AuthModel().checkSession(), null);
  assert.equal(cleared, 1);
  console.log('PASS: DOM-free product/variant DTO validation; network failures retain credentials; 401 clears session.');
})().catch(error => { console.error(error); process.exitCode = 1; });
