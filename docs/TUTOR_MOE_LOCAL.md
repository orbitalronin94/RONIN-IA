# Tutor MoE local de RONIN

## Checkpoint

- Modelo: [Qwen3-30B-A3B-GGUF](https://huggingface.co/Qwen/Qwen3-30B-A3B-GGUF)
- Archivo: `Qwen3-30B-A3B-Q4_K_M.gguf` (18,56 GB aprox.).
- Parámetros: 30,5B totales; 3,3B activos/token; 128 expertos, 8 activos.
- Licencia upstream: Apache-2.0.
- Inferencia: `llama.cpp` CLI, CPU. **No se utiliza Ollama.**

Cuando se ejecute correctamente en el runner propio, el GGUF se descargará la primera vez a `${runner.tool_cache}/ronin-checkpoints/qwen3-30b-a3b-q4km`. El diseño conserva el archivo en el almacenamiento persistente del runner y lo reutiliza en ejecuciones posteriores. Hasta que una ejecución satisfactoria registre tamaño y SHA-256, no debe afirmarse que ya está descargado. Cada ejecución calcula y publica SHA-256. No se comitea un binario de 18,56 GB en Git ni se depende de la retención temporal de Actions artifacts para los pesos.

## Infraestructura

Runner propio Linux x64 con etiqueta `ronin-32gb-cpu`, al menos 28 GiB de RAM disponible y 55 GiB de disco libre. Los 3,3B activos no reducen el tamaño almacenado: todos los pesos del MoE deben estar disponibles. El workflow falla explícitamente si el runner no cumple los mínimos.

## Pipeline: 100 pasos

1. Comprueba RAM y disco.
2. Descarga el GGUF solo si no existe el checkpoint local.
3. Compila `llama.cpp` para CPU y ejecuta un smoke test usando directamente el archivo GGUF.
4. Opcionalmente genera un máximo de **100 trazas** (un prompt por paso) mediante el CLI.
5. Guarda manifiesto, SHA-256, trazas y tiempos en un artifact de Actions.

Entrada JSONL opcional, una línea por ejemplo:

```json
{"id":"ejemplo-001","prompt":"Explica por qué una prueba de regresión es necesaria."}
```

Las trazas se etiquetan `candidate_unreviewed`: no se incorporan automáticamente al corpus ni a gradientes. Exigen revisión factual, procedencia y promoción explícita. MMLU-Pro y los splits de evaluación quedan fuera.

Workflow: [local-moe-tutor.yml](../.github/workflows/local-moe-tutor.yml)
