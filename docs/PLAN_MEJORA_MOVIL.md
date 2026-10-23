# Plan de mejora integral de Ronin IA

> Estado: propuesta técnica priorizada. Las métricas no se consideran verificadas hasta ejecutarlas en dispositivos físicos. Actualizado: 2026-10-23.

## Objetivo
Convertir Ronin IA en una aplicación Android/web sólida, rápida, accesible, modular y auditable. Se permite que el repositorio crezca si cada dependencia aporta una mejora verificable.

## Principios
1. **Medir antes de elegir:** estrellas y benchmarks de terceros no sustituyen pruebas reproducibles propias.
2. **Separar UI e inferencia:** la interfaz habla con un proveedor común, no directamente con un runtime.
3. **Degradación elegante:** explicar fallos de WebGPU, memoria o red sin bloquear las funciones disponibles.
4. **Privacidad explícita:** distinguir inferencia local, descarga de modelos y consultas que salen a servicios externos.
5. **Seguridad por defecto:** no insertar HTML arbitrario, no usar `eval`, validar enlaces y limitar historial/contexto/salida.
6. **Dependencias justificadas:** cada dependencia nueva necesita propósito, pruebas y documentación de mantenimiento.
7. **Comentarios útiles:** explicar razones y compromisos; no repetir en comentarios lo que la sintaxis ya dice.

## Runtimes candidatos

| Tecnología | Uso | Ventaja | Coste/riesgo | Decisión |
|---|---|---|---|---|
| Transformers.js + ONNX Runtime | Web/WebView | Integración web sencilla, carga bajo demanda | Compatibilidad WebGPU/WASM variable | Mantener baseline |
| LiteRT-LM | Android nativo | Backends móviles y posible aceleración GPU/NPU | Integración y cobertura por dispositivo | Prototipo aislado |
| llama.cpp | Android nativo/GGUF | Modelos cuantizados y control de CPU/GPU | JNI/NDK, empaquetado, consumo y licencias a revisar | Prototipo si lo justifican las métricas |
| MLC LLM | Android/WebGPU | Runtime compilado orientado a GPU | Compilación y compatibilidad complejas | Comparar, no incluir aún |
| WebLLM | WebGPU | API tipo chat en navegador | Requiere WebGPU compatible | Comparar con Transformers.js |
| ExecuTorch | Android nativo | Runtime móvil y varios backends | Exportación y compatibilidad de modelos | Comparar primero con LiteRT-LM |
| sherpa-onnx / whisper.cpp | Voz offline | STT/TTS/VAD locales | Modelos adicionales, batería, tamaño y permisos | Módulo opcional posterior |

Fuentes de proyecto:
- https://github.com/huggingface/transformers.js
- https://github.com/mlc-ai/web-llm
- https://github.com/google-ai-edge/LiteRT-LM
- https://github.com/google-ai-edge/LiteRT
- https://github.com/ggml-org/llama.cpp
- https://github.com/mlc-ai/mlc-llm
- https://github.com/pytorch/executorch
- https://github.com/huggingface/optimum-executorch
- https://github.com/k2-fsa/sherpa-onnx
- https://github.com/ggml-org/whisper.cpp
- https://github.com/AI-with-Andrew/awesome-mobile-llm

Los benchmarks publicados por autores de un runtime son referencias, no comparaciones neutrales. No comparar números de dispositivos, cuantizaciones, prompts o contextos diferentes como si fueran una sola prueba.

## Modelos candidatos
- **Qwen3-0.6B ONNX:** baseline actual; capacidad limitada, pero permite medir una ruta web local.
- **SmolLM2-135M:** candidato ligero para medir latencia y calidad modesta.
- **Llama 3.2 1B:** candidato intermedio; verificar licencia, formato y memoria antes de adoptarlo.
- **Gemma 3 1B:** candidato según soporte del runtime y artefacto; verificar licencia y requisitos.
No cambiar de modelo por un benchmark aislado: usar el mismo conjunto de prompts en español.

## Inicio del modelo en Android

La APK ahora intenta preparar Qwen3 al iniciar, después de pintar la interfaz. La primera ejecución requiere conexión y espacio para descargar los pesos; Transformers.js está configurado para usar la caché del navegador cuando el WebView la permita. La web fuera de Android conserva carga bajo demanda para evitar consumo inesperado de datos. **Esto no significa que los pesos estén empaquetados dentro del APK**. La inclusión real de pesos requiere medir el tamaño, validar el formato/runtime y probar instalación/actualización en dispositivos físicos.

## Arquitectura objetivo

```text
UI / accesibilidad / historial
            |
      ChatController
            |
     InferenceProvider
       /     |      \
  WebONNX  Native   Remote (opcional, consentimiento explícito)
            |
  métricas / límites / cancelación
```

La ruta remota, si se implementa, debe ser explícita y no activarse por defecto.

## Hoja de ruta

### P0 — base fiable
- [ ] Reparar y reforzar la validación JS en CI.
- [ ] Añadir pruebas de escape HTML, Markdown permitido, historial corrupto y cálculos.
- [ ] Usar lockfile y `npm ci` para instalaciones reproducibles.
- [ ] Limitar historial, contexto, salida y tamaño de descargas.
- [ ] Mejorar estados, errores de red y reintentos.
- [ ] Probar accesibilidad, teclado, lector de pantalla y movimiento reducido.
- [ ] No publicar APK si fallan las pruebas previas.

### P1 — medición y experiencia
- [ ] Medir inicio de UI, descarga, carga de runtime, primer token y tokens/s.
- [ ] Diferenciar visualmente respuestas del modelo, herramientas locales y servicios externos.
- [ ] Añadir cancelar/reintentar cuando el runtime lo permita.
- [ ] Permitir borrar historial y explicar que se guarda localmente.
- [ ] Crear 30–50 prompts fijos en español para instrucciones, matemáticas, código y abstención.
- [ ] Registrar errores sin capturar contenido privado de conversaciones.

### P2 — modularización
- [ ] Separar `www/index.html` en CSS, UI, almacenamiento, herramientas y proveedores.
- [ ] Definir `InferenceProvider.load/generate/cancel/dispose/getCapabilities`.
- [ ] Añadir pruebas de contrato para cada proveedor.
- [ ] Mantener la misma UI y seleccionar el runtime mediante configuración explícita.

### P3 — comparar motores
- [ ] Comparar Transformers.js/WebGPU, Transformers.js/WASM y un prototipo nativo (LiteRT-LM o llama.cpp, uno inicialmente).
- [ ] Probar gama baja, media y alta; al menos cinco repeticiones tras calentamiento.
- [ ] Registrar modelo/hash, cuantización, runtime, Android, WebView, RAM, conectividad y condiciones térmicas.
- [ ] Comparar p50/p95 de primer token, tokens/s, memoria pico, errores, tamaño y calidad humana.
- [ ] Adoptar otro motor solo si mejora los objetivos sin regresión grave de estabilidad o mantenimiento.

### P4 — módulos opcionales
- [ ] Voz offline con sherpa-onnx o whisper.cpp, con modelos descargables y permisos justificados.
- [ ] RAG local solo después de medir utilidad, espacio y privacidad.
- [ ] Exportar/importar historial con advertencias de privacidad.
- [ ] Preparar release firmado, SBOM y revisión de licencias.

## Protocolo de benchmark
1. Medir tiempo de primera pantalla en frío.
2. Medir descarga e inicialización por separado, tanto en frío como en caché.
3. Usar prompts fijos de longitud controlada y medir primer token/tokens por segundo.
4. Probar preguntas cortas/largas y contexto nuevo/acumulado.
5. Repetir en CPU y acelerador cuando ambos estén disponibles.
6. Registrar errores, cierres por memoria, batería aproximada y temperatura.
7. Puntuar corrección, seguimiento de instrucciones, español, utilidad y alucinaciones.
8. Publicar configuración y resultados brutos, incluidas pruebas fallidas.

## Criterios de aceptación
- La UI aparece sin esperar al modelo.
- Un fallo de inferencia no bloquea el historial.
- Nunca se ejecuta HTML arbitrario del modelo.
- Historial corrupto no impide abrir la app.
- Las consultas externas se identifican y sus fallos se comunican.
- El APK se asocia a un commit y pasa pruebas de sintaxis.
- Cada nuevo runtime tiene prueba reproducible, revisión de licencia y ruta de retirada.

## Política de comentarios por archivo
- `www/index.html`: documentar subsistemas, decisiones de seguridad/performance y funciones no obvias.
- `package.json` y `capacitor.config.json`: JSON no admite comentarios; documentar motivos aquí y en `docs/DECISIONES.md`.
- `.github/workflows/*.yml`: explicar por qué existe cada etapa y qué garantiza/no garantiza.
- `docs/*.md`: separar evidencia, supuestos, decisiones y tareas.
- SVG: describir grupos visuales y accesibilidad.
- Nuevos módulos: encabezado con propósito, límites, dependencias e invariantes.

Las fuentes y notas ampliadas se mantienen en [REFERENCIAS_OPEN_SOURCE.md](./REFERENCIAS_OPEN_SOURCE.md). Revisar licencias y compatibilidad antes de distribuir, porque cambian con las versiones.
