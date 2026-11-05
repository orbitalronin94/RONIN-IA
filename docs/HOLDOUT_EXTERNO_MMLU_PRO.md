# Holdout externo RONIN: MMLU-Pro

## Fuente y derechos

- Dataset: [TIGER-Lab/MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro)
- Licencia declarada en la ficha del dataset fijada: MIT.
- Revisión inmutable: `b189ec765aa7ed75c8acfea42df31fdae71f97be`.
- Split reservado: `test`, 12.032 preguntas disponibles.
- Muestra inicial del ciclo 2: 140 preguntas, seleccionadas de forma determinista y estratificada por categoría entre los 14 dominios.
- Split de desarrollo: `validation`, 70 preguntas; no se mezcla con train ni se usa para esta comparación.
- Dominios: biología, empresa, química, informática, economía, ingeniería, salud, historia, derecho, matemáticas, filosofía, física, psicología y otros.
- Fuente metodológica: Wang et al., *MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark* (NeurIPS 2024), https://arxiv.org/abs/2406.01574.

La ficha de Hugging Face declara MIT y documenta 12.032 elementos de test y 70 de validation. El conjunto incluye preguntas originales MMLU filtradas y preguntas procedentes de STEM, TheoremQA y SciBench. La licencia de la ficha se aplica al dataset distribuido; no debe inferirse que cada fuente subyacente tiene condiciones idénticas sin revisar su procedencia.

## Protocolo RONIN

Se fija la revisión y se calcula un SHA-256 determinista de los registros normalizados. Se seleccionan 140 preguntas mediante round-robin estratificado por categoría, con semilla 2026. El modelo responde zero-shot mediante la log-probabilidad del siguiente byte de la etiqueta A–J tras el enunciado y las opciones. No se suministran ejemplos, cadenas de razonamiento ni respuestas correctas al modelo.

**No es la puntuación oficial de MMLU-Pro**: no utiliza el protocolo CoT de referencia y no es comparable directamente con su leaderboard. Se informa accuracy global y por dominio, tamaño de muestra, IDs evaluados, cobertura, revisión y SHA-256 del dataset completo.

El evaluador no trunca preguntas. Para respetar el presupuesto de contexto del modelo tiny, se permite excluir preguntas cuyo prompt exceda 8.192 bytes. La comparación solo es válida si antes y después se evalúan exactamente los mismos IDs y se alcanza al menos el 95 % de cobertura de la muestra de 140 preguntas. Si no se cumple, no se considera una comparación válida.

## Separación y contaminación

- MMLU-Pro no forma parte del corpus de entrenamiento.
- El entrenamiento de este ciclo usa solo el split train documental legacy verificado (608 documentos) y parte del checkpoint main previo.
- El split test se usa exclusivamente para evaluación, nunca para gradientes.
- La muestra test se reserva para este ciclo; el uso repetido de resultados para seleccionar sucesivos checkpoints puede producir contaminación por selección. Por eso el workflow no promociona automáticamente el candidato.
- El checkpoint base se fija por run ID y SHA-256. El candidato se publica como artefacto separado; no reemplaza el modelo main por el mero hecho de que el workflow termine.

## Ejecución

Workflow: [main-cycle2-mmlu-pro.yml](../.github/workflows/main-cycle2-mmlu-pro.yml).

- Modelo base: RONIN tiny, 9.922.880 parámetros, checkpoint de RUN #42014728700.
- Entrenamiento: fine-tuning desde ese checkpoint, 1.000 pasos por defecto, learning rate 3e-5 y mínimo 3e-6.
- Evaluación: muestra externa de 140 preguntas estratificadas sobre MMLU-Pro test; contexto de inferencia 8.192 bytes; mismo conjunto de IDs antes y después; cobertura mínima del 95 %.
- Secundario: benchmark interno de 23 preguntas, siempre identificado como piloto pequeño.
