# Decisión de tutor y siguiente ciclo de RoninLM

Fecha: 2026-11-05

## Tutor elegido

Tutor único inicial: **Qwen/Qwen3-8B**, ejecutado localmente con llama.cpp y GGUF Q4_K_M.

- Modelo base: https://huggingface.co/Qwen/Qwen3-8B
- GGUF oficial: https://huggingface.co/Qwen/Qwen3-8B-GGUF
- Licencia declarada: Apache-2.0.
- Archivo Q4_K_M esperado: `qwen3-8b-q4_k_m.gguf`.
- Descarga y verificación: `python scripts/download_dual_teachers.py --model qwen3-8b --quantization 4bit`.
- El manifiesto registra revisiones, licencia y SHA-256. No se importan los pesos del tutor al estudiante.

La elección prioriza razonamiento, instrucciones multilingües y viabilidad de ejecución local cuantizada. En runners CPU la generación será lenta; el primer ciclo debe medir tiempo real, memoria y tasa de aceptación antes de ampliar el volumen.

## Destilación controlada

El nuevo flujo de tutor único es:

1. Muestrear ejemplos del split `train` de MMLU-Pro.
2. Pedir respuesta y justificación breve y verificable; no pedir ni conservar cadenas privadas de pensamiento.
3. Contrastar la respuesta con la etiqueta gold independiente.
4. Admitir únicamente respuestas correctas que incluyan una justificación breve.
5. Entrenar RoninLM con el corpus aceptado.
6. Evaluar en MMLU-Pro `validation`; no cargar `test` durante iteraciones.
7. No promover automáticamente. Comparar con el checkpoint de main y conservar el candidato solo si mejora las métricas acordadas.

Scripts:
- `scripts/distill_mmlu_pro_single_tutor.py`
- `scripts/train_from_local_single_tutor.py`

## Las 64 bibliotecas

La intención de entrenamiento es incorporar las 64 bibliotecas (32 dominios × General/HKD) a una mezcla común, sin excluir dominios por conveniencia. Sin embargo, el inventario actual `data/datasets/libraries/manifest-64.json` declara:

- 64 slots catalogados.
- 0 documentos Level A admitidos.
- 0 bytes Level A admitidos.
- 0/64 bibliotecas training-eligible.
- G-0 global: FAIL.

Por tanto, **no se deben tratar los 64 directorios de catálogo como corpus entrenables**: hoy son slots documentados, no bibliotecas con payloads admitidos. La única colección con texto legado separada es `data/datasets/admitted/literature-es-v1`, cuyo manifiesto registra 608 documentos de train (140.295.523 bytes), 18 de validation y 18 de test. Su estado legal territorial está pendiente de reconciliación con el inventario Level A; no se incorporará automáticamente a una nueva mezcla sin resolver esa condición.

Regla de inclusión futura:
- incluir todas las bibliotecas que alcancen estado admitted + training-eligible;
- exigir evidencia de licencia por obra/versión, procedencia, privacidad, calidad, hashes y deduplicación;
- mantener General/HKD disjuntas;
- crear splits por documento y grupo de duplicados;
- nunca mezclar validation/test/holdout con train;
- mantener G-0 como gate obligatorio. No se rebaja el gate para acelerar el entrenamiento.

## Próximo hito operativo

Antes de lanzar una ejecución larga:
1. Ejecutar descarga/verificación de Qwen3-8B Q4_K_M en un runner y medir RAM/tiempo de inferencia.
2. Ejecutar una muestra pequeña de destilación con el filtro gold.
3. Verificar que la evaluación de desarrollo usa validation y que test no se descarga.
4. Terminar admisión documental de las bibliotecas; solo entonces habilitar la mezcla global de las 64.
5. Comparar el checkpoint candidato con main y registrar métricas, artefactos y hashes.

El entrenamiento sintético anterior fue una prueba del bucle de optimización; no acredita aprendizaje documental.
