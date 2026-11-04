# Primera iteración y benchmark interno

## Objetivo

Ejecutar RONIN tiny desde pesos aleatorios y medir el cambio en un conjunto de evaluación independiente. La primera referencia usa tres repositorios literarios públicos:

- CLiGS Textbox: novelas españolas e hispanoamericanas.
- CoNSSA: novelas del Siglo de Oro.
- ELTeC-spa: novelas españolas.

Los textos se declaran de dominio público; el marcado TEI y los metadatos se distribuyen bajo CC BY 4.0. Los repositorios y commits concretos están fijados en `scripts/prepare_open_corpora.py` y descritos en `docs/FUENTES_CORPUS_ABIERTOS.md`.

## Acceso y preparación

No se necesita cuenta, aceptación de términos mediante registro, token, clave API ni secreto de GitHub. El workflow descarga archivos ZIP públicos por HTTPS desde GitHub, fijados a commits inmutables.

La preparación:

1. Extrae únicamente el contenido textual del elemento TEI `text`, no las cabeceras de metadatos.
2. Conserva repositorio, commit, rutas, licencia declarada y SHA-256 de cada archivo comprimido.
3. Excluye documentos cortos, XML inválido, duplicados exactos y textos con patrones de credenciales.
4. Divide documentos completos en train, validation y test de forma determinista; no reparte fragmentos de una misma obra entre particiones.
5. Publica manifiesto y hashes de las particiones.

La descarga se ejecuta en el runner efímero. No se suben los textos ni los checkpoints al repositorio o al artefacto.

## Ejecución

En **Actions**, ejecuta **Primera iteración y benchmark interno**. Elige entre 1 y 1000 pasos; la primera ejecución recomendada es de 1000. Se entrena el perfil tiny en CPU desde inicialización aleatoria.

## Qué se mide

- Entropía cruzada en nats por byte.
- Perplejidad byte-level.
- Bits por byte (BPB).
- Diferencia inicial → entrenado en validation y test.
- Procedencia, commits, SHA-256 de los archivos de origen y particiones.
- Número de documentos por fuente y partición, documentos excluidos.
- Parámetros, pasos, tokens presentados aproximados, tiempo de entrenamiento y entorno.

El artefacto contiene solo informes JSON y el tiempo de entrenamiento. Los textos del corpus y los checkpoints permanecen en el runner efímero.

## Protocolo para iterar

- Mantener el mismo conjunto, hashes, tokenizador, perfil y protocolo al comparar ejecuciones.
- Ajustar hiperparámetros usando validation.
- Reservar test para comparaciones finales.
- Registrar cada experimento con su configuración y SHA-256.
- No comparar directamente perplejidades de tokenizadores distintos; BPB es la métrica principal de esta primera referencia.

## Límites

La primera referencia es literaria e histórica. No representa por sí sola el español contemporáneo, oral, técnico ni todas sus variedades. La mejora en BPB solo indica mejor predicción del siguiente byte en este corpus concreto. No demuestra comprensión, calidad conversacional ni razonamiento.

Esta ejecución es una referencia experimental pequeña para iterar, no una afirmación de que RONIN ya sea un modelo útil.
