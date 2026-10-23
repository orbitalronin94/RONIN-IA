# Investigación de proyectos open source de IA

> Revisión de referencias públicas para orientar la arquitectura de Ronin IA. Consultado el 23 de octubre de 2026. Esta selección es cualitativa, no un benchmark independiente de rendimiento.

## Criterios

1. Encaje con web y Android de recursos limitados.
2. Licencia y documentación visibles.
3. Capacidad de ejecutar localmente o integrar motores alternativos.
4. Coste de mantenimiento y complejidad que añade al producto.
5. Posibilidad de medir la mejora en dispositivos reales.

## Referencias

### Transformers.js — runtime web

- Proyecto: https://github.com/huggingface/transformers.js
- Documentación: https://huggingface.co/docs/transformers.js/en/index
- Aporta: ejecución de tareas de ML en el navegador usando ONNX Runtime; soporte opcional de WebGPU y cuantizaciones como q4/q8 según el modelo.
- Aplicación a Ronin: mantener la carga bajo demanda, cachear los artefactos y tratar WebGPU como aceleración opcional, nunca como requisito universal.
- Riesgo: compatibilidad y rendimiento cambian según el navegador/WebView, modelo y operador ONNX.

### Qwen3 — familia de modelos

- Proyecto: https://github.com/QwenLM/Qwen3
- Aporta: varios tamaños y rutas de inferencia local, con documentación de despliegue y cuantización.
- Aplicación a Ronin: usar Qwen3-0.6B como línea base móvil, medir su calidad real en español y comparar modelos mayores solo con un presupuesto de RAM y latencia definido.
- Riesgo: un modelo pequeño puede fallar en tareas complejas; la interfaz no puede compensar las limitaciones del modelo subyacente.

### Ollama — experiencia de ejecución local

- Proyecto: https://github.com/ollama/ollama
- Aporta: flujo sencillo para ejecutar modelos y una API compatible con OpenAI.
- Aplicación a Ronin: referencia para una futura configuración de proveedor remoto/local en escritorio o LAN.
- Decisión: no añadir Ollama como dependencia de Android, porque necesita un runtime/servicio adicional y no es la ruta ligera actual.

### Open WebUI — interfaz extensible

- Proyecto: https://github.com/open-webui/open-webui
- Documentación: https://docs.openwebui.com/
- Aporta: conversaciones, historial, herramientas, extensibilidad y soporte de varios proveedores.
- Aplicación a Ronin: inspirarse en la claridad del flujo de chat y en el desacoplamiento entre interfaz y motor.
- Decisión: mantener la interfaz propia y pequeña; incorporar una plataforma grande aumentaría el coste de empaquetado y mantenimiento.

### llama.cpp — inferencia nativa

- Proyecto: https://github.com/ggml-org/llama.cpp
- Aporta: inferencia cuantizada GGUF con rutas CPU/GPU y amplia variedad de hardware.
- Aplicación a Ronin: candidato para estudiar una integración nativa Android si las pruebas revelan que la ruta WebGPU/WASM no cumple objetivos.
- Decisión: no cambiar todavía. Un segundo motor añade código nativo, licencias y complejidad de compilación; primero se necesita un benchmark reproducible.

## Plan de evaluación

Registrar en al menos tres dispositivos Android de capacidades diferentes:

- Tiempo hasta mostrar la primera pantalla.
- Tiempo de descarga e inicialización del modelo, por separado.
- Tiempo hasta el primer token y tokens por segundo.
- Memoria máxima aproximada y fallos por falta de memoria.
- Calidad de respuestas en un conjunto fijo de preguntas en español, matemáticas y código.
- Comportamiento con WebGPU disponible y con CPU/WASM.
- Tamaño de descarga y consumo de datos.

Cada prueba debe anotar el modelo exacto, cuantización, versión del runtime, navegador/WebView, dispositivo y conectividad. No presentar estrellas de GitHub ni una compilación CI exitosa como evidencia de calidad o velocidad.

## Decisión actual

Conservar **Capacitor + interfaz web ligera + Transformers.js + Qwen3-0.6B** como base experimental. Priorizar seguridad de renderizado, manejo de errores, accesibilidad, pruebas automatizadas y medición. Solo sustituir el runtime o aumentar el modelo cuando los datos medidos justifiquen el coste.

## Fuentes consultadas

- Transformers.js: https://huggingface.co/docs/transformers.js/en/index
- Qwen3: https://github.com/QwenLM/Qwen3
- Ollama: https://github.com/ollama/ollama
- Open WebUI: https://docs.openwebui.com/
- llama.cpp: https://github.com/ggml-org/llama.cpp
