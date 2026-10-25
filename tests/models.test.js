import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';

const packageJson = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
const androidWorkflow = readFileSync(new URL('../.github/workflows/build-android.yml', import.meta.url), 'utf8');
const expertsSource = readFileSync(new URL('../www/experts.js', import.meta.url), 'utf8');

test('el build no ofrece un paso que descargue modelos de varios GB', () => {
  assert.equal(packageJson.scripts['prepare:models'], undefined);
  assert.equal(packageJson.scripts['sync:android'], undefined);
  assert.equal(existsSync(new URL('../scripts/prepare-models.mjs', import.meta.url)), false);
  assert.doesNotMatch(androidWorkflow, /prepare-models|prepare:models|onnx-community/);
});

test('el runtime ligero no instala una biblioteca de inferencia local que no utiliza', () => {
  assert.equal(packageJson.dependencies['@huggingface/transformers'], undefined);
  assert.equal(packageJson.devDependencies.esbuild, undefined);
  assert.match(expertsSource, /source: 'remote'/);
  assert.match(expertsSource, /No model weights are bundled/);
});

test('la compilación de Android conserva la comprobación que excluye pesos ONNX', () => {
  assert.match(androidWorkflow, /no deben empaquetarse|pesos ONNX/);
  assert.match(androidWorkflow, /APK_MIB/);
});
