// Catálogo de expertos RONIN-IA. Los candidatos no se cargan automáticamente.
// Mantener expertos remotos desactivados evita descargas grandes y costes de datos sorpresa.
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
    source: 'huggingface',
    status: 'candidate',
    // El archivo ONNX q4f16 publicado ronda los 555 MB; q4 ronda los 862 MB.
    // El tamaño final depende del backend y la cuantización seleccionada.
    estimatedDownloadMB: 555,
    requiresExplicitOptIn: true,
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
 * Un experto candidato solo se selecciona cuando el usuario lo ha habilitado.
 * La carga real y su comprobación de caché se gestionan en la capa de runtime.
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
