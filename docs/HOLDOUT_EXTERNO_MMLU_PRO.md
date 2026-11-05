# Holdout externo RONIN: MMLU-Pro

## Fuente y derechos

- Dataset: [TIGER-Lab/MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro)
- Licencia declarada por el repositorio del dataset: MIT.
- Revisión inmutable: `b189ec765aa7ed75c8acfea42df31fdae71f97be`.
- Split reservado: `test`, 12.032 preguntas.
- Split de desarrollo: `validation`, 70 preguntas; no se mezcla con train.
- Cobertura temática: 14 dominios (biología, empresa, química, informática, economía, ingeniería, salud, historia, derecho, matemáticas, filosofía, física, psicología y otros).
- Fuente metodológica: Wang et al., *MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark* (2024), https://arxiv.org/abs/2406.01574.

La ficha oficial de Hugging Face declara MIT y documenta 12.032 elementos de test y 70 de validation. El conjunto reúne preguntas originales MMLU filtradas y preguntas de STEM, TheoremQA y SciBench. La licencia de la ficha se aplica al dataset distribuido; no debe inferirse que cada fuente externa subyacente o los modelos entrenados con datos de terceros tienen idénticas condiciones sin revisar su procedencia.

## Protocolo RONIN

Se fija la revisión y se calcula un hash determinista de los registros normalizados. El modelo responde en zero-shot mediante la log-probabilidad del siguiente byte de la etiqueta A–J tras el enunciado y las opciones. No se suministran ejemplos, cadenas de razonamiento ni respuestas correctas al modelo.

**No es la puntuación oficial de MMLU-Pro**: no utiliza el protocolo CoT de referencia y no es comparable directamente con el leaderboard. Se informa accuracy, resultados por dominio, número de preguntas evaluadas, preguntas omitidas por contexto, cobertura, revisión y SHA-256 del dataset.

El test no se usa para gradientes. Para cada ciclo se ejecuta la misma evaluación completa antes y después. Las preguntas que excedan el contexto no se truncan: el workflow exige cobertura completa; si no se consigue, la ejecución queda incompleta y no produce una comparación válida.

## Separación y contaminación

- MMLU-Pro no forma parte del corpus de entrenamiento.
- El entrenamiento de este ciclo usa solo el split train documental legacy verificado (608 documentos) y parte del checkpoint main previo.
- No se descarga ni se utiliza el split test para optimizar pesos.
- El uso repetido de resultados del test para seleccionar sucesivos checkpoints puede producir contaminación por selección. Por eso el workflow no promociona automáticamente el candidato: publica la evidencia y deja la decisión de promoción para revisión explícita.
- El checkpoint base se fija por run ID y SHA-256. El candidato se publica como artefacto separado; no reemplaza el modelo main por el mero hecho de que el workflow termine.

## Ejecución

Workflow: [main-cycle2-mmlu-pro.yml](../.github/workflows/main-cycle2-mmlu-pro.yml).

- Modelo base: RONIN tiny, 9.922.880 parámetros, checkpoint de RUN #42014728700.
- Entrenamiento: fine-tuning de pesos desde ese checkpoint, 1.000 pasos por defecto, learning rate 3e-5 y mínimo 3e-6.
- Evaluación: MMLU-Pro test completo (12.032 preguntas) antes y después, revisión fijada, contexto 4.096 y control de cobertura.
- Secundario: benchmark interno de 23 preguntas, siempre identificado como piloto pequeño.
