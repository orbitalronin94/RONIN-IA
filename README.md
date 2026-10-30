# Ronin IA

> Asistente experimental ligero para web y Android. Esta versión prioriza arrancar rápido, una APK pequeña y una ruta de IA remota intercambiable.

## Estado actual

- Interfaz web empaquetada con Capacitor para Android.
- Respuestas generativas mediante un endpoint público experimental compatible con OpenAI.
- Modo local opt-in con un candidato Qwen3-0.6B DQ-ONNX (repositorio publicado de ~370 MB; pesos ONNX ~356 MB) y fallback al Qwen2.5-0.5B-Instruct anterior.
- Herramientas deterministas locales para cálculos sencillos y utilidades web.
- Historial local, enrutamiento de prompts y pruebas automatizadas.
- GitHub Actions construye una APK de depuración; el artefacto no es una release firmada.

**Importante:** el modo remoto usa un servicio público experimental y depende de su conexión/cuota. El modo local procesa los mensajes en el dispositivo; la primera carga descarga el modelo y el runtime cuando se usa el navegador compatible. En el build Android offline, los pesos deben estar presentes en los assets locales. El router de expertos es lógica de aplicación, no una red neuronal MoE.

## Decisión de peso y velocidad

La APK no debe incluir pesos de modelos ni descargar varios modelos durante cada build.

- No se empaquetan modelos ONNX en la APK normal.
- No se descargan pesos durante el build Android normal.
- El modo local es opt-in mediante el botón **IA local**; los pesos se descargan bajo demanda en entornos que permiten modelos remotos.
- El candidato Qwen3-0.6B DQ-ONNX se ha elegido inicialmente por su huella publicada inferior a 400 MB y compatibilidad con Transformers.js. Todavía no es un ganador medido: debe superar un benchmark de razonamiento y rendimiento frente al fallback.
- En navegador, si Qwen3 no está disponible, el runtime intenta Qwen2.5-0.5B-Instruct como fallback. El APK offline no lleva ese fallback para respetar el límite de tamaño.
- Los pesos, checkpoints, cachés y resultados grandes permanecen fuera del historial Git.

## Ejecutar y probar

Requisitos: Node.js 20 y npm.

```bash
npm install
npm test
```

Para compilar el APK desde GitHub, abre **Actions → Build Ronin IA APK → Run workflow**. El artefacto es una APK de depuración, no una release firmada.

## Ruta del modelo Ronin

1. Mantener Qwen3-0.6B DQ-ONNX como candidato local inicial (<400 MB publicado).
2. Compararlo con el modelo anterior mediante tareas fijas de razonamiento, COBOL, código, seguimiento de instrucciones y robustez.
3. Medir calidad, latencia, memoria y tamaño descargado en dispositivos reales.
4. Incorporar únicamente datasets revisados y con procedencia/licencia verificadas.
5. Adaptar pesos solo después de congelar una línea base y reservar un holdout independiente.
6. Evaluar cualquier adaptador o fusión frente al modelo base; no asumir que mezclar pesos mejora el resultado.

Una adaptación de pesos existentes no es preentrenamiento desde cero. Los pesos cuantizados para inferencia no sustituyen a un checkpoint entrenable para LoRA/QLoRA.

## Integración con Agent-Eval

Agent-Eval genera datasets trazables, propuestas de anotación y evaluaciones reproducibles. Ronin IA podrá consumir versiones aprobadas; no debe importar automáticamente propuestas sin revisar ni usar el holdout para entrenamiento o selección de prompts.

El catálogo del modelo está en `models/catalog.json`. La propuesta de pipeline COBOL está en [Agent-Eval](https://github.com/orbitalronin94/Agent-Eval/tree/main/datasets/cobol2py/PIPELINE.md).

## Privacidad y seguridad

El historial de chat se conserva localmente en el dispositivo. En modo remoto, las consultas se envían al proveedor remoto experimental. En modo local, los mensajes se procesan en el dispositivo, aunque la primera carga puede descargar pesos desde Hugging Face y el runtime desde CDN. No se incluyen claves personales ni secretos en la aplicación.

## Limitaciones

- El endpoint público puede cambiar, limitar peticiones o dejar de estar disponible.
- El modo local puede ir lento o fallar en dispositivos con poca RAM; WebGPU no está disponible en todos los WebViews.
- Qwen3-0.6B es pequeño: sus respuestas pueden ser débiles o incorrectas y requieren evaluación.
- El tamaño publicado del repositorio no equivale a memoria RAM total; también cuentan runtime, KV cache y buffers.
- El build de APK no valida el rendimiento en un dispositivo Android físico.
- La selección de modelos y las puntuaciones preliminares no demuestran superioridad; hacen falta benchmarks comparables.


### Reproducible under-400MB model comparison

\`.github/workflows/quantized-model-candidate-compare.yml\` compares Qwen3-0.6B DQ-ONNX, SmolLM2-360M Q4F16 and SmolLM2-135M Q4F16 using the same Spanish reasoning and COBOL semantics prompts. It measures the files actually downloaded, cold start, RSS and latency, and reports exact-match accuracy and reasoning accuracy per MB. COBOL target outputs are checked against GnuCOBOL before scoring.

The first candidate is not promoted until the workflow passes and the comparison is reviewed. The Node CPU run is a screening measurement, not an Android/WebGPU performance claim.

### Dataset synchronization

\`.github/workflows/sync-agent-eval-datasets.yml\` checks Agent-Eval's curated approval manifest weekly and opens an integration PR when approved train/dev data changes. It refuses holdout, model proposals, non-MIT sources and unverified records. The sync is PR-based; it does not auto-merge datasets or weights.
