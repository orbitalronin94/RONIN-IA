import test from 'node:test';
import assert from 'node:assert/strict';
import { BASE_MODEL, EXPERTS, selectExpert } from '../www/experts.js';

test('el modelo base actual sigue siendo el respaldo por defecto', () => {
  const selected = selectExpert('general');
  assert.equal(selected.model, BASE_MODEL);
  assert.equal(selected.status, 'active');
  assert.equal(selected.fallback, false);
});

test('el experto de código está disponible como modelo incluido en el paquete', () => {
  const selected = selectExpert('coding');
  assert.equal(selected.model, EXPERTS.coding.model);
  assert.equal(selected.status, 'active');
  assert.equal(selected.fallback, false);
  assert.equal(selected.source, 'bundled');
});

test('categorías aún no especializadas conservan el modelo base', () => {
  for (const category of ['math', 'language', 'instruction', 'unknown']) {
    assert.equal(selectExpert(category).model, BASE_MODEL);
  }
});

test('todos los expertos del catálogo están marcados como incluidos en el paquete', () => {
  assert.equal(EXPERTS.general.status, 'active');
  assert.equal(EXPERTS.coding.status, 'active');
  assert.equal(EXPERTS.general.source, 'bundled');
  assert.equal(EXPERTS.coding.source, 'bundled');
  assert.equal(EXPERTS.coding.estimatedDownloadMB, 0);
});
