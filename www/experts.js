// Catálogo de expertos incluidos en el paquete de modelos de Android.
// Los pesos se descargan durante la preparación del build, no durante el uso de la app.
export const BASE_MODEL = 'onnx-community/Qwen3-0.6B-ONNX';

export const EXPERTS = Object.freeze({
  general: Object.freeze({
    id: 'general-base',
    model: BASE_MODEL,
    source: 'bundled',
    status: 'active',
    estimatedDownloadMB: 0,
  }),
  coding: Object.freeze({
    id: 'qwen25-coder-05b-instruct',
    model: 'onnx-community/Qwen2.5-Coder-0.5B-Instruct',
    source: 'bundled',
    status: 'active',
    estimatedDownloadMB: 0,
  }),
});

const CATEGORY_EXPERT = Object.freeze({
  coding: 'coding',
  math: 'general',
  language: 'general',
  instruction: 'general',
  general: 'general',
});

/**
 * Planifica qué modelo usar sin cargarlo.
 * Todos los modelos del catálogo se incluyen durante la preparación del APK.
 * La carga de inferencia sigue siendo diferida para no ocupar RAM hasta necesitarlos.
 */
export function selectExpert(category, { enabledExperts = [] } = {}) {
  const key = CATEGORY_EXPERT[category] || 'general';
  const candidate = EXPERTS[key];
  const enabled = enabledExperts.includes(key);
  if (candidate.status === 'candidate' && !enabled) {
    return { ...EXPERTS.general, requestedCategory: category, fallback: true };
  }
  return { ...candidate, requestedCategory: category, fallback: false };
}
