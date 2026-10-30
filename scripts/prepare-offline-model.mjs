import { createHash } from 'node:crypto';
import { createWriteStream } from 'node:fs';
import { mkdir, rename, stat, unlink, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { Transform } from 'node:stream';
import { pipeline } from 'node:stream/promises';

// The offline bundle pins the same <400 MB q4f16 artifact used by the runtime candidate.
const MODEL_ID = 'onnx-community/Qwen3-0.6B-DQ-ONNX';
const REQUESTED_REVISION = process.env.RONIN_MODEL_REVISION || 'd6beae7';
const ROOT = resolve('www/models');
const MODEL_DIR = join(ROOT, MODEL_ID);
const REQUIRED = ['config.json', 'tokenizer.json', 'tokenizer_config.json', 'added_tokens.json', 'special_tokens_map.json', 'genai_config.json', 'vocab.json', 'onnx/model_q4f16.onnx', 'onnx/model_q4f16.onnx_data'];
const OPTIONAL = ['generation_config.json', 'special_tokens_map.json', 'added_tokens.json', 'chat_template.jinja'];
const sha256 = createHash;

async function resolveRevision() {
  const response = await fetch(`https://huggingface.co/api/models/${MODEL_ID}/revision/${encodeURIComponent(REQUESTED_REVISION)}`);
  if (!response.ok) throw new Error(`No se pudo resolver la revisión de Hugging Face (${response.status}).`);
  const data = await response.json();
  if (!/^[a-f0-9]{40}$/i.test(data.sha || '')) throw new Error('La API no devolvió un SHA de revisión de 40 caracteres.');
  return data.sha;
}

async function downloadFile(revision, file, optional) {
  const target = join(MODEL_DIR, file);
  try {
    if ((await stat(target)).size > 0) return { path: file, size: (await stat(target)).size, sha256: null, cached: true };
  } catch {}
  const url = `https://huggingface.co/${MODEL_ID}/resolve/${revision}/${file}?download=true`;
  const response = await fetch(url, { redirect: 'follow' });
  if (response.status === 404 && optional) return null;
  if (!response.ok || !response.body) throw new Error(`Descarga fallida (${response.status}) para ${file}`);
  const expected = Number(response.headers.get('content-length') || 0);
  let received = 0;
  const digest = sha256('sha256');
  const meter = new Transform({
    transform(chunk, _encoding, callback) {
      received += chunk.length;
      digest.update(chunk);
      callback(null, chunk);
    },
    flush(callback) {
      if (expected && received !== expected) callback(new Error(`Descarga incompleta de ${file}: ${received}/${expected} bytes`));
      else callback();
    },
  });
  await mkdir(dirname(target), { recursive: true });
  const temp = target + '.partial';
  try {
    await pipeline(response.body, meter, createWriteStream(temp));
    if (!received) throw new Error(`Archivo vacío: ${file}`);
    await rename(temp, target);
    return { path: file, size: received, sha256: digest.digest('hex'), cached: false };
  } catch (error) {
    await unlink(temp).catch(() => {});
    throw error;
  }
}

async function main() {
  const revision = await resolveRevision();
  console.log(`Modelo: ${MODEL_ID}@${revision}`);
  console.log('Cuantización empaquetada: Q4F16 DQ-ONNX; pesos ONNX ~356 MB y repositorio completo ~370 MB.');
  await mkdir(MODEL_DIR, { recursive: true });
  const files = [];
  for (const file of REQUIRED) {
    const result = await downloadFile(revision, file, false);
    files.push(result);
    console.log(`✓ ${file} (${(result.size / 1024 / 1024).toFixed(1)} MiB)`);
  }
  for (const file of OPTIONAL) {
    const result = await downloadFile(revision, file, true);
    if (result) {
      files.push(result);
      console.log(`✓ ${file}`);
    } else {
      console.log(`· ${file} no está publicado; se omite`);
    }
  }
  const manifest = {
    model_id: MODEL_ID,
    resolved_revision: revision,
    requested_revision: REQUESTED_REVISION,
    dtype: 'q4f16',
    generated_at: new Date().toISOString(),
    files: files.map(({ path, size, sha256: hash, cached }) => ({ path, size_bytes: size, sha256: hash, sha256_reused_from_cache: cached })),
    note: 'El hash es null cuando el archivo ya existía en el workspace; en CI limpio no debería ocurrir.',
  };
  await writeFile(join(MODEL_DIR, 'ronin-bundle-manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  console.log('Manifiesto escrito. El workflow empaquetará estos archivos en una APK de debug.');
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
