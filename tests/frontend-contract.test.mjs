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
});

test('la APK Android intenta preparar el modelo al iniciar, pero la web no lo descarga automáticamente', () => {
  assert.match(script, /window\.Capacitor\?\.getPlatform\?\.\(\)==='android'/);
  assert.match(script, /if\(isNativeAndroid\).*?loadModel\(\)\.catch/s);
});

test('no se usa eval y la entrada del usuario tiene un límite', () => {
  assert.doesNotMatch(script, /\beval\s*\(/);
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
