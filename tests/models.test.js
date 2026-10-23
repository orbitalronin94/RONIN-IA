import test from 'node:test';
import assert from 'node:assert/strict';
import { MODEL_BUNDLE } from '../scripts/prepare-models.mjs';

test('el build prepara los dos modelos que usa el router', () => {
  assert.deepEqual(MODEL_BUNDLE.map(model => model.id), [
    'onnx-community/Qwen3-0.6B-ONNX',
    'onnx-community/Qwen2.5-Coder-0.5B-Instruct',
  ]);
});

test('cada modelo se prepara con una única variante q4 para GPU/CPU', () => {
  for (const model of MODEL_BUNDLE) {
    assert.equal(model.dtype, 'q4');
    assert.ok(model.files.includes('onnx/model_q4.onnx'));
    assert.ok(model.files.includes('config.json'));
    assert.ok(model.files.includes('tokenizer.json'));
  }
});
