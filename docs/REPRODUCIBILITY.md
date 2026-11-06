# Reproducibilidad y cadena de procedencia

## Regla

Un run no se considera reproducible solo por tener una URL. La cadena debe identificar checkpoint de entrada, transformación, corpus, configuración, checkpoint de salida y evaluación.

## Cadena Drosophila

| Orden | Elemento | Identificador verificable |
|---|---|---|
| 1 | Entrenamiento del checkpoint base | [Run 42181780771](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42181780771) |
| 2 | Checkpoint base | checkpoints/seed-95/step-00010000.pt; SHA-256 7a7fe93350b72ebc8d645900c2ae8be455a60334e04ac95176e09bab72f981ed |
| 3 | Workflow de expansión | [expand-10x-from-10k.yml](../.github/workflows/expand-10x-from-10k.yml) |
| 4 | Código de expansión/entrenamiento | [expand_and_train_10x.py](../scripts/expand_and_train_10x.py) |
| 5 | Corpus | Seis particiones train scoped; 286.468 documentos/segmentos y 685.023.414 bytes declarados |
| 6 | Ejecución de expansión | [Run 42198068241](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42198068241), commit 23c5cf803b098f06a4bad50cd562aa65bf0d0b86 |
| 7 | Artefacto | [Artifact 13494355120](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42198068241/artifacts/13494355120); SHA-256 del ZIP 3ba95948131aecab2d089d0690c2341d7d11fb041b70de345f6628ae8d938bd5 |
| 8 | Checkpoint Drosophila | SHA-256 7d9345ecb9e3d7ad22aa628b93324ffd18e7b8a477f2d24c04885eced587d2f3 |

El artefacto es un ZIP y su digest no es el hash del checkpoint. No deben intercambiarse.

## Qué está verificado

- El workflow descargó el checkpoint de 10.000 pasos por run ID y el script valida su SHA-256 y metadato de paso.
- Se verificaron las seis fuentes scoped antes de ensamblar train.
- El script exige 500 pasos; el workflow especifica CPU y dos hilos.
- Se ejecuta una prueba de equivalencia funcional antes del entrenamiento.
- El artefacto se publicó con retención declarada hasta el 4 de febrero de 2027.
- El workflow no promociona pesos automáticamente.

## Qué falta publicar para una reproducción cerrada

El manifiesto candidato registra el tamaño del corpus y el hash del checkpoint final, pero no incluye la descomposición por fuente ni el SHA-256 del corpus combinado. El script genera esos datos en experiment-report.json y six-source-mixture.json; deben conservarse y enlazarse como parte del registro de artefactos. Hasta inspeccionar y archivar esos informes, la cadena es trazable por runs y checkpoint, pero el manifiesto por sí solo no basta para reconstruir byte a byte el corpus.

Tampoco se publica en el manifiesto el tiempo real del job, el tiempo exclusivo de entrenamiento ni los minutos facturables de Actions. El workflow declara un límite de 360 minutos; ese límite **no** es el tiempo consumido.

## Protocolo para futuros runs

Cada ejecución debe publicar un JSON de procedencia con:

- Run ID, workflow path, commit SHA, runner y timestamps de inicio/fin.
- SHA-256 del checkpoint base, del checkpoint final y del corpus combinado.
- Para cada fuente: dataset ID, revisión upstream, manifiesto SHA-256, train payload SHA-256, documentos y bytes.
- Hash del orden de concatenación y del texto ensamblado.
- Parámetros, seed, pasos, batch, acumulación, secuencia y tokens efectivamente procesados.
- Tiempo de job, tiempo de entrenamiento y minutos facturables.
- Artefactos con ID, digest, tamaño y expiración.

## Coste de Actions

El run Drosophila se ejecutó en CPU, en ubuntu-26.04, con dos hilos configurados y timeout de 360 minutos. El registro de jobs consultado no expone timestamps de inicio/fin, por lo que no se publica aquí una cifra de minutos consumidos. No se infiere el coste a partir del timeout ni del tamaño del artefacto.

No se declara uso de GPU: el workflow especifica --device cpu. Para convertir el experimento en referencia de coste cero, futuros informes deben guardar los tiempos reales del runner y separar instalación, materialización, entrenamiento y evaluación.
