# Procedencia del corpus por checkpoint

## Regla de atribución

Un checkpoint solo puede atribuirse a las particiones train que el run realmente verificó y ensambló. La presencia posterior de una fuente en data/datasets/ no cambia la historia de un checkpoint anterior.

## Mapa de checkpoints

| Checkpoint / etapa | Corpus declarado | Documentos | Bytes | Observaciones |
|---|---|---:|---:|---|
| Main tiny seed95, 100 pasos | Mezcla nativa declarada en weights/main-model.json | 286.468 | 684.738.932 | Manifiesto main; no inferir fuentes posteriores |
| Ganador 10k, seed95 | Corpus ensamblado por run 42181780771 | 279.352 unidades train-scoped | 256.612.919 | BPB y full test MMLU-Pro citados en README pertenecen a esta etapa |
| Drosophila, tras expansión y continuación | Literatura, Mathlib4, NASA file-reviewed, Papers propios, ScienceVerse y CoVoST 2 translation-only | 286.468 | 685.023.414 | Run 42198068241; validation/test fuera de gradientes |

Las cifras main y Drosophila proceden de manifiestos/cortes distintos. No se sustituyen unas por otras ni se presentan como una serie homogénea.

## Mezcla Drosophila

El workflow [expand-10x-from-10k.yml](../.github/workflows/expand-10x-from-10k.yml) descarga y verifica seis particiones train scoped:

| Fuente | Documentos train declarados | Alcance |
|---|---:|---|
| Literatura española | 608 | Train scoped |
| Lean mathlib4 | 8.498 | Train scoped |
| NASA file-reviewed | 6 | Revisión individual; subconjunto NASA |
| Papers propios | 9 | Autorización interna del propietario |
| ScienceVerse | 7.103 | CC BY/CC0 por DOI, train scoped |
| CoVoST 2 translation-only | 270.244 | CC0-1.0; solo campo de traducción |

**Suma declarada: 286.468 documentos/segmentos.** La cifra suma particiones reportadas por el workflow; no implica que todas tengan la misma unidad documental ni el mismo tamaño medio.

Los manifiestos de fuente conservan derechos, hashes y particiones. La admisión es scoped. G-0 global sigue FAIL; near-duplicates globales y contaminación de benchmark/holdout siguen pendientes. No describir esta mezcla como corpus globalmente certificado.

## Tokens y bytes

El tokenizador byte-v1 codifica texto UTF-8 por bytes. El corpus declarado tiene 685.023.414 bytes, pero el entrenador Drosophila no recorre una época secuencial: codifica el archivo y muestrea ventanas aleatorias de 128 tokens con reemplazo. En 500 pasos, batch 1 y sin acumulación, el presupuesto nominal de la continuación es 64.000 posiciones de entrada.

Por ello:
- 685 MB describen el tamaño del pool de datos, no los tokens vistos por el optimizador.
- 64.000 es exposición nominal de la continuación, no un recuento de tokens únicos.
- No se suman tokens de la etapa de 10.000 pasos porque su recuento procesado no está declarado en el manifiesto Drosophila.
- Validation y test no entraron en los gradientes del experimento de expansión.

## Manifiestos y auditorías

Los manifiestos y revisiones de cada fuente se mantienen en [data/datasets/README.md](../data/datasets/README.md). El workflow Drosophila genera reports/six-source-mixture.json, con bytes y SHA-256 por fuente, además del hash del corpus concatenado. Ese informe debe conservarse junto al artefacto del run para reproducir el corpus a nivel de bytes.
