# Modelos auxiliares locales y generación de corpus

RONIN aprende siempre desde una inicialización aleatoria. Los tutores solo aportan texto; sus pesos nunca se copian al estudiante.

## Modelos admitidos

| Alias | Repositorio | Licencia declarada |
|---|---|---|
| gpt2 | https://huggingface.co/openai-community/gpt2 | MIT |
| gpt-neo-125m | https://huggingface.co/EleutherAI/gpt-neo-125m | MIT |

El descargador vuelve a consultar los metadatos y cancela si la licencia no es exactamente mit. Fija una revisión inmutable y calcula SHA-256 de los archivos.

Ambos modelos son principalmente anglófonos. No se debe presuponer que generarán buen castellano. Sus textos requieren revisión humana, filtrado, deduplicación y comprobación de derechos.

## Descargar una vez en el equipo local

    python -m pip install -e '.[teachers]'
    python scripts/download_teacher_models.py --model gpt2
    python scripts/download_teacher_models.py --model gpt-neo-125m

Los pesos y manifiestos quedan en models/teachers/, excluido de Git. Las generaciones posteriores pueden cargarlos desde disco sin repetir la descarga.

## Caché de GitHub Actions

El workflow manual «Preparar caché de tutores locales» descarga y verifica ambos modelos en un runner público y guarda models/teachers/ en la caché de Actions. Se ejecuta desde la pestaña Actions. Las siguientes ejecuciones pueden restaurarla; GitHub puede desalojar cachés antiguas por sus políticas de retención, así que el descargador siempre debe poder reconstruirlas.

La caché acelera trabajos de Actions; no copia los modelos al ordenador local del operador. Los pesos no se versionan ni se publican como artefactos.

## Generación local

Ejemplo con GPT-2:

    python scripts/generate_teacher_data.py --model-dir models/teachers/gpt2 --count 40 --device auto --max-new-tokens 192 --output artifacts/teacher/gpt2.jsonl

El dispositivo auto utiliza CUDA si está disponible y CPU en caso contrario. Los registros generados deben revisarse antes de entrenar.

## Separación tutor-estudiante

- Los pesos del tutor solo se cargan en el proceso generador.
- RONIN se construye con inicialización aleatoria.
- El entrenador solo recibe texto tokenizado.
- No se realiza fine-tuning, fusión ni destilación de parámetros.
