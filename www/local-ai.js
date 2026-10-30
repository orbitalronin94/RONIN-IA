// Inferencia local opcional. El candidato Qwen3 se carga bajo demanda; el fallback conserva compatibilidad.
export const LOCAL_MODEL_ID = 'onnx-community/Qwen3-0.6B-DQ-ONNX';
export const LOCAL_MODEL_REVISION = 'd6beae7';
export const FALLBACK_MODEL_ID = 'onnx-community/Qwen2.5-0.5B-Instruct';
export const LOCAL_MODEL_ARTIFACT_MB = 356;
const TRANSFORMERS_CDN = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.2/+esm';
const IS_NATIVE_ANDROID = typeof window !== 'undefined' && window.Capacitor?.getPlatform?.() === 'android';
let pipelinePromise;

async function createPipeline({ loader, onProgress }) {
  const module = await loader();
  const { env, pipeline } = module;
  env.allowLocalModels = true;
  // En la APK offline, un archivo ausente debe fallar localmente; nunca se consulta Hugging Face.
  env.allowRemoteModels = !IS_NATIVE_ANDROID;
  env.localModelPath = './models/';
  env.useBrowserCache = !IS_NATIVE_ANDROID;

  if (IS_NATIVE_ANDROID && env.backends?.onnx?.wasm) {
    env.backends.onnx.wasm.wasmPaths = './vendor/';
  }

  const hasWebGPU = !IS_NATIVE_ANDROID && typeof navigator !== 'undefined' && !!navigator.gpu;
  const device = hasWebGPU ? 'webgpu' : 'wasm';

  try {
    // Qwen3 DQ-ONNX publica pesos q4f16 y es compatible con Transformers.js.
    return await pipeline('text-generation', LOCAL_MODEL_ID, {
      device,
      dtype: 'q4f16',
      revision: LOCAL_MODEL_REVISION,
      progress_callback: (event) => {
        if (event && typeof event === 'object') onProgress?.(event);
      },
    });
  } catch (error) {
    // The offline APK bundles Qwen3 only; do not attempt to load an absent remote fallback.
    if (IS_NATIVE_ANDROID) throw error;
    onProgress?.({
      status: 'fallback',
      message: 'Qwen3 no está disponible en este dispositivo; probando Qwen2.5-0.5B.',
    });
    // El fallback mantiene operativas las instalaciones que aún no tengan los pesos Qwen3.
    return pipeline('text-generation', FALLBACK_MODEL_ID, {
      device,
      dtype: hasWebGPU ? 'q4f16' : 'q4',
      progress_callback: (event) => {
        if (event && typeof event === 'object') onProgress?.(event);
      },
    });
  }
}

export async function loadLocalModel({ loader, onProgress } = {}) {
  const defaultLoader = IS_NATIVE_ANDROID
    ? () => import('./vendor/transformers.js')
    : () => import(TRANSFORMERS_CDN);
  if (!pipelinePromise) {
    pipelinePromise = createPipeline({ loader: loader ?? defaultLoader, onProgress }).catch((error) => {
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
