import test from 'node:test';
import assert from 'node:assert/strict';
import { BASE_MODEL, EXPERTS, selectExpert } from '../www/experts.js';

test('el modelo base actual sigue siendo el respaldo por defecto', () => {
  const selected = selectExpert('general');
  assert.equal(selected.model, BASE_MODEL);
  assert.equal(selected.status, 'active');
  assert.equal(selected.fallback, false);
});

test('el experto de código no se activa sin consentimiento explícito', () => {
  const selected = selectExpert('coding');
  assert.equal(selected.model, BASE_MODEL);
  assert.equal(selected.fallback, true);
  assert.equal(selected.requestedCategory, 'coding');
});

test('el experto de código solo se selecciona si está habilitado', () => {
  const selected = selectExpert('coding', { enabledExperts: ['coding'] });
  assert.equal(selected.model, EXPERTS.coding.model);
  assert.equal(selected.fallback, false);
  assert.equal(selected.requiresExplicitOptIn, true);
});

test('categorías aún no especializadas conservan el modelo base', () => {
  for (const category of ['math', 'language', 'instruction', 'unknown']) {
    assert.equal(selectExpert(category).model, BASE_MODEL);
  }
});

test('el catálogo distingue candidatos de modelos activos', () => {
  assert.equal(EXPERTS.general.status, 'active');
  assert.equal(EXPERTS.coding.status, 'candidate');
  assert.ok(EXPERTS.coding.estimatedDownloadMB >= 500);
});
