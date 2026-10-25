# Plan experimental: ampliar la comparación de modelos pequeños

**Fecha:** 2026-10-25  
**Estado:** plan de experimento; todavía no contiene resultados medidos.  
**Experimento:** comparación ampliada de candidatos pequeños de RONIN-IA.

## Pregunta

¿Puede un modelo más pequeño que Qwen2.5-0.5B ofrecer suficiente calidad para las tareas sintéticas de Ronin, y merece la pena comparar Qwen3-0.6B como candidato de generación más reciente?

## Candidatos y motivo

| Clave | Checkpoint evaluado en CPU | Artefacto de navegador relacionado | Motivo / riesgo |
|---|---|---|---|
| `qwen-0.5b` | `Qwen/Qwen2.5-0.5B-Instruct` | [Qwen2.5 ONNX](https://huggingface.co/onnx-community/Qwen2.5-0.5B-Instruct) | Línea base existente; mantener para comparar cambios en entorno y dataset. |
| `smollm2-360m` | `HuggingFaceTB/SmolLM2-360M-Instruct` | [SmolLM2-360M ONNX](https://huggingface.co/onnx-community/SmolLM2-360M-Instruct-ONNX) | Candidato de comparación anterior; sirve de control para la nueva ejecución. |
| `smollm2-135m` | `HuggingFaceTB/SmolLM2-135M-Instruct` | [SmolLM2-135M ONNX](https://huggingface.co/onnx-community/SmolLM2-135M-Instruct-ONNX) | Explorar el mínimo tamaño práctico; su model card advierte que se orienta principalmente al inglés. |
| `qwen3-0.6b` | `Qwen/Qwen3-0.6B` | [Qwen3-0.6B ONNX](https://huggingface.co/onnx-community/Qwen3-0.6B-ONNX) | Comparar la generación Qwen3. El evaluador desactiva el modo thinking en la plantilla para reducir una diferencia de configuración frente a respuestas directas. |

El benchmark CPU usa checkpoints PyTorch en float32. No se deben interpretar sus medidas de latencia como mediciones de los artefactos ONNX de navegador.

## Protocolo fijado

- Dataset: `benchmarks/model-eval-prompts.jsonl` (12 prompts sintéticos, español e inglés).
- Límite de generación: 96 tokens nuevos.
- Decodificación: greedy/determinista (`do_sample=False`).
- Entorno: GitHub Actions, Ubuntu, PyTorch CPU, float32.
- Scorer: `scripts/score_model_eval.py`.
- Qwen3: se pasa `enable_thinking=False` a la plantilla de chat y el archivo de predicciones registra `thinking_mode`.
- Artefactos: informe JSON y predicciones JSONL por candidato, con retención de 30 días.
- Pesos: se descargan solo en el workflow de evaluación; nunca se guardan en Git ni se añaden al build normal.
- Pruebas del scorer: ejecutar antes de inferencia.

## Métricas a registrar

1. Número de predicciones recibidas y casos faltantes.
2. Exactitud automática sobre casos deterministas, con desglose por categoría.
3. Casos marcados para revisión humana, sin sumarlos a exactitud automática.
4. Mediana, mínimo y máximo de latencia de generación, además del tiempo de arranque si aparece en las predicciones.
5. Errores, respuestas vacías, salidas truncadas y problemas de compatibilidad.

## Limitaciones conocidas

- Doce prompts son una muestra exploratoria; cada caso determinista pesa mucho en el resultado.
- Coincidencia exacta puede penalizar respuestas semánticamente correctas con texto extra o puntuación final.
- La calidad de SmolLM2-135M en español es incierta y debe evaluarse directamente.
- Qwen3 se evalúa con el modo thinking desactivado, por lo que el resultado no describe su configuración de razonamiento por defecto.
- El workflow no mide WebGPU, WASM, Android, memoria pico ni descarga fría de los artefactos ONNX.
- El experimento no decide qué modelo será el predeterminado.

## Criterios para la siguiente decisión

- Si falla la carga o no produce todas las predicciones, investigar compatibilidad antes de comparar puntuaciones.
- Revisar manualmente los casos abiertos con la misma rúbrica y sin conocer el modelo cuando sea posible.
- No promover un candidato por una sola puntuación. Exigir después una prueba del artefacto exacto en navegador/Android, registrando tamaño descargado, backend, memoria y latencia.
- Mantener Qwen2.5 como baseline y conservar el modo remoto como predeterminado hasta disponer de evidencia suficiente.

## Fuentes de modelos

- Qwen3-0.6B: https://huggingface.co/Qwen/Qwen3-0.6B
- Qwen3-0.6B ONNX: https://huggingface.co/onnx-community/Qwen3-0.6B-ONNX
- SmolLM2-135M-Instruct: https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct
- SmolLM2-135M-Instruct ONNX: https://huggingface.co/onnx-community/SmolLM2-135M-Instruct-ONNX

## Resultado

**Pendiente.** Este documento registra el diseño y los límites antes de ejecutar el experimento; no contiene resultados inventados. Tras la ejecución se debe añadir un informe separado con el SHA del commit, enlace al workflow, IDs de artefactos, métricas medidas y análisis de predicciones.
