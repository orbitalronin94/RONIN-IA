# Primera iteración y benchmark interno

## Objetivo

Entrenar RONIN tiny desde pesos aleatorios y medir su capacidad de predicción del siguiente byte en textos españoles de dominio público. La primera referencia usa tres repositorios literarios abiertos:

- CLiGS Textbox: novelas españolas e hispanoamericanas.
- CoNSSA: novelas del Siglo de Oro.
- ELTeC-spa: novelas españolas.

Los textos se declaran de dominio público; el marcado TEI y los metadatos se distribuyen bajo CC BY 4.0. Los repositorios y commits concretos están fijados en `scripts/prepare_open_corpora.py` y descritos en `docs/FUENTES_CORPUS_ABIERTOS.md`.

## Acceso y preparación

No se necesita cuenta, registro, token, clave API ni secreto de GitHub. El workflow descarga archivos ZIP públicos por HTTPS desde GitHub, fijados a commits inmutables.

La preparación:

1. Extrae únicamente el contenido textual del elemento TEI `text`, no las cabeceras de metadatos.
2. Conserva repositorio, commit, rutas, licencia declarada y SHA-256 de cada archivo comprimido.
3. Excluye documentos cortos, XML inválido, duplicados exactos y textos con patrones de credenciales.
4. Divide documentos completos en `train`, `validation` y `test` de forma determinista; no reparte fragmentos de una misma obra entre particiones.
5. Publica manifiesto, recuentos y hashes de las particiones.

La descarga se ejecuta en el runner efímero. No se suben textos ni checkpoints al repositorio o al artefacto.

## Dos modos de ejecución

En **Actions → Primera iteración y benchmark interno** se elige el número de pasos (1–1000) y si se debe evaluar el holdout reservado.

- **Experimento ordinario (`benchmark_holdout=false`)**: entrena desde cero y mide únicamente `validation`. Es el modo para iterar y comparar cambios.
- **Medición de referencia (`benchmark_holdout=true`)**: ejecuta el mismo entrenamiento y, además, mide `test` antes y después. Esta opción debe reservarse para hitos de referencia, no para cada ajuste.

La partición `test` nunca se entrega al bucle de entrenamiento ni se usa para calcular gradientes. La evaluación del holdout no interviene en selección de hiperparámetros. El test es público y, por tanto, no puede garantizarse secreto frente a contaminación externa; el protocolo garantiza separación interna y trazabilidad, no confidencialidad.

## Qué se mide

- Entropía cruzada en nats por byte.
- Perplejidad byte-level.
- Bits por byte (BPB), métrica principal para comparar predicción con el tokenizador byte.
- Diferencia inicial → entrenado en validation y, solo en mediciones explícitas, test.
- Procedencia, commits, SHA-256 de los archivos de origen y particiones.
- Número de documentos por fuente y partición, documentos excluidos.
- Parámetros, pasos, tokens presentados aproximados, tiempo de entrenamiento y entorno.

El artefacto contiene solo informes JSON y el tiempo de entrenamiento. Los textos del corpus y los checkpoints permanecen en el runner efímero.

## Protocolo para iterar y publicar resultados

1. Mantener idénticos los commits de corpus, hashes, tokenizador, perfil, semilla y protocolo al comparar ejecuciones.
2. Ajustar hiperparámetros usando exclusivamente `validation`.
3. No activar `benchmark_holdout` en las iteraciones ordinarias.
4. Reservar `test` para hitos de referencia publicados; registrar el hash del corpus, del checkpoint, la configuración completa y el entorno.
5. No comparar directamente perplejidades de tokenizadores distintos; usar BPB y documentar su cálculo.
6. No presentar una mejora de BPB como prueba de razonamiento, conocimiento factual o calidad conversacional.

## Límites y alcance

Esta primera prueba es un **benchmark de modelado de lenguaje**, no un benchmark general de capacidades. Mide predicción del siguiente byte en literatura histórica española. No representa por sí sola el español contemporáneo, oral, técnico ni todas sus variedades. Una BPB menor indica mejor compresión/predicción de este conjunto concreto; no demuestra comprensión, diálogo útil ni razonamiento.

El holdout actual se construye por documento desde las mismas fuentes públicas, con separación determinista. Es una referencia inicial pequeña. Para una siguiente versión conviene incorporar un corpus independiente de otro dominio y país (por ejemplo, textos institucionales o prensa histórica con derechos verificados), fijarlo por versión y crear una batería de tareas de generación/seguimiento de instrucciones. No se integrará ninguna fuente que requiera credenciales.

Esta ejecución es una referencia experimental pequeña para iterar, no una afirmación de que RONIN ya sea un modelo útil.
