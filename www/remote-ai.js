// Cliente para el gateway público experimental LLMFaucet.
// Sin clave personal: "free" es el marcador documentado para clientes que exigen Authorization.
// El servicio es comunitario, limitado y no debe recibir secretos ni datos sensibles.
export const REMOTE_AI_ENDPOINT = 'https://api.llmfaucet.dev/v1/chat/completions';

export function selectRemoteModel(messages = []) {
  const lastUser = [...messages].reverse().find((message) => message?.role === 'user');
  const prompt = String(lastUser?.content ?? '');
  if (/\b(código|programar|programación|debug|depura|javascript|typescript|python|sql|algoritmo|script|github)\b/i.test(prompt)) {
    return 'auto:coding';
  }
  if (/\b(compara en profundidad|razonamiento complejo|demuestra|analiza exhaustivamente|problema difícil)\b/i.test(prompt)) {
    return 'auto:smart';
  }
  return 'auto:fast';
}

export async function requestRemoteCompletion({
  messages,
  fetchImpl = globalThis.fetch,
  timeoutMs = 35000,
} = {}) {
  if (!Array.isArray(messages) || messages.length === 0) {
    throw new TypeError('Se necesita al menos un mensaje para consultar la IA remota.');
  }
  if (typeof fetchImpl !== 'function') throw new TypeError('Fetch no está disponible en este entorno.');

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(REMOTE_AI_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer free',
      },
      body: JSON.stringify({
        model: selectRemoteModel(messages),
        messages: messages.slice(-9).map(({ role, content }) => ({
          role: role === 'assistant' ? 'assistant' : role === 'system' ? 'system' : 'user',
          content: String(content ?? '').slice(0, 6000),
        })),
        max_tokens: 600,
        temperature: 0.6,
        stream: false,
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      if (response.status === 429) throw new Error('La cuota anónima de IA se ha agotado temporalmente (HTTP 429).');
      if (response.status === 401 || response.status === 403) throw new Error('El endpoint público rechazó la solicitud (HTTP ' + response.status + ').');
      throw new Error('El endpoint público no está disponible (HTTP ' + response.status + ').');
    }

    const data = await response.json();
    const content = data?.choices?.[0]?.message?.content;
    const answer = typeof content === 'string'
      ? content.trim()
      : Array.isArray(content)
        ? content.map((part) => typeof part?.text === 'string' ? part.text : '').join('').trim()
        : '';
    if (!answer) throw new Error('La IA remota no devolvió texto. Inténtalo de nuevo.');
    return answer;
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error('La IA remota tardó demasiado en responder. Inténtalo más tarde o cambia al modelo local.');
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
