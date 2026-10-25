import test from 'node:test';
import assert from 'node:assert/strict';
import { REMOTE_AI_ENDPOINT, requestRemoteCompletion, selectRemoteModel } from '../www/remote-ai.js';

test('selecciona modelos públicos por tipo de pregunta', () => {
  assert.equal(selectRemoteModel([{ role: 'user', content: 'Explícame una idea' }]), 'auto:fast');
  assert.equal(selectRemoteModel([{ role: 'user', content: 'Ayúdame a programar una función en JavaScript' }]), 'auto:coding');
  assert.equal(selectRemoteModel([{ role: 'user', content: 'Analiza exhaustivamente este problema difícil' }]), 'auto:smart');
});

test('solicita chat al endpoint anónimo compatible con OpenAI sin una clave personal', async () => {
  let captured;
  const answer = await requestRemoteCompletion({
    messages: [
      { role: 'system', content: 'Responde en español.' },
      { role: 'user', content: 'Hola' },
    ],
    fetchImpl: async (url, options) => {
      captured = { url, options, body: JSON.parse(options.body) };
      return new Response(JSON.stringify({ choices: [{ message: { content: '¡Hola!' } }] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    },
  });

  assert.equal(answer, '¡Hola!');
  assert.equal(captured.url, REMOTE_AI_ENDPOINT);
  assert.equal(captured.options.method, 'POST');
  assert.equal(captured.options.headers.Authorization, 'Bearer free');
  assert.equal(captured.body.model, 'auto:fast');
  assert.equal(captured.body.stream, false);
  assert.equal(captured.body.messages.length, 2);
});

test('convierte los límites anónimos HTTP 429 en un error comprensible', async () => {
  await assert.rejects(
    requestRemoteCompletion({
      messages: [{ role: 'user', content: 'Hola' }],
      fetchImpl: async () => new Response('rate limited', { status: 429 }),
    }),
    /cuota anónima.*HTTP 429/i,
  );
});

test('rechaza una respuesta vacía del proveedor', async () => {
  await assert.rejects(
    requestRemoteCompletion({
      messages: [{ role: 'user', content: 'Hola' }],
      fetchImpl: async () => new Response(JSON.stringify({ choices: [] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    }),
    /no devolvió texto/i,
  );
});

test('valida que exista al menos un mensaje antes de hacer la petición', async () => {
  await assert.rejects(requestRemoteCompletion({ messages: [] }), /al menos un mensaje/i);
});
