# Hoja de ruta de RONIN

Esta hoja de ruta define hitos de ingeniería verificables. No promete que todas las capacidades estén implementadas.

## Fase 0: base inicial (actual)

- [x] Paquete Python y flujo CI
- [x] Transformer decoder-only compartido
- [x] Inicialización aleatoria y embeddings compartidos
- [x] Tokenizador de bytes para tiny
- [x] Muestreador determinista de lotes de siguiente token
- [x] Optimizador y bucle de entrenamiento compartidos, con acumulación, recorte, planificación y selección de precisión
- [x] Guardado atómico de checkpoints periódicos
- [x] Registro de capacidades e informe de preparación basado en evidencias
- [x] Generación básica y utilidades de métricas de evaluación
- [ ] Ejecutar CI y corregir todos los fallos
- [x] Descargador de tutores locales con comprobación de licencia MIT
- [x] Generación de texto local con trazabilidad de modelo y revisión
- [ ] Prueba integral de entrenamiento con un corpus aprobado

## Fase 1: datos y evaluación

- [ ] Esquema de manifiesto de corpus y validación de licencias
- [ ] Deduplicación exacta y aproximada
- [ ] Separación determinista de entrenamiento/validación/prueba por origen/documento
- [ ] Fragmentación, pesos de mezcla y entrenamiento del tokenizador
- [ ] Bucle de validación e informes de perplejidad y BPB
- [ ] Suite de regresión de generación y controles de filtraciones

## Fase 2: seed-0

- [ ] Validar el recuento real de parámetros frente al perfil objetivo
- [ ] Medir memoria máxima y tokens por segundo en la GPU de destino
- [ ] Añadir reanudación exacta de checkpoint, estado aleatorio y estado del planificador
- [ ] Añadir diagnósticos de picos de pérdida y rotación de checkpoints
- [ ] Ejecutar solo cuando exista corpus aprobado y adecuación de hardware medida

## Fase 3: seed-1 y seed-2

- [ ] Entrenamiento distribuido y pruebas de comunicación
- [ ] Fragmentación de estados del optimizador cuando sea necesaria
- [ ] Checkpointing de activaciones y atención eficiente
- [ ] Recuperación multinodo y seguimiento de experimentos
- [ ] Benchmarks con datos reservados y evaluación humana

## Criterio de publicación

Una fase solo se completa cuando se han comprometido la implementación, las pruebas, las evidencias de CI, los comandos reproducibles y un informe escrito de resultados. Nunca se marca una casilla por el mero hecho de declararla en un manifiesto.
