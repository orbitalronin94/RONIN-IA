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


## Primer resultado experimental

Smoke de integración ejecutado el 4 de noviembre de 2026: perfil `tiny` (9.922.880 parámetros), 100 pasos, semilla 1337 y corpus de 48 documentos (uno excluido por el filtro). SHA-256 del corpus: `c03a5a2045e74edd5a3c7ff16af607f887a77204862db2be1de56a922ca2f8d0`.

| Muestra MMLU-Pro | Inicial | Tras 100 pasos |
|---|---:|---:|
| Aciertos | 11/131 | 10/131 |
| Exactitud | 8,40 % | 7,63 % |
| Cobertura | 93,57 % | 93,57 % |

Se seleccionaron 140 preguntas estratificadas; 9 se excluyeron por exceder el contexto y no se truncaron. La diferencia es de -0,76 puntos porcentuales (un acierto menos). Con una sola semilla y 131 preguntas no hay evidencia suficiente para afirmar mejora ni regresión. La exactitud media de azar de la muestra era aproximadamente 10,97 %, por lo que ambos estados siguen siendo débiles en esta tarea.

Este resultado es un smoke de 100 pasos, no la conclusión del proyecto. El workflow reserva los ciclos largos (hasta 1000 pasos y cinco semillas) para ejecución manual; los eventos de PR y push usan un smoke corto de 100 pasos y una semilla.


### Desglose por dominio

| Dominio | Inicial | Tras 100 pasos | Cambio de aciertos |
|---|---:|---:|---:|
| Biología | 0/10 | 0/10 | 0 |
| Empresa | 1/10 | 1/10 | 0 |
| Química | 2/10 | 0/10 | -2 |
| Informática | 1/10 | 0/10 | -1 |
| Economía | 0/10 | 1/10 | +1 |
| Ingeniería | 0/10 | 2/10 | +2 |
| Salud | 0/10 | 0/10 | 0 |
| Historia | 1/6 | 1/6 | 0 |
| Derecho | 0/6 | 0/6 | 0 |
| Matemáticas | 1/10 | 1/10 | 0 |
| Otros | 1/9 | 2/9 | +1 |
| Filosofía | 2/10 | 0/10 | -2 |
| Física | 1/10 | 1/10 | 0 |
| Psicología | 1/10 | 1/10 | 0 |

### Comparación pareada

La comparación por identificador confirma que 110 de los 131 ítems permanecieron incorrectos en ambos estados; no hubo ningún ítem correcto en ambos. En los 21 discordantes, 11 pasaron de correcto a incorrecto y 10 de incorrecto a correcto. La prueba exacta binomial bilateral equivalente al contraste de McNemar da **p = 1,00**. No hay señal estadística de cambio en esta muestra; el signo negativo de un acierto no debe presentarse como regresión demostrada.


## Interpretación

El resultado es un experimento de entrenamiento sobre un corpus concreto, no una prueba de conocimiento general. Una subida o bajada de la exactitud en la muestra puede reflejar variación, especialización o regresión; debe contrastarse entre semillas y con otras evaluaciones independientes antes de extraer conclusiones sobre la arquitectura.


## Ciclo mixto v2: fuentes de entrenamiento

La siguiente versión del workflow mezcla, con manifiesto y SHA-256 por fuente:

1. **Portfolio/Papers**: permiso expreso del titular, revisión inmutable; se usa únicamente su partición de entrenamiento.
2. **CLiGS Textbox, CoNSSA y ELTeC-spa**: revisiones Git fijadas en `scripts/prepare_open_corpora.py`; se incorpora únicamente `train.txt`. Las particiones `validation` y `test` quedan reservadas y no se pasan al entrenador.
3. **Phi-4-mini-instruct**: tutor MIT de 3,8B parámetros, ajustado para instrucciones y con español entre sus idiomas declarados. Se generan 32 propuestas en 16 dominios, se filtran por estructura REF y se incorpora solo la salida que supera el esquema. La auditoría REF no demuestra que las respuestas sean verdaderas ni que sus fuentes sean correctas; se registra como augmentación sintética de tutor, no como dato experto. La licencia MIT corresponde al modelo, no se atribuye automáticamente a las salidas; el lote generado permanece temporal en el runner y no se publica como artefacto.

El workflow concatena esas tres entradas en un corpus mixto reproducible y publica su manifiesto con tamaños y hashes. Cada semilla parte de inicialización aleatoria; los pesos de Phi-4 nunca se cargan en RONIN.

### Qué queda fuera y por qué

- `benchmarks/domains_v1.jsonl` y MMLU-Pro `test`: evaluación, nunca gradientes.
- `validation.txt` y `test.txt` de la literatura: holdouts, nunca entrenamiento.
- El corpus sintético de pseudo-palabras: útil para probar el pipeline, no aporta conocimiento lingüístico; se reserva para smoke tests.
- Los casos criptográficos y fuentes primarias marcados `excluded_pending_manual_review`: no se entrenan hasta revisión documental.
- Project Gutenberg, Internet Archive, Common Corpus y BookCorpusOpen: siguen bloqueados por G-0; este ciclo no los descarga. G-0 no se considera superado por usar las tres fuentes literarias ya integradas, que pasan una lista de permitidos y una validación de procedencia separadas.

El ciclo en PR conserva 100 pasos y una semilla para comprobar el circuito completo. Al integrarse en `main`, el push ejecuta 1000 pasos por semilla con `1337, 2027, 42`. MMLU-Pro sigue siendo una evaluación propia de siguiente byte A-J, no comparable con su leaderboard oficial.
