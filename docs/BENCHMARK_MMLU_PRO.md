# Evaluación externa MMLU-Pro en RONIN

## Fuente y alcance

RONIN incorpora un adaptador de evaluación para [TIGER-Lab/MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro), benchmark publicado con licencia MIT declarada en la ficha del conjunto. El test contiene aproximadamente 12.032 preguntas en 14 dominios académicos: matemáticas, física, química, biología, informática, ingeniería, economía, derecho, salud, psicología, empresa, filosofía, historia y otros.

La ejecución carga únicamente el split `test`. Sus preguntas no se mezclan con corpus de entrenamiento ni se usan para actualizar pesos. Esta evaluación externa es independiente del gate G-0 de adquisición de corpus de entrenamiento.

## Protocolo RONIN

- Zero-shot: pregunta original y todas las opciones disponibles (hasta diez).
- El modelo puntúa la probabilidad del siguiente byte correspondiente a la letra A-J después de `Answer: `.
- Se eliminan los marcadores de relleno `N/A` antes de volver a etiquetar las opciones, siguiendo el preprocesamiento de referencia.
- Se informa exactitud global, exactitud por dominio, tasa de azar media, huella SHA-256 del conjunto, checkpoint, contexto y cobertura.
- El muestreo por defecto selecciona 140 preguntas en rondas equilibradas por dominio, con semilla fija. `--limit 0` selecciona todo el split.
- No se truncan prompts. Los que exceden el contexto se cuentan como omitidos y reducen la cobertura.

Este protocolo es una adaptación experimental de RONIN. No reproduce el protocolo oficial con razonamiento paso a paso y no debe compararse directamente con el leaderboard oficial de MMLU-Pro. Un contexto ampliado en inferencia tampoco demuestra que el modelo haya aprendido a operar a esa longitud durante el entrenamiento.

## Ejecución local

Instalar la dependencia opcional:

```bash
pip install -e ".[benchmarks]"
```

Evaluar un checkpoint:

```bash
python scripts/evaluate_mmlu_pro.py \
  --checkpoint checkpoints/mi-checkpoint.pt \
  --profile tiny \
  --limit 140 \
  --context-length 2048 \
  --output reports/mmlu-pro.json
```

Para intentar el test completo, usar `--limit 0`. Para exigir que todas las preguntas seleccionadas quepan en el contexto, añadir `--require-full-coverage`.

## Ciclos de entrenamiento

El workflow `Ciclos sintéticos de entrenamiento RONIN` incorpora la evaluación MMLU-Pro al ejecutarse manualmente. Compara el checkpoint inicial y el final de la primera semilla; el resto de semillas conserva los benchmarks internos. Los parámetros `mmlu_limit` y `mmlu_context_length` controlan el tamaño de muestra y el contexto.

El workflow publica informes, no checkpoints. Los ciclos automáticos de PR y push siguen siendo smoke tests sintéticos y no descargan MMLU-Pro.
