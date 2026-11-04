# Benchmark externo y workflow oficial de RONIN

## Holdout principal: MMLU-Pro completo

El workflow oficial es [Experimento oficial RONIN desde cero + MMLU-Pro completo](../.github/workflows/ronin-official-training-holdout.yml). Se ejecuta al cambiar componentes críticos en `main` y también manualmente desde GitHub Actions.

- Dataset: [TIGER-Lab/MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro).
- Revisión fijada: `b189ec765aa7ed75c8acfea42df31fdae71f97be`.
- Split: `test`, externo al entrenamiento.
- Tamaño esperado del test completo: **12.032 preguntas**.
- Cobertura: multidominio, con desglose por categoría.
- Muestreo: test completo por defecto (`mmlu_limit=0)); en smoke/ejecuciones parciales se permite una muestra estratificada reproducible.
- Contexto de evaluación: 2.048 bytes. No se truncan preguntas: las que exceden el contexto se contabilizan como omitidas y reducen la cobertura.

MMLU-Pro es exigente y multidominio, pero el protocolo de RONIN no es el protocolo oficial del benchmark: se puntúa la probabilidad del siguiente byte de la letra de respuesta (A–J), sin CoT ni ejemplos. **No comparar esta puntuación con el leaderboard oficial de MMLU-Pro.** El informe debe incluir tamaño seleccionado, evaluado, cobertura, omisiones, exactitud global y desglose por dominio.

El test no se usa para gradientes, selección de corpus, ajuste de prompts, selección de tutores ni decisiones iterativas de hiperparámetros. Se ejecuta una evaluación inicial y otra final sobre los mismos ítems para estimar el cambio asociado al ciclo; los resultados se interpretan como exploratorios.

## Corpus de entrenamiento admitido

La mezcla de entrenamiento se construye desde cero con:

1. Portfolio/Papers autorizado, 48 documentos utilizables, solo train.
2. CLiGS Textbox, CoNSSA y ELTeC-spa, usando únicamente los 608 documentos de train.

Se excluyen de esta prueba:
- Los 18 documentos de validation y los 18 de test literarios.
- La biblioteca de criptografía/opacidad (506 casos) hasta terminar revisión manual de derechos, OCR, edición y evidencia.
- Los pseudodatos sintéticos, que solo sirven para smoke técnico.
- Las salidas de tutores, incluida Phi-4, hasta que superen revisión humana de calidad y derechos. Los pesos de los tutores nunca se importan al estudiante.

El modelo estudiante se inicializa aleatoriamente. El primer experimento usa el perfil `tiny` (aprox. 9,9 M de parámetros), 1.000 pasos y una semilla (1337) para controlar el coste del test completo. Los checkpoints son temporales y no se publican; el artefacto de Actions contiene informes y manifiestos, no los corpus ni los pesos.

## Métricas y reproducibilidad

Cada ejecución registra:
- Revisión del dataset y SHA-256 de sus filas normalizadas.
- SHA-256 de cada entrada de entrenamiento, de la mezcla y del checkpoint.
- Semilla, pasos, configuración, versiones de Python/dependencias y particiones.
- Exactitud inicial/final, cobertura y desglose por dominio.
- Interpretación y limitaciones del protocolo.

La evaluación de siguiente byte es una aproximación austera compatible con el tokenizador byte-level de RONIN. No equivale a generación de respuestas, razonamiento abierto, calibración ni calidad de explicación. Para afirmar competencia general harán falta más semillas, un modelo mayor, benchmarks adicionales independientes, pruebas abiertas con rúbricas humanas y análisis de incertidumbre.

## Ejecución

- [Workflow oficial](https://github.com/orbitalronin94/RONIN-IA/actions/workflows/ronin-official-training-holdout.yml)
- [Primera ejecución oficial #1](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41827976377) — en curso al corte de esta documentación.
- [PR #39 fusionada](https://github.com/orbitalronin94/RONIN-IA/pull/39).

El piloto interno `benchmarks/domains_v1.jsonl` (23 preguntas/15 dominios) se mantiene únicamente como smoke test; no sustituye el holdout externo.
