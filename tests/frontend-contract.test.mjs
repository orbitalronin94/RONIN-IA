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

test('la ruta de modelo local utiliza caché y mantiene fallback CPU', () => {
  assert.match(script, /useBrowserCache\s*=\s*true/);
  assert.match(script, /device:\s*'webgpu'/);
  assert.match(script, /cpuDtype/);
  assert.match(script, /performance\.now\(\)-startedAt/);
});

test('la APK Android prepara el modelo al iniciar y la bienvenida explica la descarga inicial', () => {
  assert.match(html, /En Android, Ronin prepara la IA al abrirse/);
  assert.match(html, /lleva los pesos del modelo dentro de la APK/);
  assert.match(script, /window\.Capacitor\?\.getPlatform\?\.\(\)==='android'/);
  assert.match(script, /if\(isNativeAndroid\).*?loadModel\(\)\.catch/s);
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

test('la UI aclara que Android no muestra un diálogo para el permiso normal de internet', () => {
  assert.match(html, /Modelo local no cargado/);
  assert.match(script, /Preparando IA al iniciar/);
  assert.match(script, /Comprueba internet y memoria disponible/);
});


test('la compilación descarga y empaqueta los dos expertos ONNX locales', () => {
  const workflow = readFileSync(new URL('../.github/workflows/build-android.yml', import.meta.url), 'utf8');
  assert.match(workflow, /Bundle local inference runtime/);
  assert.match(workflow, /node_modules\/@huggingface\/transformers\/src\/transformers\.js/);
  assert.match(workflow, /Download all bundled model weights/);
  assert.match(workflow, /npm run prepare:models/);
  assert.match(workflow, /Generate Android launcher icon from Ronin logo/);
  const manifest = readFileSync(new URL('../scripts/prepare-models.mjs', import.meta.url), 'utf8');
  assert.match(manifest, /Qwen3-0\.6B-ONNX/);
  assert.match(manifest, /Qwen2\.5-Coder-0\.5B-Instruct/);
  assert.match(manifest, /onnx\/model_q4\.onnx/);
  assert.match(script, /import\('\.\/vendor\/transformers\.js'\)/);
  assert.match(script, /allowLocalModels=isNativeAndroid/);
  assert.match(script, /allowRemoteModels=!isNativeAndroid/);
  assert.match(script, /localModelPath='\.\/models\/'/);
});
