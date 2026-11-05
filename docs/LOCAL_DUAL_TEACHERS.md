# Tutores locales duales de RONIN

RONIN utilizará dos tutores cuantizados, descargados y ejecutados exclusivamente en el equipo del operador:

| Tutor | Modelo base oficial | Cuantización local GGUF |
|---|---|---|
| Qwen3.6-27B Instruct | Qwen/Qwen3.6-27B · Apache-2.0 | Q4_K_M (4-bit) o Q8_0 (8-bit) |
| DeepSeek-R1-Distill-Qwen-32B | deepseek-ai/DeepSeek-R1-Distill-Qwen-32B · MIT | Q4_K_M (4-bit) o Q8_0 (8-bit) |

El ID oficial de Qwen no lleva el sufijo Instruct. La variante publicada como Qwen3.6-27B es el modelo instruct. Las cuantizaciones GGUF se descargan desde ggml-org (Qwen) y bartowski (DeepSeek), y se contrasta su ficha con el modelo base oficial. El manifiesto local registra ambas revisiones, la licencia original y el SHA-256 del archivo cuantizado.

## Privacidad y separación de pesos

- No se usa ningún proveedor ni API de inferencia externa.
- llama.cpp se ejecuta como proceso local enlazado exclusivamente a `127.0.0.1`. La interfaz HTTP es loopback: las peticiones no salen del equipo.
- Los prompts, respuestas, corpus y checkpoints de RONIN no se suben a GitHub Actions ni a proveedores.
- La descarga inicial de los GGUF y del benchmark público requiere conexión a Hugging Face.
- RONIN conserva su inicialización aleatoria: no copia pesos, adaptadores ni estados del optimizador de los tutores.
- Las salidas no heredan automáticamente la licencia de los modelos y no se publican como corpus redistribuible sin una revisión separada.

## Cuantización y recursos

Se recomienda empezar por Q4_K_M. Q8_0 conserva más precisión y necesita bastante más almacenamiento y memoria. Como orientación publicada, Qwen Q4_K_M ronda 19 GB y Q8_0 28,6 GB; DeepSeek Q4_K_M ronda 19,9 GB y Q8_0 34,8 GB. Reserva al menos unos 45 GB para los dos GGUF Q4 y unos 70 GB para los dos Q8, además del espacio de trabajo y checkpoints.

La memoria de ejecución depende del contexto, KV cache, buffers y capas descargadas a GPU. llama.cpp permite repartir capas entre GPU y RAM. El valor predeterminado del runner local es 99 capas GPU; para CPU-only se puede definir `RONIN_LLAMA_GPU_LAYERS=0`. El contexto inicial se limita a 4096 tokens para el currículo MMLU-Pro.

## Instalar llama.cpp

Qwen3.6 requiere una versión reciente de llama.cpp con soporte para la arquitectura Qwen3.5/Qwen3.6. Usa el commit `f9cd456` o uno posterior:

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
git checkout f9cd456
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j --target llama-server
```

Añade `llama.cpp/build/bin` al PATH para que RONIN encuentre `llama-server`. Si la máquina no usa CUDA, compila sin `-DGGML_CUDA=ON` y configura `RONIN_LLAMA_GPU_LAYERS=0`.

Instala el paquete RONIN, PyTorch adecuado al hardware y el cliente de descarga/evaluación:

```bash
python -m pip install -e .
python -m pip install --upgrade "huggingface_hub>=0.36" "datasets==3.6.0"
```

## Descargar los dos modelos cuantizados

Para Q4_K_M:

```bash
python scripts/download_dual_teachers.py --model qwen3.6-27b --quantization 4bit
python scripts/download_dual_teachers.py --model deepseek-r1-distill-32b --quantization 4bit
```

Para Q8_0, repite con `--quantization 8bit`. Los modelos quedan en `models/teachers/`, excluidos de Git. Cada descarga verifica la licencia del modelo base, que la ficha del GGUF identifica el modelo de origen y el hash del archivo descargado.

## Generar ejemplos verificados y entrenar RONIN

Primera ejecución recomendada:

```bash
python scripts/train_from_local_dual_tutors.py --count 48 --quantization 4bit --steps 250 --device cuda
```

Para comparar 8 bits sin sobrescribir resultados:

```bash
python scripts/train_from_local_dual_tutors.py --count 48 --quantization 8bit --steps 250 --device cuda --output-dir artifacts/dual-distillation-8bit --checkpoints checkpoints/dual-teacher-8bit
```

Los dos tutores se ejecutan **secuencialmente**, nunca a la vez. El proceso levanta llama.cpp en loopback para Qwen, guarda sus respuestas, apaga el servidor y después repite con DeepSeek. En la segunda ronda, RONIN pregunta «¿por qué?» y cada tutor recibe su respuesta inicial y la propuesta del otro; debe contrastar premisas, regla decisiva y un contraejemplo, y puede corregirse. Después se libera y vuelve a cargar cada modelo para su turno de contraste. El puerto local se asigna dinámicamente y el servidor se cierra al terminar cada turno.

El generador usa únicamente MMLU-Pro `validation`. Ningún tutor ve la respuesta correcta. Un ejemplo solo se admite si, **después del contraste socrático, los dos tutores responden la misma opción, ambos coinciden con la etiqueta gold independiente y ambos producen una explicación no vacía**. El acuerdo entre modelos no es por sí solo un oráculo. El JSONL de auditoría conserva las respuestas iniciales y finales, pero no almacena cadenas privadas de pensamiento. Si no se alcanza el mínimo de ejemplos aceptados, se aborta antes de entrenar.

El JSONL de auditoría y `train.txt` permanecen locales. RONIN se inicializa desde cero y entrena con el texto admitido. El split `test` no se carga durante la generación. Completar el entrenamiento no equivale a demostrar mejora: la promoción del checkpoint queda pendiente de una evaluación holdout independiente.

## Pruebas de contrato

```bash
pytest -q tests/test_local_dual_teachers.py
ruff check ronin/data/local_dual_teacher.py scripts/download_dual_teachers.py scripts/distill_mmlu_pro_dual_tutor.py scripts/train_from_local_dual_tutors.py tests/test_local_dual_teachers.py
```

## Fuentes oficiales y cuantizaciones

- Modelo Qwen: https://huggingface.co/Qwen/Qwen3.6-27B
- GGUF Qwen: https://huggingface.co/ggml-org/Qwen3.6-27B-GGUF
- Modelo DeepSeek: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
- GGUF DeepSeek: https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-32B-GGUF
