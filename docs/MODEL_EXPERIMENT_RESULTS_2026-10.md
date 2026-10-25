# Informe de resultados: evaluación inicial de modelos

**Fecha del informe:** 2026-10-25  
**Estado:** resultados exploratorios; no constituyen una decisión para cambiar el modelo predeterminado.

## Resumen ejecutivo

Se compararon Qwen2.5-0.5B-Instruct y SmolLM2-360M-Instruct con el mismo conjunto versionado de 12 prompts sintéticos y el workflow de GitHub Actions. En el subconjunto de nueve casos evaluados automáticamente con coincidencia exacta, Qwen obtuvo 5/9 (55,56 %) y SmolLM2 1/9 (11,11 %). La latencia mediana medida en ese entorno fue de 747,485 ms para Qwen y 1602,9 ms para SmolLM2.

Estos resultados favorecen a **Qwen como candidato para la siguiente fase de evaluación**, pero no prueban que sea mejor en producción ni justifican cambiar el modo predeterminado. La muestra es pequeña, hay tres casos por modelo que requieren revisión humana y el criterio exacto puede penalizar respuestas semánticamente correctas con texto adicional. El benchmark se ejecutó con PyTorch en CPU y no mide la ruta ONNX/WebGPU/WASM del producto ni un teléfono real.

## Contexto

La secuencia de trabajo que llevó a este experimento fue:

- **PR #21:** limpieza del proyecto y retirada de pesos ONNX grandes del repositorio/empaquetado.
- **PR #22:** inferencia local opcional en navegador; el modo remoto sigue siendo el predeterminado.
- **PR #23:** shortlist inicial de modelos y criterios de selección.
- **PR #24:** dataset sintético versionado y scorer determinista.
- **PR #25:** página para ejecutar la evaluación en el navegador.
- **PR #26:** workflow manual/automatizado para evaluar modelos en GitHub Actions.
- **PR #27:** corrección del setup de Python para no depender de una caché de pip sin archivo de dependencias.
- **PR #28:** comparación Qwen/SmolLM2 con el mismo dataset y parámetros, más guía de revisión humana.

La intención ha sido medir antes de cambiar el modelo, mantener los pesos fuera de Git y no descargar modelos en CI ordinario.

## Configuración del experimento

| Campo | Valor |
|---|---|
| Workflow | `.github/workflows/model-candidate-compare.yml` |
| Ejecución | [GitHub Actions run 40214012265](https://github.com/orbitalronin94/RONIN-IA/actions/runs/40214012265) |
| Commit de la ejecución | `9dfd6cf37fc9c88d68015d51db62a3434f4abbda` |
| Dataset | `benchmarks/model-eval-prompts.jsonl` |
| Casos | 12 prompts sintéticos en español e inglés |
| Candidatos | Qwen/Qwen2.5-0.5B-Instruct y HuggingFaceTB/SmolLM2-360M-Instruct |
| Entorno | GitHub Actions, PyTorch, CPU, float32 |
| Generación | `max_new_tokens=96` |
| Artefactos | Informes JSON y predicciones JSONL, retenidos por 30 días en Actions |

Los artefactos descargados para analizar esta ejecución fueron:

- **Qwen:** [artefacto 12606862272](https://github.com/orbitalronin94/RONIN-IA/actions/runs/40214012265)
- **SmolLM2:** [artefacto 12606662801](https://github.com/orbitalronin94/RONIN-IA/actions/runs/40214012265)

Los enlaces llevan a la ejecución que contiene ambos artefactos; los identificadores permiten distinguirlos en la sección de artefactos.

## Resultados cuantitativos

| Métrica | Qwen2.5-0.5B-Instruct | SmolLM2-360M-Instruct |
|---|---:|---:|
| Casos del dataset | 12 | 12 |
| Predicciones recibidas | 12 | 12 |
| Casos puntuados automáticamente | 9 | 9 |
| Casos correctos según el scorer | 5 | 1 |
| Exactitud automática | 55,56 % | 11,11 % |
| Latencia medida: mediana | 747,485 ms | 1602,9 ms |
| Latencia medida: mínima | 430,7 ms | 880,35 ms |
| Latencia medida: máxima | 10 919,58 ms | 6412,34 ms |
| Casos que requieren revisión humana | 3 | 3 |

La mediana de latencia observada de Qwen fue aproximadamente un 53 % menor que la de SmolLM2 en esta ejecución. Es una comparación descriptiva de este entorno concreto, no una estimación de rendimiento en el dispositivo final.

### Desglose de los casos puntuados automáticamente

| Categoría | Qwen | SmolLM2 | Nota |
|---|---:|---:|---|
| Extracción | 2/2 | 0/2 | SmolLM2 incluyó frases adicionales en vez de devolver únicamente el valor solicitado. |
| Formato | 2/2 | 1/2 | Ambos pasaron el caso JSON; SmolLM2 no devolvió exactamente `READY` en el otro caso. |
| Matemáticas | 1/4 | 0/4 | Algunos cálculos eran correctos, pero la respuesta no respetó el formato de solo número; también hubo errores de cálculo. |
| Razonamiento | 0/1 | 0/1 | La salida de Qwen fue `Eva.`; el scorer probablemente la penalizó por el punto final. SmolLM2 respondió incorrectamente `Ana`. |

Las categorías de resumen, seguimiento de instrucciones e incertidumbre tienen un caso cada una y se marcan para revisión humana; no forman parte del denominador de exactitud automática.

## Observaciones cualitativas importantes

### Qwen

- Respondió correctamente a ambos casos de extracción y ambos casos de formato.
- En matemáticas, resolvió correctamente una división, pero falló dos cálculos y en otro caso dio el resultado correcto con una expresión adicional, incumpliendo «solo el número».
- En el caso de razonamiento respondió `Eva.`; conviene normalizar puntuación final antes de concluir que fue un error.
- El resumen transmitió la idea principal, pero tenía un problema gramatical.
- La respuesta a la instrucción de una sola frase fue larga, numerada y aparentemente truncada; también registró la mayor latencia del conjunto (10 919,58 ms).
- En el caso de incertidumbre reconoció que no tenía acceso al dato solicitado, aunque la respuesta fue más extensa de lo necesario.

### SmolLM2

- El único caso automáticamente correcto fue el de formato JSON.
- Sus respuestas matemáticas incluyeron resultados correctos en algunos casos, pero incumplieron el requisito de devolver únicamente el resultado; otro caso repitió la pregunta sin resolverla.
- En extracción devolvió frases completas con información adicional, en vez del valor exacto solicitado.
- En razonamiento respondió `La persona más baja es Ana.`, cuando la respuesta esperada era Eva.
- El resumen parece claro y correcto en una lectura preliminar, pero sigue pendiente de evaluación humana formal.

Estas observaciones se basan en las predicciones guardadas en los artefactos de esa ejecución. La revisión cualitativa no reemplaza un protocolo de evaluación humana ciego.

## Cómo interpretar las métricas

1. **El denominador de exactitud es nueve, no doce.** Tres casos abiertos por modelo requieren revisión humana. Un solo caso cambia el resultado automático en unos 11,1 puntos porcentuales.
2. **Coincidencia exacta no equivale a calidad semántica.** Una respuesta correcta acompañada de explicación puede fallar cuando la instrucción exigía un único token o número. A la inversa, no conviene aceptar texto adicional cuando seguir el formato es parte de la tarea.
3. **El scorer puede producir falsos negativos evitables.** La puntuación final de `Eva.` es un ejemplo que debe revisarse y cubrirse con pruebas antes de interpretar el resultado como fallo real.
4. **No es una comparación de ejecución local.** El benchmark usó PyTorch CPU float32. No mide ONNX Runtime, Transformers.js, WebGPU, WASM, Android, memoria máxima, tiempo de descarga fría ni tiempo hasta el primer token.
5. **No es una prueba estadística robusta.** Doce prompts sintéticos son una muestra pequeña y no representan necesariamente conversaciones reales, diversidad lingüística o tareas de producción.
6. **La latencia es contextual.** El hardware y la carga del runner afectan a los tiempos; no se deben presentar como latencias garantizadas para usuarios.

## Benchmark previo de Qwen

Una ejecución previa de Qwen, [run 40213183165](https://github.com/orbitalronin94/RONIN-IA/actions/runs/40213183165), también produjo 12 predicciones, 9 casos puntuados, 5 correctos (55,56 %) y 3 casos de revisión humana. Su mediana de latencia fue 722,745 ms, con mínimo 450,95 ms y máximo 10 511,47 ms. La similitud de exactitud entre las dos ejecuciones de Qwen es alentadora como comprobación preliminar, pero no demuestra reproducibilidad estadística ni elimina las limitaciones del scorer y del entorno.

## Conclusión y decisión actual

- **Candidato para la siguiente fase:** Qwen2.5-0.5B-Instruct, por su resultado superior en esta comparación acotada.
- **Decisión de producto:** mantener el modo remoto como predeterminado y la inferencia local como opción. No cambiar defaults basándose solo en este experimento.
- **Modelo SmolLM2:** no priorizar su integración adicional hasta mejorar el protocolo y reunir más evidencia; el resultado actual es insuficiente para recomendarlo frente a Qwen en estas tareas.
- **Entrenamiento o fusión de modelos:** no procede todavía. Primero hacen falta evaluación y diagnóstico más sólidos.

## Próximos pasos recomendados

1. Mejorar y versionar el scorer: normalización conservadora de puntuación, pruebas unitarias para formatos estrictos y casos semánticamente correctos con puntuación final. Mantener separados los requisitos de formato exacto y la corrección semántica.
2. Completar la revisión humana de los tres casos abiertos por modelo usando una rúbrica común y, si es posible, revisores que no sepan qué modelo produjo cada respuesta.
3. Ampliar el dataset con más casos de español e inglés, aritmética, extracción, seguimiento de instrucciones, resumen y rechazo/expresión de incertidumbre; añadir casos adversariales y evitar duplicados triviales.
4. Volver a ejecutar ambos modelos con dataset y configuración versionados, conservando informes y predicciones.
5. Probar Qwen en el navegador real y en dispositivos Android representativos, registrando backend, cuantización, latencia, memoria, tiempo de descarga fría y tasa de fallos.
6. Solo después comparar calidad, experiencia, tamaño descargado y coste operativo para decidir si el modo local debe cambiar de estado.

## Reproducibilidad

Para repetir la comparación, ejecuta el workflow **Model Candidate Compare** desde GitHub Actions y conserva los artefactos JSON/JSONL generados. Registra el SHA del commit, los identificadores de los artefactos y cualquier cambio en el dataset, scorer, parámetros o entorno. No sustituyas resultados medidos por estimaciones ni mezcles métricas de PyTorch CPU con resultados de ONNX/WebGPU/WASM.

Documentos relacionados:

- [Selección de modelos](MODEL_SELECTION.md)
- [Guía del evaluador](MODEL_EVALUATION_HARNESS.md)
- [Revisión humana](MODEL_EVAL_HUMAN_REVIEW.md)
- [Ejecución de evaluación en navegador](RUN_MODEL_EVAL_IN_BROWSER.md)
