import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { pipeline, env } from '@huggingface/transformers';

const args = process.argv.slice(2);
const modelId = args[0], revision = args[1], datasetPath = args[2], predictionsPath = args[3];
if (!modelId || !revision || !datasetPath || !predictionsPath) {
  throw new Error('Usage: node scripts/run_onnx_model_eval.mjs MODEL_ID REVISION DATASET PREDICTIONS');
}
const dtype = 'q4f16';
const cacheDir = path.resolve(process.env.MODEL_CACHE_DIR || '.cache/onnx-models');
await fs.mkdir(cacheDir, { recursive: true });
env.allowRemoteModels = true;
env.allowLocalModels = true;
env.useBrowserCache = false;
env.cacheDir = cacheDir;

async function filesUnder(directory) {
  const rows = [];
  async function walk(current) {
    for (const entry of await fs.readdir(current, { withFileTypes: true })) {
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) await walk(full);
      else if (entry.isFile() || entry.isSymbolicLink()) {
        const stat = await fs.stat(full);
        if (stat.isFile()) rows.push({ path: path.relative(directory, full), bytes: stat.size });
      }
    }
  }
  await walk(directory);
  return rows;
}
function finalAnswer(value) {
  let text = Array.isArray(value)
    ? String(value.filter(item => item?.role === 'assistant').at(-1)?.content ?? '')
    : String(value ?? '');
  const endThink = text.lastIndexOf('</think>');
  if (endThink >= 0) text = text.slice(endThink + '</think>'.length);
  return text.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
}

const datasetBytes = await fs.readFile(datasetPath);
const dataset = datasetBytes.toString('utf8').split(/\r?\n/).filter(Boolean).map(line => JSON.parse(line));
const started = performance.now();
const generator = await pipeline('text-generation', modelId, { device: 'cpu', dtype, revision });
const startupMs = Math.round((performance.now() - started) * 100) / 100;
const cachedFiles = await filesUnder(cacheDir);
const artifactBytes = cachedFiles.reduce((sum, file) => sum + file.bytes, 0);
if (artifactBytes <= 0) throw new Error("Model cache is empty; exact artifact size cannot be measured.");
const predictions = [];
let peakRssBytes = process.memoryUsage().rss;

for (let index = 0; index < dataset.length; index++) {
  const item = dataset[index];
  const caseStart = performance.now();
  const result = await generator([{ role: 'user', content: item.prompt }], {
    max_new_tokens: 192,
    do_sample: modelId.includes('Qwen3'),
    temperature: 0.6,
    top_p: 0.95,
    top_k: 20,
    seed: 42,
    return_full_text: false,
  });
  const output = finalAnswer(result?.[0]?.generated_text);
  const latencyMs = Math.round((performance.now() - caseStart) * 100) / 100;
  const encodedTokens = generator.tokenizer?.encode?.(output) ?? [];
  peakRssBytes = Math.max(peakRssBytes, process.memoryUsage().rss);
  predictions.push({
    case_id: item.id,
    output,
    latency_ms: latencyMs,
    startup_ms: index === 0 ? startupMs : 0,
    model_id: modelId,
    model_revision: revision,
    quantization: dtype,
    backend: 'transformers_js_onnx_wasm_cpu',
    thinking_mode: modelId.includes('Qwen3') ? 'template_default_enabled' : 'not_applicable',
    generated_tokens: Array.isArray(encodedTokens) ? encodedTokens.length : null,
  });
  console.log('[' + (index + 1) + '/' + dataset.length + '] ' + item.id + ': ' + latencyMs.toFixed(1) + ' ms');
}

await fs.mkdir(path.dirname(path.resolve(predictionsPath)), { recursive: true });
await fs.writeFile(predictionsPath, predictions.map(row => JSON.stringify(row)).join('\n') + '\n');
const metadata = {
  schema_version: 1,
  model_id: modelId,
  model_revision: revision,
  quantization: dtype,
  backend: 'Transformers.js / ONNX Runtime Node CPU',
  dataset_sha256: crypto.createHash('sha256').update(datasetBytes).digest('hex'),
  dataset_cases: dataset.length,
  artifact_bytes: artifactBytes,
  artifact_mb_decimal: Math.round(artifactBytes / 1e6 * 100) / 100,
  model_cache_files: cachedFiles,
  cold_start_ms: startupMs,
  peak_rss_mb: Math.round(peakRssBytes / 1e6 * 100) / 100,
  median_case_latency_ms: predictions.map(row => row.latency_ms).sort((a, b) => a - b)[Math.floor(predictions.length / 2)],
  thinking_mode: modelId.includes('Qwen3') ? 'template_default_enabled' : 'not_applicable',
  limitations: [
    'Node CPU runner measurement is not a browser WASM/WebGPU or physical Android measurement.',
    'Peak RSS includes Node, tokenizer, runtime and model; it is not isolated model memory.',
    'Artifact bytes count files present in this job cache after loading this model.',
    'Qwen3 uses sampling settings recommended for thinking mode; seed support may vary by runtime version.',
  ],
};
await fs.writeFile(predictionsPath + '.metadata.json', JSON.stringify(metadata, null, 2) + '\n');
console.log(JSON.stringify({
  model_id: modelId,
  artifact_mb_decimal: metadata.artifact_mb_decimal,
  cold_start_ms: startupMs,
  peak_rss_mb: metadata.peak_rss_mb,
}));
