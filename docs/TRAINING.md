# Entrenamiento del modelo RONIN

## Estado: proceso experimental

RONIN **no tiene todavía un protocolo de entrenamiento único y definitivo**. Los experimentos cambian según la hipótesis que se quiere probar: número de pasos, semilla, corpus, inicialización, selección de candidatos, presupuesto de evaluación y holdout utilizado.

Por tanto:

- No interpretes los valores por defecto de un workflow como una receta global del proyecto.
- No asumas que todos los workflows ejecutan la misma secuencia.
- No atribuyas a un checkpoint los datos incorporados después de su entrenamiento.
- No consideres que un run exitoso demuestra una mejora del modelo.
- La configuración real de cada experimento se obtiene de su YAML, commit, inputs, logs y artefactos.

El [historial de GitHub Actions](https://github.com/orbitalronin94/RONIN-IA/actions) es el registro operativo de ejecuciones. Los workflows versionados describen los experimentos disponibles en cada commit.

## Línea base y candidatos

El modelo versionado en `main` se identifica en [`weights/main-model.json`](../weights/main-model.json). Ese manifiesto es la fuente de verdad para el nombre, arquitectura, parámetros, checkpoint de origen, hashes y evaluación asociada.

La línea base actual es **RONIN-tiny-seed95-100-001**, con 9.922.880 parámetros y checkpoint de origen de 100 pasos. Es una referencia operativa para comparar experimentos; no implica que 100 pasos sea la duración óptima ni que el modelo haya alcanzado una configuración final.

Los candidatos experimentales se mantienen separados del modelo principal. La promoción requiere revisión explícita de sus métricas y procedencia.

## Familias de workflows

Los siguientes workflows ilustran enfoques distintos. Su configuración puede evolucionar entre commits:

### Cribado multi-semilla sin tutor y holdout por etapas

[main-native-no-tutor-holdout.yml](../.github/workflows/main-native-no-tutor-holdout.yml)

Permite configurar pasos, semillas y profundidad de evaluación mediante `workflow_dispatch`. Parte de los pesos propios, verifica las particiones admitidas, prepara una partición de validación interna desde train, entrena candidatos y los compara. El workflow de la rama principal impone límites a sus inputs; no debe confundirse con experimentos de mayor duración lanzados desde otras ramas.

### Torneo adaptativo de semillas

[adaptive-50-seed-tournament.yml](../.github/workflows/adaptive-50-seed-tournament.yml)

Explora candidatos mediante un torneo de semillas. Su objetivo es comparar inicializaciones/candidatos bajo el protocolo definido por ese workflow. El resultado del torneo es una selección experimental, no una promoción automática.

### Experimentos asociados a un corpus o presupuesto concretos

[micro-corpus-4-seeds.yml](../.github/workflows/micro-corpus-4-seeds.yml)

Este workflow define un experimento específico con semilla 202 y 500 pasos, asociado a una ejecución de PR. Sus parámetros son propios de ese experimento y no constituyen una regla general para futuros entrenamientos.

Además, pueden lanzarse experimentos desde ramas que todavía no estén integradas en `main`, incluidos presupuestos de pasos distintos. Para interpretarlos hay que consultar la ejecución exacta en Actions, no extrapolar la configuración de otro workflow.

## Datos y particiones

La raíz canónica es `data/datasets/`; su [inventario](../data/datasets/README.md) enlaza manifiestos, fuentes y estado de admisión.

Un corpus solo puede entrar en entrenamiento cuando la partición train correspondiente está explícitamente admitida y supera los controles declarados por su manifiesto. La descarga o la presencia de un documento en una biblioteca no bastan para considerarlo entrenable.

- **Train:** únicos datos que pueden contribuir a los gradientes.
- **Validation:** se utiliza para medir y seleccionar dentro de los límites del protocolo; nunca se incorpora a los gradientes.
- **Test/holdout:** debe permanecer aislado de entrenamiento y selección cuando se use como evaluación independiente.

Los controles son por fuente y por alcance. No describas el corpus completo como globalmente certificado si el manifiesto mantiene gates globales, near-duplicates o contaminación de holdout pendientes.

## Evaluación y promoción

Siempre que sea posible, compara el checkpoint inicial y el candidato con exactamente las mismas preguntas, splits, revisión y configuración.

Interpreta las métricas según su alcance:

- Loss, BPB y perplexity miden predicción del texto en una distribución concreta.
- Una muestra de MMLU-Pro es screening; no equivale al benchmark completo ni a una certificación de capacidad general.
- Una mejora en validation no sustituye un resultado independiente en test/holdout.
- Los resultados no son comparables si cambian las preguntas, el split o el protocolo sin declararlo.

La promoción de un candidato requiere revisar, como mínimo, el benchmark pareado, la integridad/hash del checkpoint, el corpus realmente utilizado, las particiones y cualquier limitación del informe. Ningún workflow debe promocionar automáticamente un candidato por haber terminado con `success`.

## Entrenamiento local

Entorno orientativo: Python 3.11 y PyTorch 2.2 o posterior.

```bash
python -m pip install -e '.[dev]'
pytest -q
python scripts/train_text.py \
  --text /ruta/al/corpus-autorizado.txt \
  --profile tiny \
  --steps 500
```

El ejemplo muestra cómo invocar el entrenador local; los 500 pasos son ilustrativos y no una recomendación universal. Para reproducir un experimento, usa sus parámetros y artefactos reales.

## Registro mínimo de cada experimento

Al documentar un run, registra:

1. URL e ID de GitHub Actions, workflow y commit.
2. Checkpoint inicial y sus hashes.
3. Semilla, pasos, configuración y dispositivo.
4. Manifiestos, fuentes y bytes/documentos realmente usados en train.
5. Confirmación de que validation/test no entraron en los gradientes.
6. Holdout, revisión, número de preguntas y protocolo.
7. Métricas antes/después, límites y decisión (screening, candidato o promoción).
8. Checkpoint candidato y artefactos publicados.

La finalidad es que cada resultado sea interpretable y reproducible sin fingir que ya existe una receta estable.

## Expansión funcional ×10 desde el ganador de 10.000 pasos

El workflow [expand-10x-from-10k.yml](../.github/workflows/expand-10x-from-10k.yml) define un experimento independiente, no una nueva línea base:

- Origen inmutable: run [42181780771](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42181780771), checkpoint `checkpoints/seed-95/step-00010000.pt`, SHA-256 `7a7fe93350b72ebc8d645900c2ae8be455a60334e04ac95176e09bab72f981ed`.
- Expansión de 9.922.880 a 100.900.160 parámetros: se mantiene el ancho residual, atención, RoPE, vocabulario y tokenizer; se ensancha SwiGLU de 854 a 12.700 canales.
- Las nuevas columnas de salida SwiGLU se inicializan a cero. Antes de entrenar, el script exige equivalencia de logits con el checkpoint original; si no se cumple, detiene el experimento.
- Continuación de exactamente 1.000 pasos, sin tutor, con seis particiones train scoped: literatura, Mathlib4, NASA file-reviewed, Papers propios, ScienceVerse y CoVoST 2 translation-only.
- Validation/test no se incorporan a los gradientes. El workflow registra hashes y recuentos por fuente; los controles globales G-0, near-duplicates y contaminación del holdout siguen declarados como pendientes.
- La evaluación MMLU-Pro usa un screening pareado de 64 preguntas de validation, con los mismos IDs antes/después. No es una certificación ni un test independiente.
- El artefacto resultante es candidato experimental. No hay promoción automática a `main`.

El workflow se puede lanzar desde GitHub Actions después de integrar esta definición en `main`. Su estado y resultados se consultan en el run y artefacto concretos.
