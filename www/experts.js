// Routing profiles for the current lightweight remote-inference MVP.
// No model weights are bundled or downloaded by the Android build.
export const BASE_MODEL = 'auto:fast';

export const EXPERTS = Object.freeze({
  general: Object.freeze({
    id: 'general-remote',
    model: 'auto:fast',
    source: 'remote',
    status: 'active',
    estimatedDownloadMB: 0,
  }),
  coding: Object.freeze({
    id: 'coding-remote',
    model: 'auto:coding',
    source: 'remote',
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
 * Selects a prompt-routing profile. This is application-level routing,
 * not a neural MoE and not a registry of locally installed model weights.
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
