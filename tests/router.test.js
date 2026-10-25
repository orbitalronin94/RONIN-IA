import test from 'node:test';
import assert from 'node:assert/strict';
import { routeRequest } from '../www/router.js';

test('routes programming requests to coding profile', () => {
  const result = routeRequest('Ayúdame a depurar este error en Python');
  assert.equal(result.category, 'coding');
  assert.match(result.profile, /programación/);
});

test('routes explicit calculations to math profile', () => {
  assert.equal(routeRequest('Resuelve esta ecuación de álgebra').category, 'math');
});

test('routes translation and writing requests to language profile', () => {
  assert.equal(routeRequest('Traduce este párrafo al inglés').category, 'language');
});

test('routes strict formatting requests to instruction profile', () => {
  assert.equal(routeRequest('Responde solo en formato JSON').category, 'instruction');
});

test('falls back to general and reports the one currently connected model', () => {
  const result = routeRequest('¿Qué es la fotosíntesis?');
  assert.equal(result.category, 'general');
  assert.equal(result.model, 'auto:fast');
});

test('is deterministic and safely accepts empty/non-string input', () => {
  assert.deepEqual(routeRequest('Write a Python function'), routeRequest('Write a Python function'));
  assert.equal(routeRequest('').category, 'general');
  assert.equal(routeRequest(null).category, 'general');
});
