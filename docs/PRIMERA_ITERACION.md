# Primera iteración y benchmark interno

## Objetivo

Ejecutar RONIN tiny desde pesos aleatorios y medir el cambio en un conjunto de evaluación independiente. La primera referencia usa el corpus **Finance Sentences - North American Spanish** de Mozilla Data Collective, con licencia CC0-1.0.

Este conjunto es pequeño y especializado en español financiero norteamericano. Sirve para comprobar el ciclo de entrenamiento y fijar una primera referencia reproducible; no es un benchmark general de español ni mide conversación, razonamiento o conocimiento general.

## Preparación obligatoria

1. Abre la ficha del conjunto en Mozilla Data Collective y acepta sus condiciones.
2. Crea una credencial de API en tu cuenta de Mozilla.
3. En GitHub, entra en **Settings → Secrets and variables → Actions → New repository secret**.
4. Crea el secreto `MDC_API_KEY` con la clave. No la escribas en el repositorio ni en esta conversación.
5. En **Actions**, ejecuta **Primera iteración y benchmark interno**. Elige entre 1 y 1000 pasos; la primera ejecución recomendada es de 1000.

La ejecución descarga y prepara el corpus, crea una referencia del modelo inicial aleatorio, entrena tiny en CPU y evalúa tanto el modelo inicial como el entrenado sobre validation y test.

## Qué se mide

- Entropía cruzada en nats por byte.
- Perplejidad byte-level.
- Bits por byte (BPB).
- Diferencia inicial → entrenado en validation y test.
- Huellas SHA-256 del archivo de origen, particiones y checkpoints evaluados.
- Parámetros, pasos, tokens presentados aproximados, tiempo de entrenamiento y entorno de ejecución.

El artefacto contiene solo informes JSON y el tiempo de entrenamiento. Los textos del corpus y los checkpoints permanecen en el runner efímero y no se publican ni se guardan en Git.

## Protocolo para iterar

- Mantener el mismo conjunto, hashes, tokenizador, perfil y protocolo de evaluación al comparar ejecuciones.
- Ajustar hiperparámetros usando validation.
- No usar repetidamente test para elegir configuraciones; reservarlo para comparaciones finales.
- Registrar cada experimento con su configuración y SHA-256.
- No comparar directamente perplejidades de tokenizadores distintos; BPB es la métrica principal de esta primera referencia.

## Límites

El modelo tiny usa un tokenizador byte-level y un contexto corto. La mejora en BPB solo indica mejor predicción del siguiente byte en este corpus concreto. No demuestra comprensión, calidad de respuestas ni superioridad frente a modelos externos.

La primera ejecución es una referencia experimental pequeña para iterar, no una afirmación de que RONIN ya sea un modelo útil.
