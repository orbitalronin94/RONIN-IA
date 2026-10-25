// Inferencia local opcional. En la APK offline, runtime, tokenizer y pesos se sirven desde assets empaquetados.
export const LOCAL_MODEL_ID = 'onnx-community/Qwen2.5-0.5B-Instruct';
const TRANSFORMERS_CDN = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.7.2/+esm';
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
  const dtype = IS_NATIVE_ANDROID ? 'q4' : hasWebGPU ? 'q4f16' : 'q4';
  const options = {
    device,
    dtype,
    progress_callback: (event) => {
      if (event && typeof event === 'object') onProgress?.(event);
    },
  };
  try {
    return await pipeline('text-generation', LOCAL_MODEL_ID, options);
  } catch (error) {
    if (!hasWebGPU) throw error;
    onProgress?.({ status: 'fallback', message: 'Aceleración GPU no compatible; usando CPU.' });
    return pipeline('text-generation', LOCAL_MODEL_ID, {
      ...options,
      device: 'wasm',
      dtype: 'q4',
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
