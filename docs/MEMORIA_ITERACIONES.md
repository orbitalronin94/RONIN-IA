# Memoria de iteraciones — RONIN-IA

> **Propósito:** mantener una memoria técnica acumulativa de las iteraciones, decisiones, pruebas, resultados y pendientes del proyecto. Registrar hechos verificables y separar claramente los resultados confirmados de las tareas en curso o las hipótesis.
>
> **Última actualización:** 2026-10-23 (UTC).  
> **Estado general:** auditoría de candidatos correcta; APK de depuración compilada correctamente; evaluación profunda de modelos en curso. No se ha demostrado todavía una fusión de modelos válida ni una mejora de calidad.

## Índice

- [Reglas de mantenimiento](#reglas-de-mantenimiento)
- [Objetivos de trabajo](#objetivos-de-trabajo)
- [Registro de iteraciones](#registro-de-iteraciones)
- [Estado de las comprobaciones](#estado-de-las-comprobaciones)
- [Evaluación de modelos](#evaluación-de-modelos)
- [Decisiones técnicas](#decisiones-técnicas)
- [Pendientes y criterios de cierre](#pendientes-y-criterios-de-cierre)
- [Enlaces de seguimiento](#enlaces-de-seguimiento)

## Reglas de mantenimiento

1. Añadir una entrada después de cada iteración relevante: cambios de código, pruebas, ejecuciones de CI, análisis de modelos, compilaciones o decisiones.
2. Anotar fecha UTC, SHA de commit si se conoce, archivos afectados, motivo, resultado comprobado y próximos pasos.
3. No presentar una ejecución en curso como terminada ni una auditoría de metadatos como prueba de compatibilidad o calidad.
4. Registrar los fallos y las correcciones, no solo los éxitos. Mantener los resultados históricos aunque una iteración posterior los corrija.
5. Cuando una ejecución finalice, añadir el enlace al workflow y resumir su conclusión y artefactos.
6. No afirmar que se ha fusionado o validado un modelo si no existe un artefacto reproducible y una evaluación comparativa que lo respalde.

## Objetivos de trabajo

- Auditar 24 repositorios candidatos relacionados con Qwen3-0.6B.
- Revisar configuración, archivos de pesos, formas/nombres de tensores y vocabulario/tokenizador.
- Evaluar los modelos con prompts de prueba y registrar fallos de descarga, carga o inferencia.
- Comparar el modelo base y cualquier candidato o modelo fusionado con pruebas reproducibles.
- Construir la aplicación Android y verificar los tests y el artefacto APK.
- Documentar limitaciones, incompatibilidades y pasos para reproducir los resultados.

## Registro de iteraciones

### 2026-10-23 — Iteración 1: auditoría de pesos y cobertura de candidatos

**Commit:** [96f8add](https://github.com/orbitalronin94/RONIN-IA/commit/96f8addfcee4cca65082dafe7a25656f8210e816)

**Cambios**
- El detector de archivos de pesos excluye checkpoints auxiliares de entrenamiento, como `optimizer.pt`, `optimizer.bin`, `rng_state.pth`, `scaler.pt`, `scheduler.pt`, `training_args.bin` y `trainer_state.json`.
- El informe de auditoría incorpora cobertura: total de candidatos, candidatos auditados, elegibles para la siguiente etapa y excluidos/incompletos.
- Los errores específicos de un candidato se registran como hallazgos; los fallos fatales se reservan para problemas de infraestructura o del modelo base.

**Motivo:** evitar que archivos auxiliares de entrenamiento se confundan con pesos del modelo y que un candidato incompleto impida revisar el resto.

**Resultado:** cambio incorporado. La ejecución de auditoría de este commit falló posteriormente por una prueba que aún esperaba cuatro modelos en vez de 24; no se considera una validación exitosa de esa iteración.

### 2026-10-23 — Iteración 2: actualización de pruebas del detector

**Commit:** [96345b3](https://github.com/orbitalronin94/RONIN-IA/commit/96345b3d5f18aab42dc97c4f2bc455ff9ed3d29d)

**Cambios**
- Se añadieron aserciones para asegurar que los archivos auxiliares de entrenamiento no se detectan como pesos.

**Resultado observado:** la ejecución de CI encontró una prueba desactualizada: esperaba cuatro modelos, pero la lista actual contiene 24. El resto de esa ejecución no debe interpretarse como validación completa.

### 2026-10-23 — Iteración 3: pruebas alineadas con los 24 candidatos

**Commit:** [8e92cc5](https://github.com/orbitalronin94/RONIN-IA/commit/8e92cc53a160e67f4d3efe0cffc50b3fc6e00d8b)

**Cambios**
- La prueba de cobertura se renombró para reflejar todos los modelos.
- La aserción del número de modelos se actualizó de 4 a 24.
- Se mantiene el conjunto de nueve casos de prompts para el benchmark heurístico.

**Resultado:** corrección incorporada. La evaluación profunda iniciada con este SHA sigue siendo la ejecución que se está vigilando; revisar su conclusión antes de dar por validado el benchmark.

### 2026-10-23 — Iteración 4: filtros de CI y auditoría completa

**Commit:** [ef0ff49](https://github.com/orbitalronin94/RONIN-IA/commit/ef0ff4984bf3979d94b5cac09a6ce1ccc4b617b4)

**Cambios**
- El workflow de auditoría se dispara también cuando cambian `scripts/benchmark_fusion.py` y `tests/test_benchmark_fusion.py`.
- Se actualizaron los textos del workflow para indicar que se auditan los 24 repositorios y que los fallos específicos de candidatos no deben confundirse con fallos de infraestructura.

**Resultados de CI comprobados en la última consulta**
- Auditoría, ejecución **39995711599**: **éxito**. Los tests offline, la auditoría de candidatos y la publicación del informe terminaron correctamente.
- APK Android, ejecución **39995711424**: **éxito**. Pasaron los contratos del frontend, la validación de sintaxis JavaScript, el empaquetado del runtime de inferencia, la descarga de pesos Qwen3, la sincronización de Capacitor y `assembleDebug`. Se publicó el artefacto `ronin-ia-debug-apk`.
- Evaluación profunda, ejecución **39995671249**: **en curso** en la última consulta. Los tests offline pasaron; la evaluación de modelos, formas de tensores y prompts en español estaba ejecutándose. Aún no se había publicado el informe final.

## Estado de las comprobaciones

| Área | Estado conocido | Evidencia / notas |
|---|---|---|
| Tests offline de auditoría | Correctos en la última ejecución | Workflow 39995711599 |
| Auditoría de candidatos | Correcta | Workflow 39995711599; artefacto `ronin-fusion-audit` |
| Compilación Android debug | Correcta | Workflow 39995711424; artefacto `ronin-ia-debug-apk` |
| Evaluación profunda de modelos | En curso en la última consulta | Workflow 39995671249 |
| Compatibilidad real para fusionar | Pendiente de demostrar | Requiere evidencia por candidato |
| Comparativa base vs. modelo fusionado | Pendiente | No se debe inventar ningún resultado |
| Modelo fusionado validado | No confirmado | No consta un artefacto de fusión validado |

## Evaluación de modelos

La lista de trabajo contiene 24 repositorios candidatos:

1. `Qwen/Qwen3-0.6B` — modelo base.
2. `andresnowak/Qwen3-0.6B-instruction-finetuned_v2`
3. `rohitnagareddy/Qwen3-0.6B-Coding-Finetuned-v1`
4. `kurakurai/Luth-0.6B-Instruct`
5. `suayptalha/Qwen3-0.6B-Math-Expert`
6. `suayptalha/Qwen3-0.6B-Code-Expert`
7. `suayptalha/Qwen3-0.6B-IF-Expert`
8. `suayptalha/Qwen3-0.6B-Medical-Expert`
9. `rohitnagareddy/Qwen3-0.6B-Medical-Finetuned-v1`
10. `x32/Qwen3-0.6B-GRPO-GSM8K-Think`
11. `huihui-ai/Huihui-Qwen3-0.6B-abliterated-v2`
12. `lunahr/Qwen3-0.6B-abliterated`
13. `codelion/Qwen3-0.6B-PTS-DPO`
14. `jeehwon/Qwen3-0.6B-Distill`
15. `jeehwon/Qwen3-0.6B-Distill_001`
16. `Rexhaif/Qwen3-0.6B-MTEval-SFT`
17. `rd211/Qwen3-0.6B-Instruct`
18. `Flare0p/Qwen3-Agentic-Coder-0.6B`
19. `MaheshNagabhairava/Best-Security-Practices-Model`
20. `MoxStone/SmaliLLM-Qwen3-0.6B-Finetuned`
21. `cytoe/qwen_finetuned`
22. `ya-yje-krasni/qwen3-0.6b-russian-dialogues`
23. `tuandunghcmut/Qwen3-FT-Customer-Dataset`
24. `Ontario/qwen3-0.6b-awesome-prompts`

**Pruebas mencionadas en el plan técnico**
- Revisión de nombres y formas de tensores.
- Comprobación de IDs del vocabulario del tokenizador.
- Nueve prompts heurísticos, incluidos prompts en español.
- Benchmark de referencia con EleutherAI `lm_eval`: ARC-Easy, HellaSwag, TruthfulQA MC2 y GSM8K, con límite configurado de 100 ejemplos por tarea, semilla 42 y batch 1.

**Importante:** el benchmark está configurado, pero esta memoria no contiene puntuaciones finales. No afirmar mejoras ni ordenar los candidatos por calidad hasta que el informe de evaluación lo demuestre.

## Decisiones técnicas

- La similitud de nombre, tamaño o arquitectura no basta para declarar dos modelos compatibles.
- La auditoría de metadatos sirve para filtrar y priorizar; no demuestra por sí sola compatibilidad tensor a tensor.
- Las diferencias de vocabulario/tokenizador, arquitectura, formas de tensores o claves de estado deben registrarse explícitamente.
- La evaluación debe conservar resultados por modelo y distinguir entre fallo de descarga, error de carga, incompatibilidad y resultado de calidad.
- No fusionar por una puntuación heurística aislada: validar con pruebas reproducibles y comparación contra el modelo base.
- La compilación exitosa de la APK demuestra que se construyó el artefacto, no que toda la inferencia funcione correctamente en un dispositivo físico.

## Pendientes y criterios de cierre

- [ ] Consultar la conclusión final de la ejecución 39995671249 y descargar/revisar su informe.
- [ ] Registrar el resultado y el estado de cada uno de los 24 candidatos.
- [ ] Identificar los candidatos que pasan realmente las comprobaciones de arquitectura, tensores y tokenizador.
- [ ] Ejecutar o completar la comparación cuantitativa base vs. candidatos/modelo fusionado, documentando limitaciones y puntuaciones reales.
- [ ] Si procede, generar un artefacto de fusión reproducible y comprobar que se puede cargar e inferir.
- [ ] Ejecutar pruebas funcionales de la aplicación además de la compilación, incluyendo inferencia en dispositivo si el entorno lo permite.
- [ ] Revisar el artefacto APK y registrar su tamaño, procedencia, SHA y método de instalación.
- [ ] Actualizar esta memoria después de cada iteración y enlazar commits, ejecuciones y artefactos.
- [ ] Cerrar únicamente los puntos con evidencia verificable; mantener abiertos los bloqueados por recursos, hardware o datos insuficientes.

## Enlaces de seguimiento

- [Repositorio RONIN-IA](https://github.com/orbitalronin94/RONIN-IA)
- [Auditoría de candidatos — ejecución 39995711599](https://github.com/orbitalronin94/RONIN-IA/actions/runs/39995711599)
- [Build APK — ejecución 39995711424](https://github.com/orbitalronin94/RONIN-IA/actions/runs/39995711424)
- [Evaluación profunda — ejecución 39995671249](https://github.com/orbitalronin94/RONIN-IA/actions/runs/39995671249)
- [Commit de corrección de pesos](https://github.com/orbitalronin94/RONIN-IA/commit/96f8addfcee4cca65082dafe7a25656f8210e816)
- [Commit de pruebas auxiliares](https://github.com/orbitalronin94/RONIN-IA/commit/96345b3d5f18aab42dc97c4f2bc455ff9ed3d29d)
- [Commit de actualización a 24 candidatos](https://github.com/orbitalronin94/RONIN-IA/commit/8e92cc53a160e67f4d3efe0cffc50b3fc6e00d8b)
- [Commit de workflow de auditoría](https://github.com/orbitalronin94/RONIN-IA/commit/ef0ff4984bf3979d94b5cac09a6ce1ccc4b617b4)

---

## Plantilla para la siguiente iteración

### YYYY-MM-DD — Iteración N: título breve

- **Commit:**
- **Motivo:**
- **Archivos/cambios:**
- **Pruebas ejecutadas:**
- **Resultado observado:**
- **Problemas o limitaciones:**
- **Próximos pasos:**
- **Enlaces a CI/artefactos:**
