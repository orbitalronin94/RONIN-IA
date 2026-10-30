// Pruebas de contrato estáticas para las garantías críticas del frontend.
// No simulan WebGPU ni Android real: comprueban que las protecciones básicas no desaparezcan por accidente.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../www/index.html', import.meta.url), 'utf8');
const script = html.match(/<script type="module">([\s\S]*?)<\/script>/)?.[1] ?? '';

test('la app tiene un único módulo principal y puede validarse en CI', () => {
  assert.ok(script.length > 1000, 'debe existir el módulo de la app');
  assert.match(html, /<html lang="es">/);
});

test('el envío no referencia un control inexistente antes de enviar el prompt', () => {
  assert.match(script, /function busyState\(v\)\{busy=v;el\.input\.disabled=v;el\.send\.disabled=v\|\|!el\.input\.value\.trim\(\);if\(!v\)el\.input\.focus\(\)\}/);
  assert.doesNotMatch(script, /el\.load\.disabled/);
});

test('la app no incluye runtime ni pesos de modelos locales', () => {
  assert.doesNotMatch(script, /transformers\.js|loadModel\(|getPipelineForRequest|Qwen3-0\.6B-ONNX/);
  assert.doesNotMatch(html, /Probar IA local|Qwen3 local/);
});

test('el modo seleccionado enruta al motor local o remoto', () => {
  assert.match(html, /LLMFaucet · sin clave personal/);
  assert.match(html, /No envíes contraseñas ni datos sensibles/);
  assert.match(script, /localMode \? requestLocalCompletion\(\{messages\}\) : requestRemoteCompletion\(\{messages\}\)/);
  assert.match(script, /import \{ requestLocalCompletion \} from '\.\/local-ai\.js'/);
  assert.match(script, /Si es la primera ejecución, comprueba la conexión para descargar el runtime y los pesos/);
});

test('no se usa eval y la entrada del usuario tiene un límite', () => {
  const executableScript = script.replace(/^\s*\/\/.*$/gm, '');
  assert.doesNotMatch(executableScript, /\beval\s*\(/);
  assert.match(html, /maxlength="12000"/);
});

test('los enlaces Markdown se limitan a HTTP(S) y abren con protección noopener', () => {
  assert.match(script, /https\?:\\\/\\\//);
  assert.match(script, /rel="noopener noreferrer"/);
});

test('el historial local tolera errores de almacenamiento', () => {
  assert.match(script, /function readSessions\(\)\{try\{/);
  assert.match(script, /function persist\(\)\{try\{/);
});

test('los controles principales conservan etiquetas accesibles y foco visible', () => {
  assert.match(html, /aria-label="Mensaje para Ronin IA"/);
  assert.match(html, /aria-label="Enviar mensaje"/);
  assert.match(html, /aria-label="Abrir menú"/);
  assert.match(html, /button:focus-visible/);
  assert.match(html, /prefers-reduced-motion:reduce/);
});

test('la salida del modelo pasa por el renderizador Markdown y el escape HTML', () => {
  assert.match(script, /function escapeHtml\(/);
  assert.match(script, /function markdown\(/);
  assert.match(script, /m\.role==='user'\?escapeHtml\(m\.content\).*?:markdown\(m\.content\)/);
});


test('los adjuntos admiten formatos documentales con límites y extracción local', () => {
  assert.match(html, /id="fileInput" type="file" multiple/);
  assert.match(script, /MAX_FILE_BYTES=5\*1024\*1024/);
  assert.match(script, /MAX_FILES=5/);
  assert.match(script, /MAX_EXTRACTED_CHARS=18000/);
  assert.match(script, /async function extractFile\(file\)/);
  assert.match(script, /pdfjs-dist/);
  assert.match(script, /mammoth/);
  assert.match(script, /Analiza los siguientes archivos adjuntos/);
});

test('el dictado de voz usa SpeechRecognition de forma opcional y explica incompatibilidad', () => {
  assert.match(html, /id="voiceBtn"/);
  assert.match(script, /window\.SpeechRecognition\|\|window\.webkitSpeechRecognition/);
  assert.match(script, /El dictado por voz no está disponible/);
  assert.match(script, /recognition\.lang='es-ES'/);
});


test('la compilación declara permisos Android de red antes de generar la APK', () => {
  const workflow = readFileSync(new URL('../.github/workflows/build-android.yml', import.meta.url), 'utf8');
  assert.match(workflow, /Ensure Android network permissions/);
  assert.match(workflow, /android\.permission\.INTERNET/);
  assert.match(workflow, /android\.permission\.ACCESS_NETWORK_STATE/);
  assert.match(workflow, /android\/app\/src\/main\/AndroidManifest\.xml/);
});

test('la UI explica la naturaleza experimental de la IA remota', () => {
  assert.match(html, /IA remota experimental/);
  assert.doesNotMatch(html, /cambiar a Qwen3 local|Probar IA local/);
});

test('la compilación no descarga ni empaqueta modelos locales', () => {
  const workflow = readFileSync(new URL('../.github/workflows/build-android.yml', import.meta.url), 'utf8');
  assert.doesNotMatch(workflow, /Bundle local inference runtime|Download all bundled model weights|npm run prepare:models|@huggingface\/transformers\/src\/transformers\.js/);
  assert.match(workflow, /Generate Android launcher icon from Ronin logo/);
  assert.match(workflow, /Verify APK size and fingerprint/);
  assert.match(workflow, /APK_MIB=/);
  assert.match(workflow, /La APK aún contiene pesos ONNX locales/);
  assert.doesNotMatch(script, /transformers\.js|allowLocalModels|localModelPath/);
});


test('la APK offline empaqueta Qwen3 DQ-ONNX y runtime local sin cambiar el build ligero', () => {
  const localAI = readFileSync(new URL('../www/local-ai.js', import.meta.url), 'utf8');
  const offlineBuild = readFileSync(new URL('../.github/workflows/build-offline-apk.yml', import.meta.url), 'utf8');
  const modelPrep = readFileSync(new URL('../scripts/prepare-offline-model.mjs', import.meta.url), 'utf8');
  const runtimeBundle = readFileSync(new URL('../scripts/bundle-offline-runtime.mjs', import.meta.url), 'utf8');
  const marker = readFileSync(new URL('../www/offline-build.js', import.meta.url), 'utf8');
  assert.ok(localAI.includes('onnx-community/Qwen3-0.6B-DQ-ONNX'));
  assert.ok(localAI.includes('onnx-community/Qwen2.5-0.5B-Instruct'), 'Qwen2.5 se conserva como fallback del navegador');
  assert.ok(localAI.includes('env.allowRemoteModels = !IS_NATIVE_ANDROID'));
  assert.ok(localAI.includes("import('./vendor/transformers.js')"));
  assert.ok(localAI.includes("env.backends.onnx.wasm.wasmPaths = './vendor/'"));
  assert.ok(offlineBuild.includes('workflow_dispatch'));
  assert.ok(offlineBuild.includes('RONIN_MODEL_REVISION'));
  assert.ok(offlineBuild.includes('ronin-ia-qwen3-dq-offline-debug-apk'));
  assert.match(offlineBuild, /-Dorg\.gradle\.jvmargs=.*-Xmx4g/, 'la APK offline necesita más heap para comprimir los assets grandes');
  assert.ok(modelPrep.includes('onnx/model_q4f16.onnx'));
  assert.ok(modelPrep.includes('resolved_revision'));
  assert.ok(modelPrep.includes('sha256'));
  assert.ok(runtimeBundle.includes('onnxruntime-web'));
  assert.ok(runtimeBundle.includes("@huggingface/transformers';"), 'debe resolver el entrypoint del paquete, no su src interno');
  assert.ok(runtimeBundle.includes("conditions: ['browser']"));
  assert.ok(runtimeBundle.includes("mainFields: ['browser', 'module', 'main']"));
  assert.ok(runtimeBundle.includes("await rm(entry, { force: true })"), 'el entry temporal debe limpiarse incluso si falla el bundle');
  assert.match(marker, /OFFLINE_BUNDLE_ENABLED = (?:true|false)/, 'el marcador debe exportar un booleano; CI lo cambia a true solo para la APK offline');
});
