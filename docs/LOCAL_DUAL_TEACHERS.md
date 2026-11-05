# Tutores locales duales de RONIN

RONIN utilizará dos tutores descargados y ejecutados exclusivamente en el equipo del operador:

| Tutor | ID oficial | Licencia |
|---|---|---|
| Qwen3.6-27B Instruct | Qwen/Qwen3.6-27B | Apache-2.0 |
| DeepSeek-R1-Distill-Qwen-32B | deepseek-ai/DeepSeek-R1-Distill-Qwen-32B | MIT |

El nombre «Qwen3.6-27B-Instruct» identifica la variante instruct publicada oficialmente como Qwen/Qwen3.6-27B; el ID del repositorio no lleva el sufijo Instruct. La licencia Apache-2.0 de Qwen y la MIT de DeepSeek se verifican contra los metadatos de Hugging Face antes de descargar. Se fija el SHA de revisión y se calcula SHA-256 de cada archivo.

## Privacidad y separación de pesos

- No se usa ninguna API de inferencia externa.
- La inferencia carga los modelos desde disco con `local_files_only=True`.
- No se envían prompts, respuestas ni corpus privados a proveedores.
- Las descargas iniciales de los pesos y del benchmark público sí requieren conexión a sus repositorios.
- RONIN conserva inicialización aleatoria: no copia pesos, adaptadores ni estados del optimizador de los tutores.
- Las salidas generadas no heredan automáticamente la licencia de los modelos y no se publican como corpus redistribuible sin una revisión separada.

## Cuantización

El modo inicial es bitsandbytes NF4 de 4 bits. Se puede repetir el mismo experimento en 8 bits para comparar calidad y memoria. La cuantización se aplica en la máquina local al cargar los pesos; el descargador conserva los checkpoints safetensors originales y verifica sus hashes.

Los dos tutores se ejecutan **secuencialmente**, nunca a la vez en VRAM. El proceso genera primero las respuestas de Qwen, libera el modelo y la memoria CUDA, y después ejecuta DeepSeek sobre las mismas preguntas. Esto reduce la VRAM simultánea, pero no elimina la necesidad de almacenar ambos checkpoints en disco.

Como orientación, 4 bits es la primera configuración que debe probarse; 8 bits requiere aproximadamente el doble de memoria para los pesos. La memoria real también depende de arquitectura, contexto, caché KV, buffers y versión de CUDA. No se debe asumir que un modelo cabe por dividir el número de parámetros entre dos: hay que medir el pico real de VRAM. Se requiere GPU NVIDIA/CUDA para el flujo bitsandbytes de estos scripts.

## Instalación en la máquina de tutoría

Instala primero una versión de PyTorch compatible con el controlador CUDA de la máquina, siguiendo el selector oficial de PyTorch. Después:

```bash
python -m pip install -e .
python -m pip install --upgrade "transformers>=5.0" "accelerate>=1.0" "bitsandbytes>=0.45" "huggingface_hub>=0.36" "safetensors>=0.4" "datasets==3.6.0"
```

No instales el extra antiguo `.[teachers]` para este flujo: fija Transformers 4.53.3 por compatibilidad con Phi-4 y no es la base de dependencias de Qwen3.6.

## Descargar y verificar los dos modelos

```bash
python scripts/download_dual_teachers.py --model qwen3.6-27b
python scripts/download_dual_teachers.py --model deepseek-r1-distill-32b
```

Los modelos quedan en `models/teachers/`, excluidos del control de versiones. Cada carpeta contiene `ronin-teacher-manifest.json` con modelo, licencia, revisión inmutable e inventario SHA-256.

## Generar datos verificados y entrenar RONIN

Primera ejecución recomendada:

```bash
python scripts/train_from_local_dual_tutors.py --count 48 --quantization 4bit --steps 250 --device cuda
```

Para comparar 8 bits sin sobrescribir los resultados:

```bash
python scripts/train_from_local_dual_tutors.py --count 48 --quantization 8bit --steps 250 --device cuda --output-dir artifacts/dual-distillation-8bit --checkpoints checkpoints/dual-teacher-8bit
```

El script usa únicamente MMLU-Pro `validation` para la generación. Ningún tutor ve la respuesta correcta. Un ejemplo solo se admite si **los dos tutores responden la misma opción, ambos coinciden con la etiqueta gold independiente y ambos producen una explicación no vacía**. El acuerdo entre modelos, por sí solo, nunca es un oráculo. Si no se alcanza el mínimo de ejemplos aceptados, el proceso aborta antes de entrenar.

Después del filtro se escribe un JSONL de auditoría y un `train.txt` local. RONIN se inicializa desde cero y entrena con ese texto. El split `test` no se carga en la generación. La promoción del checkpoint sigue pendiente de una evaluación holdout separada; completar el entrenamiento no equivale a demostrar mejora.

## Pruebas de contrato

```bash
pytest -q tests/test_local_dual_teachers.py
ruff check ronin/data/local_dual_teacher.py scripts/download_dual_teachers.py scripts/distill_mmlu_pro_dual_tutor.py scripts/train_from_local_dual_tutors.py tests/test_local_dual_teachers.py
```

## Referencias oficiales

- Qwen: https://huggingface.co/Qwen/Qwen3.6-27B
- DeepSeek: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
