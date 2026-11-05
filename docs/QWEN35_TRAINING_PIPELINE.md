# Entrenamiento principal RONIN — Qwen3.5-4B

## Decisión de modelo

El pipeline experimental principal usa un único modelo: unsloth/Qwen3.5-4B.

- Método: SFT de continuación de texto con LoRA en BF16 (FP16 si la GPU no soporta BF16).
- No se usa QLoRA de 4 bits: la guía actual de Unsloth desaconseja QLoRA para Qwen3.5 por las diferencias de cuantización.
- Perfil inicial: contexto 2.048, microbatch 1, acumulación 8, 1.000 pasos.
- El adaptador se guarda por separado; no se suben pesos ni datos privados a GitHub.
- No se descargan ni ejecutan modelos tutores. Solo hay un modelo en esta línea.

## Corpus de arranque

El único corpus documental admitido en el catálogo al 5-11-2026 es admitted/literature-es-v1, con 608 documentos y particiones separadas. El workflow .github/workflows/qwen35-prepare-corpus.yml recupera el artefacto ronin-admitted-literature-es-v1-train del run fijado 41926088900, comprueba UTF-8, tamaño y SHA-256, y publica ronin-qwen35-admitted-corpus-v1.

Los candidatos de las otras bibliotecas no se mezclan hasta superar sus gates de derechos, privacidad, calidad y partición. No se incorporan validation/test al entrenamiento.

## Pipeline

1. GitHub Actions prepara y publica el artefacto de corpus con manifiesto y SHA-256.
2. Abrir el notebook Colab enlazado abajo y seleccionar una GPU T4 si está disponible.
3. Descargar el artefacto de corpus desde la ejecución del workflow y subir el ZIP al notebook.
4. El notebook instala Unsloth/Transformers v5 y ejecuta scripts/train_qwen35_unsloth.py.
5. El script evalúa el modelo base y el adaptado sobre la misma muestra estratificada de MMLU-Pro validation (nunca test), entrena 1.000 pasos y guarda adaptador, métricas y manifiesto.
6. Descargar el ZIP de resultados y adjuntarlo a una ejecución de auditoría/promoción posterior. El checkpoint es candidato; no se promueve solo porque la loss baje.

## Ejecutar en Colab

Notebook: https://colab.research.google.com/github/orbitalronin94/RONIN-IA/blob/main/notebooks/ronin_qwen35_4b_training.ipynb

En Colab: Runtime → Change runtime type → GPU. La GPU gratuita no está garantizada; Colab ajusta disponibilidad y límites dinámicamente. El notebook detecta CUDA y aborta si no hay GPU.

## Ejecución reproducible fuera de Colab

Con una GPU CUDA compatible y el corpus preparado:

    pip install --upgrade unsloth unsloth_zoo datasets "transformers>=5" trl
    python scripts/train_qwen35_unsloth.py \
      --train-file artifacts/qwen35-corpus/train.txt \
      --steps 1000 \
      --max-seq-length 2048 \
      --eval-limit 140 \
      --output-dir outputs/ronin-qwen35-4b

## Métricas y límites

- La pérdida de entrenamiento no demuestra mejora de razonamiento.
- MMLU-Pro validation se usa como señal de desarrollo, no como test final.
- El test MMLU-Pro permanece intacto para una evaluación final independiente.
- El protocolo de evaluación de este pipeline usa generación greedy y extracción de una letra final; no es la puntuación oficial del leaderboard MMLU-Pro.
- Si validation no mejora, el adaptador no se promociona. Si mejora, sigue siendo candidato hasta pasar la evaluación final independiente.
- El acceso gratuito a GPU Colab no es permanente ni garantizado.
