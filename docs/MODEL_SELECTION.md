# Selección de modelos pequeños para Ronin

Estado: shortlist inicial para evaluar; **no es un ranking definitivo ni una decisión de sustitución**. Fecha de revisión: 2026-10-25.

## Objetivo y restricciones

Elegir un modelo instruct pequeño que dé buen resultado en español y tareas cotidianas, que se pueda ejecutar en navegador/Android, que no infle la APK y que tenga licencia compatible con el uso previsto.

No descargar modelos en CI normal, no guardar pesos en Git y no entrenar/fusionar antes de medir una línea base.

## Shortlist priorizada para pruebas

| Prioridad | Modelo / artefacto | Evidencia publicada | Encaje en Ronin | Riesgos / siguiente paso |
|---|---|---|---|---|
| A — baseline | [Qwen2.5-0.5B-Instruct (ONNX)](https://huggingface.co/onnx-community/Qwen2.5-0.5B-Instruct) | Model card de Qwen informa 0.49B parámetros y resultados en matemáticas/código/IFEval; Apache-2.0 para el modelo base. | Ya integrado con Transformers.js. ONNX `q4f16` ~483 MB; `q4` ~786 MB según archivos publicados. | Mantener como referencia, no asumir que es el mejor. Medir WebGPU/WASM, memoria y español en un dispositivo real. |
| B — comparación directa | [SmolLM2-360M-Instruct (ONNX)](https://huggingface.co/onnx-community/SmolLM2-360M-Instruct-ONNX) | SmolLM2 publica comparaciones con Qwen2.5-0.5B: mejora en varias pruebas de conocimiento/IFEval; Qwen supera en algunas pruebas matemáticas y MT-Bench. | Apache-2.0 y familia de 360M; artefacto ONNX para Transformers.js, con `q4f16` ~272 MB y `q4` ~386 MB listados en el repositorio ONNX. | Buena alternativa para reducir descarga; validar plantilla de chat, calidad en español y runtime real. Los benchmarks publicados no son una comparación específica de nuestro uso. |
| C — investigación, no integrar aún | [LFM2-350M](https://huggingface.co/LiquidAI/LFM2-350M) | Liquid AI publica resultados propios competitivos para el tamaño, incluidos MMLU/IFEval/GSM8K. | Diseñado para edge y tamaño compacto. | No dar por hecho compatibilidad con el runtime Transformers.js/ONNX actual. Verificar licencia LFM Open License v1.0, disponibilidad de formato y restricciones antes de invertir en integración. |

### Lectura correcta de los números

- No mezclar resultados de distintas versiones, datasets, shots, plantillas o evaluadores como si fueran una clasificación común.
- Los resultados del creador son evidencia inicial, no verificación independiente.
- Los benchmarks ingleses no sustituyen pruebas en español.
- El tamaño del archivo no equivale a RAM máxima ni predice por sí solo velocidad o calidad.
- Una variante cuantizada puede cambiar la calidad y el consumo; registrar siempre el artefacto y la cuantización exactos.

Fuentes principales:
- Qwen2.5: https://qwenlm.github.io/blog/qwen2.5-llm/
- Qwen2.5-0.5B-Instruct model card: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct
- SmolLM2-360M-Instruct model card y benchmarks: https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct
- SmolLM2 ONNX para Transformers.js: https://huggingface.co/onnx-community/SmolLM2-360M-Instruct-ONNX
- LFM2-350M model card: https://huggingface.co/LiquidAI/LFM2-350M

## Protocolo de evaluación de Ronin

### 1. Filtro de viabilidad (antes de comparar calidad)
1. Licencia y términos del artefacto exacto documentados.
2. Existe formato compatible con el runtime elegido y se conoce el tamaño de descarga.
3. La carga y una generación corta funcionan en Android/WebView real.
4. No se empaquetan pesos en la APK ni se descargan durante el build.
5. Registrar navegador/WebView, dispositivo, RAM disponible, backend (WebGPU/WASM), versión del runtime y cuantización.

### 2. Conjunto pequeño, versionado y sin datos privados

Crear/usar un conjunto fijo de prompts de evaluación en español e inglés, versionado en el repo. Cubrir al menos:
- seguir instrucciones y respetar formato;
- resumen breve y reescritura;
- comprensión y preguntas sobre el texto aportado;
- matemáticas básicas con respuesta verificable;
- razonamiento cotidiano;
- código sencillo con tests deterministas;
- rechazo de instrucciones inseguras y manejo de incertidumbre;
- español natural, no solo traducción literal.

Usar ejemplos propios y sintéticos, sin datos personales ni texto de benchmark con licencia dudosa. No usar los prompts de entrenamiento como evaluación final.

### 3. Métricas obligatorias por candidato

- calidad: exactitud en tareas verificables y rúbrica humana ciega para respuestas abiertas;
- tasa de salida vacía/error y cumplimiento de formato;
- tiempo hasta primer token y tokens/s, con 3 repeticiones después de una ejecución de calentamiento;
- tamaño descargado, tiempo de descarga en red declarada y caché fría/caliente;
- pico de memoria si el dispositivo permite medirlo, cierres y fallos;
- estabilidad de resultados y limitaciones observadas.

Publicar CSV/JSON de resultados como artefacto de Actions; no commitear pesos ni volcados grandes.

### 4. Regla de decisión

No cambiar el modelo por una única puntuación agregada. Primero exigir que cargue y responda de forma estable en el dispositivo objetivo. Después comparar calidad en español, latencia, memoria y descarga. Un modelo más pequeño solo gana si la pérdida de calidad es aceptable para el uso real. Conservar Qwen como baseline hasta que un candidato lo supere de forma medible.

## Qué significa “modelo propio”

Integrar o ajustar pesos abiertos no convierte automáticamente a Ronin en un modelo preentrenado desde cero. Primero establecer baseline y evaluación reproducible; después decidir si procede un ajuste fino con datos permitidos. No hacer fusiones de pesos sin hipótesis y evaluación antes/después.
