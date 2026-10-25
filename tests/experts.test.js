import test from 'node:test';
import assert from 'node:assert/strict';
import { BASE_MODEL, EXPERTS, selectExpert } from '../www/experts.js';

test('el modelo base actual sigue siendo el respaldo por defecto', () => {
  const selected = selectExpert('general');
  assert.equal(selected.model, BASE_MODEL);
  assert.equal(selected.status, 'active');
  assert.equal(selected.fallback, false);
});

test('el perfil de código usa el proveedor remoto actual', () => {
  const selected = selectExpert('coding');
  assert.equal(selected.model, EXPERTS.coding.model);
  assert.equal(selected.status, 'active');
  assert.equal(selected.fallback, false);
  assert.equal(selected.source, 'remote');
});

test('categorías aún no especializadas conservan el modelo base', () => {
  for (const category of ['math', 'language', 'instruction', 'unknown']) {
    assert.equal(selectExpert(category).model, BASE_MODEL);
  }
});

test('el catálogo no afirma que los pesos estén incluidos en el paquete', () => {
  assert.equal(EXPERTS.general.status, 'active');
  assert.equal(EXPERTS.coding.status, 'active');
  assert.equal(EXPERTS.general.source, 'remote');
  assert.equal(EXPERTS.coding.source, 'remote');
  assert.equal(EXPERTS.coding.estimatedDownloadMB, 0);
});
