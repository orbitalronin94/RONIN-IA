# Torneo conservador de checkpoints — ganador 6/50

## Estado

Esta rama continúa el experimento desde las dos candidatas empatadas con 7/50. No modifica `main`, no sustituye `weights/ronin-main.pt` y no autoriza promoción automática. El workflow se ejecuta en la PR para validar los cuatro entrenamientos; los resultados solo se aceptarán tras comprobar artefactos y cobertura.

Como antecedente, el checkpoint 6/50 y su continuación de 500 pasos pertenecen al torneo anterior; no son las semillas de este experimento.

## Nuevo experimento B/C — 10.000 pasos (2026-11-05)

Se comparan B (replay equilibrado) y C (replay equilibrado + anclaje L2) desde dos semillas independientes: B-7/50 y C-7/50. Cada semilla genera ambas variantes con 10.000 pasos por entrenamiento: cuatro entrenamientos y 40.000 pasos totales, ejecutados secuencialmente. El workflow evalúa cada semilla antes de entrenar y cada resultado después sobre los mismos 50 IDs, revisión y hash del split validation; exige 50/50, cero skips y cobertura 100 %. Se guardan checkpoints finales, hashes, métricas y diferencias por pregunta. No hay promoción automática. Este validation de 50 preguntas es screening de desarrollo, no confirmación independiente.

## Pregunta experimental

¿Podemos obtener mejoras de predicción del corpus sin perder el comportamiento que produjo el 6/50? Los candidatos deben partir exactamente del mismo checkpoint, corpus, partición interna, contexto, semilla de muestreo y holdout pareado.

## Candidatos

| ID | Método | Presupuesto | Parámetros iniciales |
|---|---|---:|---|
| A | Fine-tuning conservador con anclaje L2 a los pesos iniciales | 100 pasos (torneo inicial) | LR 2.5e-6; min LR 2.5e-7; grad clip 1.0; penalización anclada normalizada |
| B | Replay equilibrado por fuente | 10.000 pasos (nuevo experimento) | Literatura 50 %, Mathlib4 49.5 %, NASA revisado máximo 0.5 % |
| C | Replay equilibrado + anclaje L2 | 10.000 pasos (nuevo experimento) | Igual que B más LR conservador y anclaje |
| D | Interpolación de checkpoints, sin entrenamiento | 0 pasos | alpha 0.10, 0.25 y 0.50 |

La mezcla no asigna 5 % a NASA: con solo dos documentos esa proporción los sobremuestrearía intensamente. El límite 0.5 % es un techo experimental, no una afirmación de que NASA aporte más señal. Se comparará también contra muestreo proporcional al corpus como control de B/C.

## Implementación disponible en esta rama

1. Añadir una penalización explícita a la pérdida de entrenamiento:
   `loss_total = loss_corpus + lambda * mean((W - W0)^2)`.
   Debe calcularse sobre parámetros entrenables compatibles, excluir buffers y guardar lambda/configuración en los informes.
2. Añadir un generador de mezcla por fuente con cuotas reproducibles, sin copiar ni modificar los documentos de origen. Registrar bytes, documentos, muestras y proporción real observada.
3. Interpolación solo si ambos checkpoints tienen claves, formas y dtypes compatibles. Construir pesos FP32, comprobar finitud y cargar strict; no interpolar buffers incompatibles.
4. El evaluador debe medir el checkpoint ganador antes de cada candidato y evaluar después exactamente los mismos IDs, revisión, split y configuración.
5. Gate estricto: 50/50, cobertura 100 %, cero skips, mismos IDs, misma revisión y mismo hash de dataset. Si no se cumple antes, abortar antes de entrenar.
6. Validación interna BPB/PPL secundaria, con mismo archivo/hash y mismos lotes.
7. Guardar checkpoint, SHA-256, configuración, logs y reporte por candidato. No sobrescribir pesos main.

## Protocolo de selección

La muestra de 50 preguntas validation ya se ha usado para comparar ciclos anteriores y por tanto está parcialmente expuesta a selección. Se permite usarla solo como screening de desarrollo, no como confirmación independiente.

- Screening inicial: comparar los métodos en los mismos 50 IDs de validation, antes/después. Nuevo experimento: B y C con 10.000 pasos cada uno.
- Selección: conservar como máximo un candidato provisional; no promoverlo.
- Confirmación: evaluar el candidato provisional y el ganador original en un conjunto independiente no usado para selección (preferentemente split test completo, o una muestra pre-registrada de al menos 100 ítems si el protocolo y el presupuesto lo permiten). No ajustar hiperparámetros después de ver esa confirmación.
- Reportar aciertos, accuracy, delta en puntos porcentuales, predicciones cambiadas, nuevos aciertos, regresiones, categorías, cobertura y skips.
- No declarar razonamiento general a partir de una muestra pequeña ni comparar este protocolo next-byte con la puntuación oficial CoT de MMLU-Pro.

## Criterios de aceptación

Un candidato no gana por mejorar BPB/PPL únicamente.

1. Integridad: 100 % de cobertura, cero skips y holdout idéntico.
2. No regresión: no perder aciertos respecto al ganador 6/50 en el screening; cualquier regresión debe dejarlo fuera del grupo preferente.
3. Señal positiva: al menos un acierto nuevo, o mejora confirmada en test independiente; el screening por sí solo no basta para promoción.
4. Estabilidad: publicar todas las regresiones por categoría, no solo el total.
5. Reproducibilidad: checkpoint y corpus con SHA-256, semilla, configuración, código y artefactos trazables.

## Presupuesto y ejecución

El torneo inicial usó 300 pasos de entrenamiento (A/B/C: 100 cada uno); D no entrenó. La continuación actual usa 40.000 pasos totales: cuatro entrenamientos de 10.000 pasos, dos variantes desde cada una de las dos semillas 7/50. Las variantes no se ejecutan en paralelo si compiten por CPU; se ejecutan secuencialmente para mantener throughput y memoria predecibles.

La implementación está disponible en `scripts/run_checkpoint_tournament.py`, `ronin/data/source_batches.py` y `ronin/training/loop.py`. El workflow manual está en `.github/workflows/checkpoint-tournament-6of50.yml`. Antes de lanzar el workflow, deben pasar los checks de la PR y verificarse los artefactos de origen. El workflow no promueve pesos automáticamente.


## Continuación desde las dos candidatas 7/50

El experimento de continuación toma como semillas independientes los checkpoints B y C del run
[42081603425](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42081603425):

- B — SHA-256 `bcef0ec6db635f7f75d1fd84bf2e407aa50e86d34b1e7849516c158708256123`.
- C — SHA-256 `e27f11c2eb93e2c8c3d95da6b4249a793fdc9d042981d1a5cdd98715c5addc92`.

Sobre cada semilla se ejecutan las dos variantes B/C con 10.000 pasos cada una: B y C desde la semilla B, y B y C desde la semilla C. Son cuatro entrenamientos de 10.000 pasos, 40.000 pasos totales. Cada resultado se compara con su propia semilla
mediante los mismos 50 IDs de MMLU-Pro validation, revisión y hash de dataset, con cobertura completa y cero regresiones reportadas por separado. No hay promoción automática y no se modifica `main`.
