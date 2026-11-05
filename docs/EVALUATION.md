# Evaluación de RONIN

Toda comparación debe fijar checkpoint, SHA-256, configuración, tokenizador, corpus, partición, semilla y protocolo.

## Evidencia del modelo main

RONIN-tiny-main-001 (9.922.880 parámetros, paso 1.000) redujo los bits por byte de **7,8684 a 2,8219** en el holdout literario fijo de 18 documentos y 65.536 tokens. El test se reservó para evaluación y no se utilizó para calcular gradientes. La identidad del checkpoint está fijada en `weights/main-model.json`.

## Holdout MMLU-Pro

El evaluador `scripts/evaluate_mmlu_pro.py` utiliza la revisión inmutable `b189ec765aa7ed75c8acfea42df31fdae71f97be` de TIGER-Lab/MMLU-Pro. RONIN puntúa la probabilidad del siguiente byte de la etiqueta A–J. Es un protocolo zero-shot propio: **no equivale al protocolo oficial CoT ni a la puntuación del leaderboard**.

En cada ciclo, el mismo checkpoint base y el candidato se evalúan sobre los mismos IDs, revisión, split y cobertura. Los informes registran selección, preguntas evaluadas, cobertura, accuracy y desglose por dominio. Una muestra estratificada no se presenta como el test completo.

## Criterios de comparación

- Hashes del checkpoint y de los datos fijados.
- Identidad de ítems y misma cobertura antes/después.
- Métricas de lenguaje (BPB) sobre una partición reservada.
- Accuracy y cobertura multidominio.
- Tiempo total, tokens/s, latencia por paso y coste de checkpoints.
- Ausencia de NaN/Inf y carga correcta del checkpoint.

Una pérdida de entrenamiento menor no demuestra mejora general. Un cambio solo se considera favorable cuando mejora la métrica objetivo sin regresiones en las métricas de control. Los candidatos quedan separados del modelo principal hasta revisión explícita.

## Comandos

```bash
python scripts/evaluate_text.py \
  --checkpoint checkpoints/candidate.pt \
  --validation-text /ruta/validacion-reservada.txt \
  --profile tiny --batches 128 --batch-size 2 \
  --seed 2026 --device cpu --output reports/language.json

python scripts/evaluate_domains.py \
  --checkpoint checkpoints/candidate.pt \
  --dataset benchmarks/domains_v1.jsonl \
  --profile tiny --device cpu --output reports/domains.json
```
