// Inferencia local opcional. Los pesos se descargan bajo demanda y nunca forman parte de la APK.
// Modelo ONNX de Qwen2.5-0.5B-Instruct; la primera carga puede descargar cientos de MB.
export const LOCAL_MODEL_ID = 'onnx-community/Qwen2.5-0.5B-Instruct';
const TRANSFORMERS_CDN = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.2/+esm';
let pipelinePromise;

async function createPipeline({ loader, onProgress }) {
  const module = await loader();
  const { env, pipeline } = module;
  env.allowRemoteModels = true;
  env.useBrowserCache = true;
  // WASM funciona en más dispositivos; WebGPU usa un modelo de menor tamaño si está disponible.
  const hasWebGPU = typeof navigator !== 'undefined' && !!navigator.gpu;
  const device = hasWebGPU ? 'webgpu' : 'wasm';
  const dtype = hasWebGPU ? 'q4f16' : 'q4';
  try {
    return await pipeline('text-generation', LOCAL_MODEL_ID, {
      device,
      dtype,
      progress_callback: (event) => {
        if (event && typeof event === 'object') onProgress?.(event);
      },
    });
  } catch (error) {
    if (!hasWebGPU) throw error;
    // Algunos WebViews anuncian WebGPU pero no soportan todos los operadores requeridos.
    onProgress?.({ status: 'fallback', message: 'Aceleración GPU no compatible; usando CPU.' });
    return pipeline('text-generation', LOCAL_MODEL_ID, {
      device: 'wasm',
      dtype: 'q4',
      progress_callback: (event) => {
        if (event && typeof event === 'object') onProgress?.(event);
      },
    });
  }
}

export async function loadLocalModel({
  loader = () => import(TRANSFORMERS_CDN),
  onProgress,
} = {}) {
  if (!pipelinePromise) {
    pipelinePromise = createPipeline({ loader, onProgress }).catch((error) => {
      pipelinePromise = undefined;
      throw error;
    });
  }
  return pipelinePromise;
}

export async function requestLocalCompletion({
  messages,
  onProgress,
  loader,
  generateOptions = {},
} = {}) {
  if (!Array.isArray(messages) || messages.length === 0) {
    throw new TypeError('Se necesita al menos un mensaje para usar el modelo local.');
  }
  const pipe = await loadLocalModel({ loader, onProgress });
  const result = await pipe(
    messages.slice(-7).map(({ role, content }) => ({
      role: role === 'assistant' ? 'assistant' : role === 'system' ? 'system' : 'user',
      content: String(content ?? '').slice(0, 3000),
    })),
    {
      max_new_tokens: 256,
      do_sample: false,
      return_full_text: false,
      ...generateOptions,
    },
  );
  const generated = result?.[0]?.generated_text;
  const answer = typeof generated === 'string'
    ? generated.trim()
    : Array.isArray(generated)
      ? String(generated.filter((message) => message?.role === 'assistant').at(-1)?.content ?? '').trim()
      : '';
  if (!answer) throw new Error('El modelo local no devolvió texto. Prueba con una pregunta más corta.');
  return answer;
}
