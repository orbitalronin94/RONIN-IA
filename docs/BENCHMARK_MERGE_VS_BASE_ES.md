# Comparación determinista: modelo original vs fusión

Este script usa [EleutherAI lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness), un harness open source con tareas versionadas para evaluación de LLM. Evalúa **el mismo conjunto de tareas y configuración** sobre el original y el directorio/modelo fusionado; no hace la fusión ni altera los pesos.

## Benchmarks por defecto

- `arc_easy`: preguntas de ciencia de opción múltiple.
- `hellaswag`: razonamiento de sentido común/completado de escenarios.
- `truthfulqa_mc2`: selección de respuestas verdaderas frente a errores comunes.
- `gsm8k`: problemas matemáticos de primaria.

Las definiciones, métricas y datasets pertenecen al harness/datasets de origen. El límite predeterminado es 100 ejemplos por tarea para que la primera comparación sea asequible; no equivale a una evaluación completa.

## Ejecución

Recomendado: usa un entorno virtual y conserva la versión de `lm-eval` en ambas ejecuciones.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install "lm-eval[hf]"
python scripts/benchmark_merge_vs_base.py \
  --base-model Qwen/Qwen3-0.6B \
  --merged-model ./ronin-fusion-experimental \
  --seed 42 --limit 100 --num-fewshot 0 --batch-size 1 \
  --output-dir results/merge-vs-base
```

En Windows, activa el entorno con `.venv\\Scripts\\activate`. Si una tarea cambia de nombre en la versión instalada, consulta `lm-eval --tasks list` y especifica `--tasks` explícitamente.

## Reproducibilidad y lectura

- Semilla fija (42 por defecto), `PYTHONHASHSEED`, cero ejemplos few-shot, mismo límite, batch size, tareas y versión del harness.
- Se ejecuta primero el original y después la fusión, en el mismo entorno. Para mayor rigor, fija versiones exactas de Python, PyTorch, Transformers, `lm-eval`, datasets y revisiones de los modelos; la descarga remota puede cambiar si no se fijan revisiones.
- `comparison.json` registra las métricas, delta por tarea, promedio de deltas comparables y tareas mejoradas/regresadas/sin cambio.
- El script no declara ganador automáticamente: diferencias de métrica no comparables se marcan como tales. No mezcles porcentajes entre tareas distintas para afirmar una mejora universal.
- Los benchmarks públicos pueden estar contaminados en datos de entrenamiento. Revisa muestras y añade evaluación humana ciega, especialmente para español, código y seguridad.
- Los resultados previos de RONIN-IA basados en heurísticas no son equivalentes a estos benchmarks estandarizados.

El primer experimento debería usar `--limit 100`; después ejecuta el conjunto completo (`--limit 0`) y repite con varias semillas para medir estabilidad.
