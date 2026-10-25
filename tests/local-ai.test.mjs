import test from 'node:test';
import assert from 'node:assert/strict';
import { LOCAL_MODEL_ID, loadLocalModel, requestLocalCompletion } from '../www/local-ai.js';

test('la inferencia local requiere mensajes y no consulta el endpoint remoto', async () => {
  await assert.rejects(requestLocalCompletion({ messages: [] }), /al menos un mensaje/i);
  assert.equal(LOCAL_MODEL_ID, 'onnx-community/Qwen2.5-0.5B-Instruct');
});

test('carga el modelo una sola vez y devuelve la respuesta generada', async () => {
  let loads = 0;
  let calls = 0;
  const loader = async () => {
    loads++;
    return {
      env: {},
      pipeline: async (task, model, options) => {
        assert.equal(task, 'text-generation');
        assert.equal(model, LOCAL_MODEL_ID);
        assert.equal(options.device, 'wasm');
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
  assert.equal(loads, 1);
  assert.equal(calls, 2);
});
