# Historial experimental de RONIN

Este documento separa las líneas de modelo y evita atribuir resultados de una etapa a otra.

## Secuencia documentada

| Etapa | Run | Modelo / parámetros | Entrenamiento | Evidencia y estado |
|---|---|---:|---:|---|
| Línea base fijada | [42121731925](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42121731925) | 9.922.880 | 100 pasos, seed 95 | RONIN-tiny-seed95-100-001, empaquetado en main |
| Entrenamiento largo | [42181780771](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42181780771) | 9.922.880 | 10.000 pasos, seed 95 | BPB 3,8152→2,9798; MMLU-Pro test 1.295/12.032→1.314/12.032; checkpoint de origen de Drosophila |
| Expansión ×10,17 y continuación | [42198068241](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42198068241) | 100.900.160 | 500 pasos, seed 20261106 por defecto del script | Logits preservados antes del entrenamiento; MMLU-Pro validation 5/64→5/64; candidato mergeable, no promocionado |

## Interpretación

### Línea base de 9,9M

El modelo que sigue en weights/ronin-main.pt tiene 9.922.880 parámetros. Su manifiesto conserva los resultados de la evaluación interna y el screening de 50 preguntas. No debe reemplazarse su identidad documental por la del candidato de 100,9M.

### Checkpoint ganador de 10.000 pasos

Este run es el origen inmediato de Drosophila. El checkpoint de entrada se identifica por SHA-256:

7a7fe93350b72ebc8d645900c2ae8be455a60334e04ac95176e09bab72f981ed

El resultado full test de MMLU-Pro y BPB corresponde a este régimen de 9,9M, antes de ampliar SwiGLU. No se atribuye a Drosophila.

### Drosophila

El run 42198068241 amplió SwiGLU y entrenó 500 pasos en CPU. Su checkpoint final se identifica por SHA-256:

7d9345ecb9e3d7ad22aa628b93324ffd18e7b8a477f2d24c04885eced587d2f3

El screening fue de 64 preguntas de validation, no del test completo. La exactitud permaneció en 5/64. La clasificación es MODEL_ORGANISM_ONLY + SCREENING_ONLY; no certifica razonamiento general.

## Seeds y varianza

La evidencia publicada para la continuación Drosophila es **n=1**. No hay cuatro ejecuciones Drosophila comparables documentadas en el manifiesto consultado. No se publican media, desviación ni curvas de cuatro seeds porque no existen esos datos verificados.

El seed 95 del checkpoint base y el seed por defecto 20261106 de la continuación son etapas diferentes; no son cuatro réplicas estadísticas.

## Promoción

- La línea base compacta permanece en main.
- Drosophila permanece como candidato mergeable.
- Mergeable no significa promovido ni mejor.
- La promoción requiere evidencia nueva, gates de datos resueltos y actualización atómica de pesos y manifiesto principal.
