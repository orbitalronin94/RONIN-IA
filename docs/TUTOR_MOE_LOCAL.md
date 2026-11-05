# Tutor MoE local de RONIN

## Modelo fijado

- Modelo: [Qwen3-30B-A3B-GGUF](https://huggingface.co/Qwen/Qwen3-30B-A3B-GGUF)
- Cuantización: `Q4_K_M`, aproximadamente 18,6 GB.
- Parámetros: 30,5B totales; 3,3B activos por token; 128 expertos, 8 activados.
- Licencia declarada por el repositorio upstream: Apache-2.0.
- Runtime: Ollama con backend llama.cpp, CPU.
- Configuración versionada: `configs/local-tutor-qwen3-30b-a3b.json`.

No se guardan los pesos en Git: son demasiado grandes. El workflow los descarga a un directorio persistente del runner propio y Ollama los reutiliza en las siguientes ejecuciones.

## Requisito real de hardware

No confundir parámetros activos con tamaño de pesos. Aunque se activen unos 3,3B por token, el GGUF Q4 contiene los pesos de todos los expertos y ocupa alrededor de 18,6 GB. El workflow exige al menos 28 GiB de RAM disponible y 55 GiB de disco libre antes de descargar. No se ejecuta en runners hosted estándar ni degrada silenciosamente a un modelo pequeño.

Registrar un runner propio Linux x64 con la etiqueta adicional `ronin-32gb-cpu`. Después ejecutar manualmente **RONIN — tutor MoE local Qwen3 30B-A3B** desde GitHub Actions.

## Flujo de trabajo

1. Comprueba memoria y almacenamiento.
2. Instala Ollama y descarga `hf.co/Qwen/Qwen3-30B-A3B-GGUF:Q4_K_M`.
3. Ejecuta una inferencia de prueba forzada en CPU.
4. Opcionalmente lee un JSONL de prompts versionado y produce trazas JSONL con ID, prompt, respuesta, tiempos y contadores de tokens.
5. Publica manifiesto y trazas como artefacto de Actions.

Formato de entrada opcional, una línea por ejemplo:

```json
{"id":"ejemplo-001","prompt":"Explica por qué una prueba de regresión es necesaria."}
```

Las salidas del tutor quedan marcadas como `candidate_unreviewed`. **No son entrenables automáticamente**: requieren revisión, comprobación factual, procedencia y promoción explícita a una partición train admitida. El benchmark MMLU-Pro y cualquier split de evaluación quedan fuera de los prompts y de la generación.

## Ejecución

Workflow: [local-moe-tutor.yml](../.github/workflows/local-moe-tutor.yml)

El primer run descargará los pesos; los siguientes reutilizarán el directorio `OLLAMA_MODELS` persistente del runner. El manifiesto del artefacto debe conservar la revisión exacta de upstream y los datos de `ollama show` para auditoría. No declarar el tutor instalado hasta que el workflow termine con descarga y smoke test correctos.
