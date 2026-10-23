import { mkdir, rename, stat } from 'node:fs/promises';
import { createWriteStream } from 'node:fs';
import { dirname, join } from 'node:path';
import { pipeline } from 'node:stream/promises';

const ROOT = new URL('../www/models/', import.meta.url);
const FILES = [
  'config.json',
  'generation_config.json',
  'tokenizer.json',
  'tokenizer_config.json',
  'special_tokens_map.json',
  'added_tokens.json',
  'merges.txt',
  'vocab.json',
  'chat_template.jinja',
];
export const MODEL_BUNDLE = Object.freeze([
  Object.freeze({ id: 'onnx-community/Qwen3-0.6B-ONNX', dtype: 'q4', files: [...FILES, 'onnx/model_q4.onnx'] }),
  Object.freeze({ id: 'onnx-community/Qwen2.5-Coder-0.5B-Instruct', dtype: 'q4', files: [...FILES, 'onnx/model_q4.onnx'] }),
]);

async function downloadFile(model, file) {
  const relative = join(model.id, file);
  const target = new URL(relative.split('\\').join('/'), ROOT);
  const finalPath = target.pathname;
  try {
    const existing = await stat(finalPath);
    if (existing.size > 0) {
      console.log('✓ ya existe', relative, `(${(existing.size / 1024 / 1024).toFixed(0)} MB)`);
      return;
    }
  } catch {}
  const url = `https://huggingface.co/${model.id}/resolve/main/${file}?download=true`;
  await mkdir(dirname(finalPath), { recursive: true });
  const tempPath = finalPath + '.partial';
  console.log('↓', relative);
  const response = await fetch(url, { redirect: 'follow' });
  if (!response.ok || !response.body) throw new Error(`Descarga fallida (${response.status}): ${url}`);
  const expected = Number(response.headers.get('content-length') || 0);
  let received = 0;
  const meter = new TransformStream({
    transform(chunk, controller) { received += chunk.byteLength; controller.enqueue(chunk); },
    flush() {
      if (expected && received !== expected) throw new Error(`Descarga incompleta: ${relative} (${received}/${expected})`);
    },
  });
  try {
    await pipeline(response.body, meter, createWriteStream(tempPath));
    if (received === 0) throw new Error(`Archivo vacío: ${relative}`);
    await rename(tempPath, finalPath);
    console.log('✓', relative, `(${(received / 1024 / 1024).toFixed(0)} MB)`);
  } catch (error) {
    const { unlink } = await import('node:fs/promises');
    await unlink(tempPath).catch(() => {});
    throw error;
  }
}

async function main() {
  if (process.argv.includes('--list')) {
    for (const model of MODEL_BUNDLE) console.log(`${model.id} · ${model.dtype} · ${model.files.join(', ')}`);
    return;
  }
  console.log('Preparando modelos locales para empaquetarlos dentro de la APK.');
  console.log('Se descargan únicamente los pesos q4 y los archivos de configuración/tokenizador necesarios.');
  console.log('La descarga inicial requiere conexión y puede ocupar aproximadamente 1.8 GB.');
  for (const model of MODEL_BUNDLE) {
    for (const file of model.files) await downloadFile(model, file);
  }
  console.log('Modelos preparados en www/models/. Ejecuta ahora la sincronización/build de Android.');
}

if (process.argv[1] && new URL(`file://${process.argv[1]}`).href === import.meta.url) {
  main().catch(error => { console.error(error); process.exitCode = 1; });
}
