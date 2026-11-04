# Plan de comparación: Supra → RONIN

## Objetivo

Cuando termine la primera ejecución oficial de RONIN, generar una comparación reproducible entre su línea base (artefacto de Actions) y las 50 propuestas Supra. Esta fase **no modifica pesos, corpus ni el holdout**: produce un informe de priorización y prepara experimentos aislados posteriores.

## Referencias

- Ejecución base: [workflow oficial](../.github/workflows/ronin-official-training-holdout.yml), artefacto `ronin-official-full-mmlu-training-cycle`.
- Informe base esperado: `resumen-portfolio-mmlu.json`, con métricas inicial/final, por dominio, cobertura, omisiones, hashes y procedencia.
- Catálogo normalizado: [supra_specs.json](../data/manifests/supra_specs.json).
- Las 50 propuestas se conservan como hipótesis de ingeniería, no como evidencia de mejora.

## Protocolo de comparación

1. Esperar a que la primera ejecución oficial termine correctamente; no cancelarla ni lanzar otro entrenamiento simultáneo.
2. Descargar el artefacto de esa ejecución por su `run_id`, no usar el último artefacto disponible por nombre.
3. Validar que existan el resumen, la revisión fija de MMLU-Pro, el test esperado (12.032 ítems seleccionados), hashes iguales entre evaluación inicial/final y cobertura/omisiones explícitas.
4. Construir una matriz de las 50 propuestas: área, prerequisitos, estado de evidencia, riesgo de fuga/contaminación, coste de implementación y experimento/ablation requerido.
5. Separar tres familias:
   - **Observabilidad/evaluación:** ECE/MCE, reliability, cobertura-riesgo, slices, dimensiones, model card.
   - **Cambios de entrenamiento/arquitectura:** dual model, FEP, curriculum, replay, sleep/wake, lambda.
   - **Nuevos datos/protocolos:** D21–D24, textos sagrados, humanidades, ecología, ética.
6. Producir un informe Markdown y JSON como artefactos. No se acepta ninguna mejora por plausibilidad: cada propuesta requiere baseline comparable, test unitario, ablation aislada y evaluación externa no usada para ajustar.

## Reglas de admisión

- Citas marcadas [NV] quedan bloqueadas hasta verificar título, autores, fecha, DOI/ID y contenido. No entran en corpus ni bibliografía científica.
- Los textos protegidos no se descargan ni entrenan sin permiso/licencia de la edición y traducción concretas. Los abstracts/metadatos solo se usan según sus términos.
- Ningún corpus nuevo entra directamente en MMLU-Pro ni en el holdout actual. Se registra fuente, revisión, licencia, jurisdicción, hash y split por documento.
- No se ejecuta el test externo repetidamente para seleccionar hiperparámetros. La validación de desarrollo debe ser separada.
- Las heurísticas no se renombran como capacidades validadas: por ejemplo, `1 - delta_f` no es confianza calibrada; una keyword no demuestra willful blindness; divergencia no equivale por sí sola a incertidumbre epistémica.
- Bootstrap del test mide variabilidad de la muestra/evaluación, no robustez causal del modelo; los remuestreos no sustituyen un holdout independiente.

## Criterios para el primer lote

Prioridad inicial recomendada: #2, #21, #24, #25, #26, #27, #29, #30, #49. Primero auditar si ya existen componentes reutilizables y evitar duplicar métricas. Después #3, #22, #28 y #1. Los cambios de arquitectura/entrenamiento se mantienen como experimentos separados.

## Lectura del resultado

El informe no declarará que “Supra mejora RONIN” salvo que haya una comparación A/B controlada: misma inicialización/semillas, mismo presupuesto, misma mezcla aprobada, mismos datos de desarrollo y evaluación final sellada. Reportará deltas absolutos, incertidumbre, dominios, cobertura y regresiones. La ejecución base actual es de una semilla; por tanto, su comparación será exploratoria, no confirmatoria.

## Activación

El workflow `supra-comparative-audit.yml` se dispara solo al completarse correctamente el workflow oficial. También permite ejecución manual indicando explícitamente el run ID base. No entrena ni publica pesos.
