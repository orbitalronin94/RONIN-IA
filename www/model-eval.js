import { loadLocalModel, requestLocalCompletion, LOCAL_MODEL_ID } from './local-ai.js';

const runButton = document.querySelector('#run');
const downloadButton = document.querySelector('#download');
const progress = document.querySelector('#progress');
const status = document.querySelector('#status');
const results = document.querySelector('#results');
let predictions = [];

function setStatus(message) { status.textContent = message; }

async function loadDataset() {
  const response = await fetch('../benchmarks/model-eval-prompts.jsonl', { cache: 'no-store' });
  if (!response.ok) throw new Error('No se pudo cargar benchmarks/model-eval-prompts.jsonl. Sirve el repositorio completo desde su raíz.');
  return (await response.text()).split(/\r?\n/).filter(line => line.trim()).map((line, index) => {
    try { return JSON.parse(line); }
    catch { throw new Error('JSONL inválido en la línea ' + (index + 1)); }
  });
}

function downloadJsonl() {
  const text = predictions.map(row => JSON.stringify(row)).join('\n') + '\n';
  const blob = new Blob([text], { type: 'application/x-ndjson;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'ronin-qwen-model-eval-predictions.jsonl';
  link.click();
  URL.revokeObjectURL(url);
}

runButton.addEventListener('click', async () => {
  runButton.disabled = true;
  downloadButton.disabled = true;
  predictions = [];
  progress.value = 0;
  results.textContent = '';
  let backend = typeof navigator !== 'undefined' && navigator.gpu ? 'webgpu_requested' : 'wasm';
  let fallbackUsed = false;
  try {
    const dataset = await loadDataset();
    setStatus('Cargando runtime y pesos del modelo… la primera vez puede tardar varios minutos.');
    const startLoad = performance.now();
    await loadLocalModel({ onProgress(event) {
      if (event?.status === 'fallback') { fallbackUsed = true; backend = 'wasm_fallback'; }
      if (event?.status) setStatus('Preparando modelo: ' + event.status + (event.progress != null ? ' (' + Math.round(event.progress) + '%)' : ''));
    }});
    const startupMs = Math.round(performance.now() - startLoad);
    const quantization = backend === 'wasm' || backend === 'wasm_fallback' ? 'q4' : 'q4f16';
    setStatus('Modelo listo (' + (startupMs / 1000).toFixed(1) + ' s). Ejecutando prompts…');
    for (let i = 0; i < dataset.length; i++) {
      const item = dataset[i];
      const started = performance.now();
      let output = '';
      let error = null;
      try {
        output = await requestLocalCompletion({
          messages: [{ role: 'user', content: item.prompt }],
          generateOptions: { max_new_tokens: 128, do_sample: false },
          onProgress(event) {
            if (event?.status === 'fallback') { fallbackUsed = true; backend = 'wasm_fallback'; }
          },
        });
      } catch (err) {
        error = String(err?.message || err);
        output = '';
      }
      const latencyMs = Math.round(performance.now() - started);
      predictions.push({
        case_id: item.id,
        output,
        latency_ms: latencyMs,
        startup_ms: startupMs,
        model_id: LOCAL_MODEL_ID,
        quantization,
        backend: fallbackUsed ? 'wasm_fallback' : backend,
        error,
      });
      progress.value = i + 1;
      results.textContent += '[' + (i + 1) + '/' + dataset.length + '] ' + item.id + ' · ' + latencyMs + ' ms' + (error ? ' · ERROR: ' + error : '') + '\n' + (output || '(sin respuesta)') + '\n\n';
      setStatus('Caso ' + (i + 1) + ' de ' + dataset.length + ' completado.');
    }
    downloadButton.disabled = false;
    setStatus('Finalizado: ' + predictions.length + ' casos. Inicialización: ' + (startupMs / 1000).toFixed(1) + ' s. Exporta el JSONL para puntuarlo.');
  } catch (err) {
    setStatus('No se pudo completar la evaluación: ' + String(err?.message || err));
  } finally {
    runButton.disabled = false;
  }
});

downloadButton.addEventListener('click', downloadJsonl);
