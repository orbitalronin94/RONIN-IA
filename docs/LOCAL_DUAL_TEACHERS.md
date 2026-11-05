# Tutores locales duales de RONIN

RONIN utilizará dos tutores descargados y ejecutados exclusivamente en el equipo del operador:

- Qwen3.6-27B: repositorio oficial Qwen/Qwen3.6-27B, licencia Apache-2.0.
- DeepSeek-R1-Distill-Qwen-32B: repositorio oficial deepseek-ai/DeepSeek-R1-Distill-Qwen-32B, licencia MIT.

La cuantización objetivo es bitsandbytes NF4 de 4 bits como configuración inicial; 8 bits será una comparación de calidad/coste de memoria. La cuantización se aplica localmente al cargar los pesos. No se llama a APIs de inferencia externas y no se envían prompts ni corpus a terceros.

Los dos tutores contestan al mismo conjunto de preguntas. Solo las respuestas que superen un oráculo independiente (por ejemplo, la clave gold de MMLU-Pro validation) pueden entrar automáticamente en el corpus de entrenamiento. El acuerdo entre tutores no constituye por sí solo verificación.

RONIN conserva su inicialización aleatoria: no copia pesos, adaptadores ni estados del optimizador de los tutores. Las salidas no heredan automáticamente la licencia del modelo y no se publican como corpus redistribuible sin una revisión separada.

Los modelos se ejecutan secuencialmente para permitir que ambos quepan en una sola GPU: primero se generan y guardan las respuestas de Qwen; después se libera la memoria y se ejecuta DeepSeek sobre exactamente los mismos ejemplos. El estudiante se entrena después con los ejemplos aceptados.

## Modelos oficiales

- https://huggingface.co/Qwen/Qwen3.6-27B
- https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B

El nombre «Qwen3.6-27B-Instruct» se refiere al modelo instruct publicado como Qwen/Qwen3.6-27B; el ID oficial no lleva el sufijo Instruct.
