# Corpus adicional de razonamiento basado en benchmarks

Este directorio documenta el candidato `ronin-benchmark-reasoning-v1`. Los payloads se generan como artefacto de GitHub Actions para no versionar datos derivados sin completar primero la auditoría.

## Fuentes incluidas

| Fuente | Split | Licencia declarada | Contenido útil | Tratamiento |
|---|---|---|---|---|
| [GSM8K](https://huggingface.co/datasets/openai/gsm8k) | `main/train` | MIT | Preguntas matemáticas y soluciones paso a paso con respuesta final `####` | Se conserva la solución original; se exige marcador de respuesta |
| [CommonsenseQA](https://huggingface.co/datasets/tau/commonsense_qa) | `train` | MIT | Pregunta, cinco opciones y etiqueta correcta | Se conserva la respuesta; no se inventa una explicación que la fuente no contiene |

Revisiones fijadas en `scripts/build_benchmark_reasoning_corpus.py`. Solo se leen particiones `train`.

## Exclusiones deliberadas

- **MMLU-Pro:** ningún split se descarga para entrenamiento. Se reserva como benchmark independiente; usar sus preguntas/soluciones contaminaría la medición.
- **AI2 ARC:** no se incluye en v1. Su tarjeta declara CC-BY-SA-4.0; se requiere revisar implicaciones share-alike antes de decidir su incorporación.
- **MATH / Hendrycks:** no se incluye en v1. Aunque hay metadatos MIT, la disponibilidad de la distribución canónica y los avisos de derechos requieren verificación adicional.
- **OpenBookQA:** no se incluye en v1 porque la tarjeta consultada no establece una licencia de contenido clara.

## Construcción

Ejecutar el workflow manual **Build benchmark reasoning corpus**. El artefacto contiene:

- `records.train.jsonl`: ejemplos normalizados con procedencia.
- `train.txt`: secuencia de texto para el loader de entrenamiento.
- `audit.sample.jsonl`: muestra reproducible de 40 preguntas por fuente por defecto para inspección humana.
- `manifest.json`: revisiones, licencias declaradas, hashes, exclusiones y controles.

## Estado de admisión

**Candidato, no entrenable todavía.** Antes de promoverlo se debe inspeccionar la muestra, verificar las respuestas, revisar la calidad y deduplicar frente a los corpus ya admitidos y frente a los holdouts de RONIN. Las preguntas de validation/test de las fuentes se mantienen fuera del artefacto.

El modelo actual es byte-level y su contexto de entrenamiento ha sido corto. Aunque el corpus incluye soluciones largas, el entrenamiento por ventanas puede exponer fragmentos y no trayectorias completas. No debe afirmarse que esto enseña razonamiento multi-paso sin una evaluación específica.
