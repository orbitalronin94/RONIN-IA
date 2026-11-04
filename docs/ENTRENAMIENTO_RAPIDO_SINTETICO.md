# Bootstrap rápido de RONIN sin corpus documental

## Propósito

Cuando el control G-0 no autoriza entrenamiento con documentos, RONIN puede ejecutar un
ciclo de arranque **procedural y sintético**. Esto evita que la falta de bibliotecas detenga
todo el trabajo de ingeniería, sin convertir material de derechos inciertos en datos de
entrenamiento.

Workflow: `.github/workflows/rapid-synthetic-bootstrap.yml`

## Separación de vías

- **Vía documental:** continúa bajo G-0 y exige autorización legal explícita. Usa su propio
  checkpoint/cache `ronin-open-warmstart`.
- **Bootstrap sintético:** solo se ejecuta cuando G-0 no autoriza corpus. Genera patrones
  reproducibles localmente; no descarga fuentes, no ingiere bibliotecas y no cambia el
  estado de admisión legal. Usa exclusivamente `ronin-synthetic-warmstart`.

Los checkpoints de ambas vías no se mezclan automáticamente.

## Diseño del ciclo sintético

1. Genera splits deterministas con rangos de identificadores disjuntos.
2. Registra hashes y procedencia vacía en `synthetic-dataset-manifest.json`.
3. Evalúa BPB sobre el split sintético de validación.
4. Ejecuta 25 pasos CPU sobre el perfil `tiny`.
5. Repite la evaluación sobre exactamente el mismo split.
6. Promueve el checkpoint sintético únicamente si BPB disminuye estrictamente.
7. Publica métricas, manifiesto y checkpoint candidato como artefacto.

## Interpretación y límites

Este experimento sirve para comprobar el pipeline, ejercitar el modelo byte-level y aprender
regularidades artificiales. **No equivale a entrenamiento lingüístico con conocimiento
externo**, no prueba razonamiento general, no sustituye las 16 bibliotecas y no se presenta
como mejora en MMLU-Pro. MMLU-Pro queda pendiente para evaluación independiente cuando
corresponda.

G-0 no se modifica ni se relaja. El bootstrap no autoriza descargas, redistribución,
admisión de documentos ni entrenamiento documental.
