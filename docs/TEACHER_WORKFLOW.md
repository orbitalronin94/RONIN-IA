# Modelos auxiliares locales y generación de corpus

Esta guía descarga modelos auxiliares gratuitos con licencia MIT, los ejecuta localmente para generar texto y prepara ese texto para entrenar RONIN. El estudiante RONIN siempre parte de una inicialización aleatoria.

## Modelos admitidos inicialmente

El descargador contiene una lista permitida de dos modelos:

| Alias | Repositorio | Licencia declarada | Uso previsto |
|---|---|---|---|
| `gpt2` | [openai-community/gpt2](https://huggingface.co/openai-community/gpt2) | MIT | Prueba de generación local |
| `gpt-neo-125m` | [EleutherAI/gpt-neo-125m](https://huggingface.co/EleutherAI/gpt-neo-125m) | MIT | Comparación de un segundo tutor |

La ficha pública de cada repositorio declara la licencia MIT. El script no se fía únicamente de esta documentación: consulta de nuevo los metadatos al descargar y cancela la operación si la licencia no es exactamente `mit`. También fija el identificador de revisión y calcula SHA-256 de los archivos descargados.

**Limitación lingüística importante:** ambos modelos se entrenaron principalmente con texto en inglés. No son tutores competentes en castellano por defecto. En esta primera etapa se utilizan para verificar que el circuito de descarga, ejecución local, generación y trazabilidad funciona. Las respuestas deben revisarse y filtrarse; no se deben incorporar automáticamente a un corpus de calidad.

La licencia MIT del modelo no convierte en MIT sus datos de entrenamiento ni garantiza los derechos de cada texto generado. La procedencia y la legalidad del corpus deben evaluarse por separado.

## Instalación

```bash
python -m pip install -e '.[teachers]'
```

## Descargar los modelos una sola vez

```bash
python scripts/download_teacher_models.py --model gpt2
python scripts/download_teacher_models.py --model gpt-neo-125m
```

Los pesos y el manifiesto quedan en:

```text
models/teachers/gpt2/
models/teachers/gpt-neo-125m/
```

El manifiesto `ronin-teacher-manifest.json` contiene el identificador del modelo, la revisión fijada, la licencia verificada, la fecha de comprobación y las huellas SHA-256. El código carga desde el directorio local con `local_files_only=True`; la generación no necesita una API remota.

No se deben subir a Git los pesos descargados ni los corpus generados. La carpeta `models/teachers/` es un artefacto local.

## Generar datos con un tutor

Ejemplo con GPT-2:

```bash
python scripts/generate_teacher_data.py \
  --model-dir models/teachers/gpt2 \
  --count 40 \
  --device auto \
  --max-new-tokens 192 \
  --output artifacts/teacher/gpt2.jsonl
```

Ejemplo con GPT-Neo:

```bash
python scripts/generate_teacher_data.py \
  --model-dir models/teachers/gpt-neo-125m \
  --count 40 \
  --device auto \
  --max-new-tokens 192 \
  --output artifacts/teacher/gpt-neo.jsonl
```

El dispositivo `auto` utiliza CUDA si está disponible y CPU en caso contrario. La primera carga y la inferencia local pueden ser más lentas en CPU; una vez descargados, los modelos se reutilizan sin repetir la descarga.

Cada registro JSONL incluye prompt, respuesta, modelo, revisión, licencia, fecha, SHA-256, indicación de que el tutor se ejecutó localmente y confirmación explícita de que los pesos del tutor no se importaron al estudiante.

## Preparar el corpus y entrenar RONIN

La preparación del corpus comprueba la procedencia y la huella de cada registro:

```bash
python scripts/prepare_teacher_corpus.py \
  --input artifacts/teacher/gpt2.jsonl \
  --output artifacts/teacher/gpt2-corpus.txt

python scripts/train_text.py \
  --text artifacts/teacher/gpt2-corpus.txt \
  --profile tiny \
  --steps 5 \
  --device cpu
```

Para comparar tutores, generar dos corpus independientes y mantenerlos identificados. No mezclar resultados ni corpus sin registrar qué modelo los produjo.

## Separación estricta entre tutor y estudiante

- Los pesos del tutor se descargan y cargan solo en el proceso generador de datos.
- RONIN se construye con inicialización aleatoria.
- El entrenador de RONIN solo recibe texto tokenizado; no recibe el estado de pesos del tutor.
- No se realiza fine-tuning, fusión ni destilación de parámetros.
- El texto generado debe someterse a revisión humana, control de calidad, deduplicación y comprobación de derechos antes de entrenar.

## Límites de esta primera etapa

- Los dos tutores iniciales son anglófonos; el castellano generado puede ser deficiente.
- El corpus curricular es pequeño y determinista.
- El objetivo actual es predecir el siguiente byte/token en texto formateado; no es un ajuste supervisado de instrucciones completo.
- Todavía no existe una separación independiente de validación y prueba para este flujo.
- La pérdida de entrenamiento no es una métrica de generalización.
- Antes de hacer afirmaciones sobre calidad se necesitan datos con licencia clara, revisión factual humana, deduplicación, controles de contaminación y evaluación reservada.
