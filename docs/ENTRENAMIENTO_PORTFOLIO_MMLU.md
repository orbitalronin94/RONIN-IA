# Ciclo de entrenamiento con Portfolio y evaluación MMLU-Pro

## Alcance

El ciclo usa exclusivamente `Portfolio/Papers` como corpus de entrenamiento. La fuente queda fijada en el commit `fffc234fdf3f82b6a90d56ae9b190d1c0de79690` y el preparador genera un manifiesto con autorización, finalidad, número de documentos y SHA-256 del corpus.

El manifiesto declara expresamente que Portfolio/Papers es **solo para entrenamiento**. Por tanto, el workflow no extrae de él particiones de validación o prueba ni presenta la pérdida sobre el corpus de entrenamiento como métrica de generalización.

## Evaluación independiente

Antes de entrenar y después de cada ciclo, RONIN se evalúa sobre el split `test` de `TIGER-Lab/MMLU-Pro`, fijado a la revisión `b189ec765aa7ed75c8acfea42df31fdae71f97be`.

- Se selecciona la misma muestra estratificada por dominio antes y después.
- El benchmark externo nunca se incorpora al corpus de entrenamiento ni se usa para gradientes.
- Las preguntas que exceden el contexto se excluyen y cuentan en el informe; nunca se truncan.
- Se registran exactitud, cobertura, resultados por dominio, hashes de dataset y checkpoint.
- El protocolo RONIN puntúa la probabilidad del siguiente byte de la opción A-J. Es una medición propia, zero-shot y sin CoT; **no es la puntuación oficial de MMLU-Pro ni se compara con su leaderboard**.

## Ejecución

El workflow `Ciclo de entrenamiento autorizado y evaluación MMLU-Pro` ejecuta en PR un smoke de 100 pasos, una semilla y 140 preguntas. La ejecución manual admite hasta 1000 pasos, cinco semillas y `mmlu_limit=0` para recorrer el test completo.

Cada semilla crea un checkpoint inicial aleatorio, mide MMLU-Pro, entrena desde cero y vuelve a medir exactamente los mismos ítems. Los informes se publican como artefacto; el corpus y los checkpoints no se suben.

## Interpretación

El resultado es un experimento de entrenamiento sobre un corpus concreto, no una prueba de conocimiento general. Una subida o bajada de la exactitud en la muestra puede reflejar variación, especialización o regresión; debe contrastarse entre semillas y con otras evaluaciones independientes antes de extraer conclusiones sobre la arquitectura.
