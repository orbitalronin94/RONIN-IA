# Experimento: RONIN-IA Fusion

Estado: propuesta técnica experimental. No sustituye el modelo de producción ni afirma que exista ya un modelo fusionado.

## Objetivo

Crear una variante de RONIN-IA con pesos derivados de modelos abiertos y evaluarla frente a Qwen3-0.6B. El objetivo no es solo cambiarle el nombre: buscamos mejoras medibles en español, instrucciones, razonamiento y uso local en Android.

## Regla fundamental de compatibilidad

No se deben promediar directamente pesos de modelos arbitrarios. Una fusión clásica necesita, como mínimo, arquitectura y claves de tensores compatibles, dimensiones iguales y un mapeo de tokens compatible; suele ser más fiable partir de checkpoints afinados desde el mismo modelo base. Que dos modelos sean «open source» no significa que sus pesos se puedan mezclar entre sí.

## Estrategia por fases

### Fase 0 — Congelar la referencia

- Mantener Qwen3-0.6B ONNX como modelo estable.
- Registrar revisión exacta, tokenizer, configuración, cuantización, licencia y hashes de los artefactos.
- Guardar una batería fija de prompts en español y una medición de tamaño, latencia y memoria.
- No reemplazar los pesos incluidos en la APK con resultados experimentales sin aprobación de las pruebas.

### Fase 1 — Seleccionar candidatos

Priorizar modelos de instrucciones o checkpoints afinados cuyo modelo base sea exactamente compatible con Qwen3-0.6B. Para cada candidato verificar:

- config.json: arquitectura, dimensiones ocultas, capas, cabezas y vocabulario.
- Tokenizer: archivos, vocabulario e IDs de tokens compatibles.
- Claves y formas de los tensores.
- Licencia del modelo base, del ajuste fino y de los archivos convertidos.
- Procedencia, revisión inmutable y requisitos de atribución.

Si no encontramos un segundo checkpoint realmente compatible y con licencia adecuada, no forzaremos la fusión. La alternativa es destilación o ajuste fino con datos autorizados, no mezclar tensores incompatibles.

### Fase 2 — Fusionar fuera del dispositivo

La fusión se realiza en un entorno de entrenamiento (por ejemplo, con MergeKit cuando los modelos sean compatibles), no en el teléfono. Probar primero una mezcla conservadora de dos checkpoints derivados del mismo origen y conservar siempre los originales. No incluir pesos experimentales de cientos de megabytes en Git; publicar artefactos versionados en un repositorio de modelos con sus hashes y ficha técnica.

### Fase 3 — Evaluación reproducible

Comparar el modelo base y cada candidato con los mismos prompts, parámetros y hardware:

- Calidad de respuestas en español y seguimiento de instrucciones.
- Alucinaciones, seguridad y resistencia a instrucciones maliciosas.
- Latencia de primera respuesta y tokens por segundo.
- RAM máxima, tamaño final y compatibilidad CPU/WebGPU/Android.
- Pruebas de regresión funcionales y al menos una evaluación humana ciega.

Aceptar la variante solo si mejora tareas objetivo sin regresiones inaceptables. Una fusión puede empeorar capacidades; no hay garantía de mejora.

### Fase 4 — Exportar e integrar

1. Exportar el checkpoint resultante a un formato compatible con Transformers.js/ONNX.
2. Validar tokenizer, generación y archivos de runtime.
3. Cuantizar después de validar el checkpoint fusionado; no intentar fusionar directamente los ONNX ya cuantizados de la APK.
4. Ejecutar pruebas de paridad y tamaño en CI.
5. Integrar la variante mediante configuración explícita y mantener una vía de vuelta al modelo estable.

## Criterios de aceptación

- Origen, revisión, licencias y hashes documentados.
- Fusión reproducible desde archivos de configuración versionados.
- Sin pérdida crítica frente a la referencia en el benchmark.
- Mejora demostrable en al menos una capacidad objetivo.
- Exportación ONNX válida y arranque local verificado.
- Prueba real en Android; el éxito de CI por sí solo no demuestra que la inferencia funcione sin conexión.

## Identidad y licencia

RONIN-IA puede ser el nombre del producto y de la variante experimental, pero una fusión de pesos preexistentes no convierte por sí sola el modelo en un modelo entrenado desde cero. La ficha pública debe indicar los modelos de origen, método, datos de ajuste cuando corresponda, licencias y limitaciones. Revisar por separado las licencias de los modelos, conversiones, datos y dependencias antes de distribuir.

## Referencias técnicas

- MergeKit y métodos de fusión: https://github.com/arcee-ai/mergekit
- Documentación sobre compatibilidad al fusionar modelos: https://www.sbert.net/docs/package_reference/base/model.html
- Qwen3: https://huggingface.co/Qwen/Qwen3-0.6B

## Próximo paso

Auditar candidatos concretos derivados de Qwen3-0.6B, comparar sus configuraciones y licencias, y elegir uno solo si pasa las comprobaciones de compatibilidad. Hasta entonces, el modelo estable de la aplicación no cambia.
