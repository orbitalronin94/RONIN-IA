import { cp, mkdir, readdir, rm, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { build } from 'esbuild';

const root = process.cwd();
const vendor = resolve(root, 'www/vendor');
const entry = resolve(root, '.offline-transformers-entry.mjs');
await mkdir(vendor, { recursive: true });

// Import the package entry point, not src/transformers.js directly. The package
// entry lets esbuild apply the browser export/field mappings that exclude Node-only
// modules such as sharp and onnxruntime-node from the Android WebView bundle.
await writeFile(
  entry,
  "export { env, pipeline } from '@huggingface/transformers';\n",
  'utf8',
);
try {
  await build({
    entryPoints: [entry],
    bundle: true,
    platform: 'browser',
    conditions: ['browser'],
    mainFields: ['browser', 'module', 'main'],
    format: 'esm',
    target: 'es2022',
    outfile: resolve(vendor, 'transformers.js'),
    minify: true,
    sourcemap: false,
    logLevel: 'info',
  });
} finally {
  await rm(entry, { force: true });
}

const candidates = [
  resolve(root, 'node_modules/onnxruntime-web/dist'),
  resolve(root, 'node_modules/@huggingface/transformers/node_modules/onnxruntime-web/dist'),
];
let dist;
for (const candidate of candidates) {
  try {
    const names = await readdir(candidate);
    if (names.some((name) => name.endsWith('.wasm'))) {
      dist = candidate;
      break;
    }
  } catch {}
}
if (!dist) throw new Error('No se encontró onnxruntime-web/dist con archivos WASM.');
const names = await readdir(dist);
const assets = names.filter((name) => /\.(wasm|mjs)$/.test(name));
if (!assets.some((name) => name.endsWith('.wasm'))) {
  throw new Error('El runtime no contiene assets WASM.');
}
for (const name of assets) await cp(resolve(dist, name), resolve(vendor, name));
console.log(`Runtime empaquetado en www/vendor/; copiados ${assets.length} assets WASM/MJS desde ${dist}`);
