# Entrenamiento del modelo RONIN

## Estado: proceso experimental

RONIN **no tiene todavía un protocolo de entrenamiento único y definitivo**. Los experimentos cambian según la hipótesis: pasos, semilla, corpus, inicialización, selección de candidatos, presupuesto de evaluación y holdout.

- No interpretes los valores por defecto de un workflow como receta global.
- No atribuyas a un checkpoint los datos incorporados después de su entrenamiento.
- No consideres que un run exitoso demuestra una mejora.
- Registra tokens procesados, no solo pasos.
- Separa minutos reales de runner, tiempo de entrenamiento y tiempo total de workflow.
- La configuración real de cada experimento se obtiene de su YAML, commit, inputs, logs y artefactos.

El [historial de GitHub Actions](https://github.com/orbitalronin94/RONIN-IA/actions) es el registro operativo. Consulta [historial experimental](EXPERIMENT_HISTORY.md), [reproducibilidad](REPRODUCIBILITY.md), [procedencia del corpus](CORPUS_PROVENANCE.md) y [métricas](METRICS.md).

## Roles de los modelos

### Línea base operativa en main

El paquete weights/ronin-main.pt y el manifiesto weights/main-model.json fijan **RONIN-tiny-seed95-100-001**, de 9.922.880 parámetros. Su checkpoint de origen tiene 100 pasos y seed 95. Sigue siendo el modelo operativo de main hasta una promoción explícita.

### Drosophila: candidato de organismo modelo

**Ronin - Drosophila (100.900.160 parámetros)** es un candidato experimental mergeable, no el modelo principal promocionado. Su expansión parte del checkpoint ganador de 10.000 pasos (run 42181780771; SHA-256 7a7fe93350b72ebc8d645900c2ae8be455a60334e04ac95176e09bab72f981ed) y continúa durante 500 pasos en CPU (run 42198068241).

El script scripts/expand_and_train_10x.py ensancha SwiGLU de 854 a 12.700 canales, conserva el resto de los tensores compatibles y pone a cero la contribución de los canales nuevos. Exige una comprobación de equivalencia de logits antes de entrenar. El modelo resultante tiene 100.900.160 parámetros.

**Clasificación de evidencia: MODEL_ORGANISM_ONLY + SCREENING_ONLY. No certifica razonamiento general.** El screening publicado usa 64 preguntas del split validation, con los mismos IDs: 5/64 antes y 5/64 después. No es el test completo de MMLU-Pro.

## Régimen de Drosophila: qué se ejecutó

El script de expansión fija los siguientes valores:

| Parámetro | Valor |
|---|---:|
| Perfil de arquitectura de partida | tiny |
| Longitud de contexto | 128 |
| Batch size | 1 |
| Acumulación de gradiente | 1 |
| Pasos | 500 |
| Posiciones de entrada nominales | 64.000 |
| Learning rate inicial | 1e-5 |
| Learning rate mínimo | 1e-6 |
| Warmup | 50 pasos |
| Weight decay | 0,1 |
| Gradient clipping | 1,0 |
| Seed de continuación | 20261106 (valor por defecto del script) |
| Dispositivo | CPU |
| Hilos | 2 |

El sampler selecciona ventanas aleatorias del corpus con reemplazo. Por ello, 64.000 posiciones nominales no significan 64.000 bytes únicos ni una pasada completa por el corpus. La exposición efectiva y su relación con el entrenamiento previo se explican en [METRICS.md](METRICS.md).

## Familias de workflows

### Expansión funcional ×10 desde el ganador de 10k

[expand-10x-from-10k.yml](../.github/workflows/expand-10x-from-10k.yml)

- Descarga el checkpoint exacto del run 42181780771.
- Verifica literatura, Mathlib4, NASA file-reviewed, Papers propios, ScienceVerse y CoVoST 2 translation-only.
- Ensambla únicamente particiones train scoped.
- Ejecuta prueba de expansión funcional, 500 pasos y screening MMLU-Pro validation de 64 preguntas.
- Publica checkpoint e informe como artefacto.
- No promociona pesos automáticamente.

### Cribado multi-semilla sin tutor

[main-native-no-tutor-holdout.yml](../.github/workflows/main-native-no-tutor-holdout.yml)

Permite configurar pasos, semillas y profundidad de evaluación. Su corpus y checkpoint de partida son los fijados por el propio workflow; no son intercambiables con el experimento Drosophila.

### Torneo adaptativo de semillas

[adaptive-50-seed-tournament.yml](../.github/workflows/adaptive-50-seed-tournament.yml)

Explora candidatos bajo su propio protocolo. No debe confundirse con cuatro seeds independientes de Drosophila.

## Datos y particiones

La raíz canónica es data/datasets/; su [inventario](../data/datasets/README.md) enlaza manifiestos, fuentes y estado de admisión.

- **Train:** única partición que puede contribuir a gradientes.
- **Validation:** desarrollo y screening; nunca se incorpora a gradientes.
- **Test/holdout:** evaluación independiente; no debe usarse para entrenar ni seleccionar repetidamente sin declarar el riesgo de contaminación por selección.

Un estado train-scoped no certifica automáticamente el corpus global. G-0, near-duplicates y contaminación de benchmarks/holdouts deben leerse según cada manifiesto.

## Evaluación y promoción

- Loss, BPB y perplexity miden predicción de texto en una distribución concreta.
- Un screening MMLU-Pro es una muestra de cribado, no el benchmark completo.
- Validation no sustituye un resultado independiente en test/holdout.
- Una comparación exige los mismos IDs, split, revisión, prompt y protocolo.
- La promoción requiere revisar checkpoint, corpus, particiones, evaluación y limitaciones.

Ningún candidato se promociona por el mero hecho de que Actions termine con success.

## Entrenamiento local

El perfil local expuesto por scripts/train_text.py es tiny (9.922.880 parámetros). No existe un --profile drosophila en ese entrenador. El comando siguiente es un smoke test limitado a 1.000 pasos, no una reproducción del candidato de 100,9M:

~~~bash
python -m pip install -e '.[dev]'
pytest -q
python scripts/train_text.py \
  --text /ruta/al/corpus-autorizado.txt \
  --profile tiny \
  --steps 500 \
  --seed 20261106 \
  --device cpu \
  --num-threads 2 \
  --metrics-out metrics.json
~~~

Para reproducir Drosophila hay que recuperar el checkpoint base y el corpus exactos del run, instalar el entorno y ejecutar el flujo de expansión. No se publica un tiempo local de referencia porque no existe una medición comparable verificada.

## Registro mínimo de cada experimento

1. URL e ID de Actions, workflow, commit y runner.
2. Checkpoint inicial/final y SHA-256.
3. Arquitectura, parámetros, seed y estado del optimizador.
4. Pasos, batch, acumulación, longitud de secuencia y **tokens/posiciones realmente procesados**.
5. Manifiestos, documentos, bytes y hashes de cada partición train.
6. Confirmación de que validation/test no entraron en gradientes.
7. Tiempo total del job, tiempo de entrenamiento y minutos facturables del runner.
8. Holdout, revisión, IDs, cobertura y métricas antes/después.
9. Número de seeds, resultados individuales, media, desviación y decisión.

El objetivo es que cada resultado sea interpretable sin fingir que existe una receta estable.
