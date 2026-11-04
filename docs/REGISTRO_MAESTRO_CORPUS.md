# Registro maestro de corpus y modelos de RONIN

Actualizado: 4 de noviembre de 2026. Se distingue entre material de preentrenamiento general, corpus auxiliar, evaluación y modelos tutores. Una descarga con hash verificado no queda automáticamente aprobada para entrenamiento.

## Preentrenamiento general del ciclo mixto

| Fuente | Evidencia y volumen | Uso |
|---|---|---|
| `orbitalronin94/Portfolio/Papers` | Permiso expreso del titular; commit `fffc234fdf3f82b6a90d56ae9b190d1c0de79690`; 48 documentos incorporados, 1 excluido; SHA-256 del corpus `c03a5a2045e74edd5a3c7ff16af607f887a77204862db2be1de56a922ca2f8d0`. Preparación: run `41824304632`, artifact `13318098610`. | Solo train; no se derivan validation/test de los documentos del autor. |
| CLiGS Textbox | Commit `1b91e940475c8a7e866457a3953fed5edb0a29f1`; 364 documentos preparados. | Solo train. |
| CoNSSA | Commit `8fccf669ed1bdbad309ff190f5afb0d6066d70a3`; 184 documentos preparados. | Solo train. |
| ELTeC-spa | Commit `83e2a22d5ef66f96e59f47f7ef810358c4236322`; 96 documentos preparados. | Solo train. |

La adquisición del run `41825919840` verificó **644 documentos**: 608 train, 18 validation y 18 test; 40 archivos/fragmentos excluidos. SHA-256 de `train.txt`: `9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78`. Los splits se agrupan por obra/archivo para evitar fugas. Artefactos: manifiesto `13319800565`; particiones `13319630770`.

## Corpus propios y material auxiliar

| Material | Estado | Política |
|---|---|---|
| Corpus sintético de pseudo-palabras (`ronin-synthetic-pseudowords-v1`) | Generador determinista y pruebas automatizadas; el workflow lo vuelve a generar con semilla fija. | Smoke del pipeline. Excluido del entrenamiento de conocimiento: no es español ni aporta conocimiento. |
| Biblioteca primaria de criptografía | Run `41825919840` descargó y verificó seis fuentes: Poe (606.476 bytes, `c8d5fec040f1dc29be8d4e9cb7d3279b65bf894adea50544d99d400b2d587386`); Verne (616.734, `d09edf443ee49f78c336a6637b0445d8fadb9ce6806bdebf96cc04fc789480b1`); Doyle (719.650, `8c4de14b3a1952417eca4673fcb1b8aa8f946f8a4164f10ec761368af34d5e5a`); *Hypnerotomachia* (9.646.209, `60b9cfcc5155004237a7e9fe0a3d8b24f7a23da61e8f0392f2b0ca75adaeb54a`); *Steganographia* de Trithemius (61.922.102, `4c2f0adddedc3f3ef5b00357b24b0115a47ba1e2b4bbdca18852ffa034d670de`); Selenus (163.115.586, `902fc370124c3c2867c4f562c399cf9fd4dba4c712df0bf37a7184c29bcb2bfb`). | Material auxiliar; las seis fuentes se mantienen `excluded_pending_manual_review`. No se mezclan en el preentrenamiento general hasta completar OCR/transcripción, revisión de derechos y aprobación documental. |
| Casos estructurados de opacidad (`ronin-obfuscation-patterns-v1`) | 506 registros validados: 3 A, 500 B (controles sintéticos), 2 C y 1 D. Splits: 404 train, 50 validation y 52 test. SHA-256 `674a3c3eae681dc0d134569321b10019423b1ab68554cbc889bdf1695134c72c`. | Corpus especializado REF/criptografía; separado del preentrenamiento general. No reutilizar validation/test para ajustar. Artefacto `13318404267`. |
| Salidas de Phi-4 | El ciclo genera 16 propuestas y las filtra por estructura REF; el resultado del entrenamiento actual aún está pendiente. | Augmentación experimental opcional. REF no certifica verdad ni derechos de salida; no publicar ni redistribuir las respuestas. |

## Modelos tutores locales

El run de caché `41824304651` verificó licencia MIT declarada, revisión inmutable, inventario y hashes:

- GPT-2: `openai-community/gpt2`, revisión `607a30d783dfa663caf39e06633721c8d4cfcd7e`, 27 archivos.
- GPT-Neo 125M: `EleutherAI/gpt-neo-125m`, revisión `21def0189f5705e2521767faed922f1f15e7d7db`, 30 archivos.
- Phi-4-mini-instruct: `microsoft/Phi-4-mini-instruct`, revisión `cfbefacb99257ffa30c83adab238a50856ac3083`, 54 archivos.

Phi-4 es el tutor principal de esta prueba. RONIN parte de inicialización aleatoria: los pesos del tutor no se importan. La licencia MIT del modelo no se atribuye automáticamente al texto generado.

## Evaluación: nunca usar como gradientes

- `benchmarks/domains_v1.jsonl`: piloto interno de 23 preguntas y 15 dominios.
- MMLU-Pro `test`, revisión `b189ec765aa7ed75c8acfea42df31fdae71f97be`.
- Los splits validation/test de CLiGS, CoNSSA y ELTeC-spa.
- El split test del conjunto de opacidad.

## Candidatos que siguen fuera

- Project Gutenberg como colección, Internet Archive como colección, PleIAs Common Corpus y BookCorpusOpen permanecen sujetos a G-0/revisión por obra. Las seis obras concretas de la biblioteca criptográfica no autorizan el catálogo general de Gutenberg.
- PleIAs Spanish Public Domain Books: PR #13 sigue abierta; no se considera descargado ni admitido.
- Prensa histórica, BNE, BOE, Common Voice, Wikipedia y otros candidatos documentados en `FUENTES_CORPUS_ABIERTOS.md` no se incorporan hasta completar su auditoría individual.

## Regla de mezcla

El ciclo actual concatena Portfolio/Papers, el split train de CLiGS/CoNSSA/ELTeC-spa y, si la generación pasa la auditoría REF estructural, el texto de tutor Phi-4. El manifiesto registra bytes, SHA-256 y cuota real por fuente; presencia en la mezcla no implica equilibrio de contribuciones. La biblioteca criptográfica y el corpus sintético se registran como auxiliares y no se introducen en ese preentrenamiento. MMLU-Pro, benchmarks y holdouts permanecen fuera de los gradientes.
