import test from 'node:test';
import assert from 'node:assert/strict';
import {
  LOCAL_MODEL_ID,
  LOCAL_MODEL_REVISION,
  FALLBACK_MODEL_ID,
  LOCAL_MODEL_ARTIFACT_MB,
  requestLocalCompletion,
} from '../www/local-ai.js';

test('la inferencia local requiere mensajes y propone Qwen3 DQ-ONNX por debajo de 400 MB', async () => {
  await assert.rejects(requestLocalCompletion({ messages: [] }), /al menos un mensaje/i);
  assert.equal(LOCAL_MODEL_ID, 'onnx-community/Qwen3-0.6B-DQ-ONNX');
  assert.equal(LOCAL_MODEL_REVISION, 'd6beae7');
  assert.equal(FALLBACK_MODEL_ID, 'onnx-community/Qwen2.5-0.5B-Instruct');
  assert.ok(LOCAL_MODEL_ARTIFACT_MB < 400);
});

test('carga Qwen3 una sola vez, recurre al modelo anterior si falla y devuelve la respuesta', async () => {
  let loads = 0;
  let calls = 0;
  const attemptedModels = [];
  const loader = async () => {
    loads++;
    return {
      env: {},
      pipeline: async (task, model, options) => {
        assert.equal(task, 'text-generation');
        attemptedModels.push(model);
        assert.equal(options.device, 'wasm');
        if (model === LOCAL_MODEL_ID) {
          assert.equal(options.dtype, 'q4f16');
          assert.equal(options.revision, LOCAL_MODEL_REVISION);
          throw new Error('simulated missing Qwen3 weights');
        }
        assert.equal(model, FALLBACK_MODEL_ID);
        assert.equal(options.dtype, 'q4');
        return async (messages, generation) => {
          calls++;
          assert.equal(messages.at(-1).content, 'Hola');
          assert.equal(generation.max_new_tokens, 256);
          return [{ generated_text: [{ role: 'user', content: 'Hola' }, { role: 'assistant', content: '¡Hola desde Ronin!' }] }];
        };
      },
    };
  };
  const first = await requestLocalCompletion({ messages: [{ role: 'user', content: 'Hola' }], loader });
  const second = await requestLocalCompletion({ messages: [{ role: 'user', content: 'Hola' }], loader });
  assert.equal(first, '¡Hola desde Ronin!');
  assert.equal(second, first);
  assert.deepEqual(attemptedModels, [LOCAL_MODEL_ID, FALLBACK_MODEL_ID]);
  assert.equal(loads, 1);
  assert.equal(calls, 2);
});
