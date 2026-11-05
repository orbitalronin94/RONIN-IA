# Experimento: main vs seed 202 — 500 pasos / 50 preguntas

## Protocolo
- Base: checkpoint verificado de `main` (`weights/ronin-main.pt`), nunca PR #115.
- Entrenamiento: 500 pasos de next-token prediction sobre el corpus admitido y partición train interna.
- Semilla: 202.
- Inicialización: cargar solo pesos del checkpoint main; AdamW, RNG y sampler se inicializan de nuevo.
- Datos: corpus admitido (literatura española, Mathlib4 y 2 documentos NASA revisados); sin preguntas, QA sintético, tutor ni MMLU-Pro durante el entrenamiento.
- Evaluación mínima: 50 preguntas de MMLU-Pro, split validation, selección estratificada determinista (seed 2026).
- Comparación: main antes vs candidato después sobre los mismos 50 IDs, misma revisión de dataset y mismo protocolo.
- Control adicional: bits/byte sobre la validación interna fija; cobertura MMLU-Pro mínima del 95%.
- Resultado: screening experimental, no puntuación oficial ni certificación; sin promoción automática y sin merge.

## Criterio de lectura
El candidato solo será prometedor si conserva exactamente el mismo holdout, mejora la exactitud en esas 50 preguntas y no empeora bits/byte en la validación interna. Con 50 preguntas, cada acierto equivale a 2 puntos porcentuales: la señal es preliminar y deberá confirmarse con una muestra mayor antes de cualquier promoción.
