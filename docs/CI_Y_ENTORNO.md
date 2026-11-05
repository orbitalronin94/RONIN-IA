# CI y entorno de ejecución

Actualizado: 5 de noviembre de 2026.

## Entorno

- Runner Linux x64: `ubuntu-26.04` explícito. No depender de la migración gradual de `ubuntu-latest`.
- Python: 3.11, mantenido de forma deliberada hasta validar una matriz más nueva con PyTorch y los checkpoints actuales.
- Acciones: checkout v7, setup-python v7, download-artifact v8 y upload-artifact v7.
- Las acciones actuales usan Node.js 24; los runners hospedados de GitHub ya cumplen el runtime requerido.

## Coste de instalación

Los jobs Python deben activar `cache: pip` en `actions/setup-python`. El caché conserva wheels y descargas de pip entre ejecuciones compatibles; no sustituye la resolución de dependencias ni garantiza versiones reproducibles.

## Presupuesto de CPU

Los runners estándar Linux x64 de GitHub disponen de 2 vCPU. Los experimentos CPU deben evitar lanzar más procesos de entrenamiento concurrentes que núcleos disponibles, salvo que un benchmark demuestre una mejora. El torneo de semillas usa dos workers y un hilo PyTorch por worker.

## Checkpoints

El formato versionado de MAIN es un contenedor con `model`, `step`, `profile` y metadatos. Los validadores deben cargar `payload["model"]` (o aceptar explícitamente un state_dict plano cuando proceda). La promoción debe conservar el contenedor y actualizar el manifiesto de forma atómica.

## Política de actualización

No se cambia de versión de Python, PyTorch o dependencias de benchmark solo por perseguir la versión más nueva. Primero se valida compatibilidad, checkpoint round-trip, smoke training, tests y el holdout emparejado.
