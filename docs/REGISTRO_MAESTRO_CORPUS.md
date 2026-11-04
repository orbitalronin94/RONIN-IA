# Registro maestro de corpus y modelos de RONIN

Actualizado: 4 de noviembre de 2026. Este registro distingue datos de entrenamiento general, material auxiliar, evaluación y modelos tutores. «Descargado y con SHA-256 verificado» no significa automáticamente «aprobado para entrenamiento».

## Fuentes que entran en el preentrenamiento general

| Fuente | Evidencia disponible | Uso en el ciclo mixto |
|---|---|---|
| `orbitalronin94/Portfolio/Papers` | Permiso expreso del titular; commit `fffc234fdf3f82b6a90d56ae9b190d1c0de79690`; 48 documentos incorporados, 1 excluido; corpus SHA-256 `c03a5a2045e74edd5a3c7ff16af607f887a77204862db2be1de56a922ca2f8d0`. Artefacto de preparación de Actions: run `41824304632`, artifact `13318098610`. | **Train**. No se crean holdouts a partir de los documentos del autor. |
| CLiGS Textbox | Commit `1b91e940475c8a7e866457a3953fed5edb0a29f1`; 364 documentos preparados. | Solo **train**. |
| CoNSSA | Commit `8fccf669ed1bdbad309ff190f5afb0d6066d70a3`; 184 documentos preparados. | Solo **train**. |
| ELTeC-spa | Commit `83e2a22d5ef66f96e59f47f7ef810358c4236322`; 96 documentos preparados. | Solo **train**. |

La adquisición consolidada del 4 de noviembre produjo **644 documentos**: 608 train, 18 validation y 18 test; 40 archivos o fragmentos fueron excluidos. El SHA-256 de `train.txt` es `9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78`. Los splits se agrupan por obra/archivo para evitar fugas. Artefactos de adquisición: run `41801074425`, artifacts `13307622094` y `13306714074`.

## Material propio y auxiliar que no se mezcla con el preentrenamiento general

| Material | Estado verificado | Política |
|---|---|---|
| Corpus sintético de pseudo-palabras (`ronin-synthetic-pseudowords-v1`) | Generador determinista y pruebas automatizadas; no representa español ni conocimiento. | Solo smoke del pipeline. Excluido del entrenamiento de conocimiento. |
| Biblioteca primaria de criptografía | Run `41801074425` descargó cinco fuentes y verificó sus hashes: Poe `c8d5fec0…d587386` (606.476 bytes), Verne `d09edf44…9480b1` (616.734), Doyle `8c4de14b…4d5e5a` (719.650), *Hypnerotomachia* `60b9cfcc…daeb54a` (9.646.209) y Selenus `902fc370…bcb2bfb` (163.115.586). El artefacto `13307877028` conserva los originales y el manifiesto hasta el 11-11-2026. | Material auxiliar de investigación; marcado `excluded_pending_manual_review`. La nueva adquisición incorpora también el PDF de *Steganographia* de Trithemius y verifica su hash en ejecución. |
| Casos estructurados de opacidad | `ronin-obfuscation-patterns-v1`: ejemplos anotados A/B/C/D y 500 controles sintéticos reproducibles; incluye splits propios. | Corpus especializado REF/criptografía, separado del preentrenamiento general. Mantener validation/test fuera de cualquier ajuste. |
| Salidas de Phi-4 | 32 propuestas generadas en el ciclo y filtradas por estructura REF. | Augmentación experimental. La auditoría REF no certifica verdad ni derechos de salida; no publicar ni redistribuir las respuestas. |

## Modelos tutores locales

El workflow de caché verificó satisfactoriamente licencia MIT, revisión inmutable, inventario y hashes de archivos:

- GPT-2: `openai-community/gpt2`, revisión `607a30d783dfa663caf39e06633721c8d4cfcd7e`, 27 archivos.
- GPT-Neo 125M: `EleutherAI/gpt-neo-125m`, revisión `21def0189f5705e2521767faed922f1f15e7d7db`, 30 archivos.
- Phi-4-mini-instruct: `microsoft/Phi-4-mini-instruct`, revisión `cfbefacb99257ffa30c83adab238a50856ac3083`, 54 archivos.

Run de caché: `41824304651`. Phi-4 es el tutor principal para esta prueba; los pesos del tutor nunca se importan a RONIN. La licencia del modelo no se atribuye automáticamente a su texto generado.

## Evaluación: nunca usar como gradientes

- `benchmarks/domains_v1.jsonl`: piloto multidominio, 23 preguntas y 15 dominios.
- MMLU-Pro `test`, revisión `b189ec765aa7ed75c8acfea42df31fdae71f97be`.
- Los splits validation/test de CLiGS, CoNSSA y ELTeC-spa.
- El split test del conjunto estructurado de opacidad.

## Candidatos que siguen fuera

- Project Gutenberg como colección, Internet Archive como colección, PleIAs Common Corpus y BookCorpusOpen permanecen sujetos a G-0/revisión por obra. La autorización de uso de tres obras concretas de Gutenberg en la biblioteca criptográfica no autoriza el catálogo general.
- PleIAs Spanish Public Domain Books: PR #13 sigue abierta; no se considera descargado ni admitido.
- Prensa histórica, BNE, BOE, Common Voice, Wikipedia y otros candidatos documentados en `FUENTES_CORPUS_ABIERTOS.md` no se incorporan hasta completar su auditoría individual.

## Regla de mezcla

El ciclo actual concatena Portfolio/Papers, el split train de las tres bibliotecas literarias y las propuestas REF estructuralmente válidas de Phi-4. El manifiesto de mezcla registra bytes, SHA-256 y cuota real por fuente; no se debe confundir presencia en la mezcla con contribución equilibrada. La biblioteca criptográfica y el corpus sintético se registran como auxiliares y no se introducen en ese preentrenamiento. MMLU-Pro, benchmarks y holdouts nunca entran en gradientes.
