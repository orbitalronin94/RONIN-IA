# Estado del arte de fusiones de modelos y métricas para RONIN-IA

Fecha de revisión: 2026-10-25

## Resumen ejecutivo

La literatura reciente no respalda la idea de que promediar arbitrariamente pesos de modelos distintos produzca automáticamente un modelo mejor. La vía más defendible es: partir de una base común y checkpoints derivados de ella, comprobar compatibilidad estricta, comparar métodos con un conjunto de validación separado, y conservar una fusión solo si supera a la base en benchmarks independientes sin regresiones graves ni coste de despliegue inaceptable.

La evidencia más relevante consultada:
- **MergeBench (NeurIPS 2025)** propone evaluación estandarizada de fusiones especializadas en instrucción, matemáticas, multilingüe, código y seguridad, y analiza retención de capacidades, coste y calidad por dominio. Advierte que las fusiones siguen teniendo límites frente a modelos multitarea entrenados conjuntamente. https://proceedings.neurips.cc/paper_files/paper/2025/hash/91f7f71cb04699f387dc863da42a1fe3-Abstract-Datasets_and_Benchmarks_Track.html
- **A Systematic Study of Model Merging Techniques in LLMs** (versión 2025; publicación TMLR 2026) compara seis métodos, cuatro familias de modelos, doce checkpoints por base y dieciséis benchmarks. Su resultado principal es una advertencia práctica: Task Arithmetic fue el método que mostró mejoras fiables en su estudio; otros métodos de interferencia/subespacio a menudo degradaron resultados. No debemos asumir que TIES/DARE u otros métodos ganarán sin medirlo. https://mcml.ai/publications/hga26/
- **Evolutionary optimization of model merging recipes** (Nature Machine Intelligence, 2025) trata la selección de modelos, métodos y coeficientes como búsqueda de recetas, no como una única media manual. https://www.nature.com/articles/s42256-024-00975-8
- **Sens-Merging** (Findings of ACL 2025) estudia coeficientes guiados por sensibilidad en lugar de usar el mismo peso en todos los parámetros. Es una línea prometedora, pero exige más cómputo y validación; no es la primera opción en un runner CPU limitado. https://aclanthology.org/2025.findings-acl.984/
- **MergeME** (NAACL 2025) estudia fusión de expertos en arquitecturas MoE, y recalca los problemas de interferencia y heterogeneidad. No equivale a promediar pesos y requiere tratar explícitamente el router/los expertos. https://aclanthology.org/2025.naacl-long.117/
- **Mergekit** documenta implementaciones de Average, Task Arithmetic, TIES, DARE, DARE-TIES y DELLA, entre otras. https://github.com/arcee-ai/mergekit/blob/main/docs/merge_methods.md
- **Model Merging Scaling Laws** (ICML 2026) analiza pérdida de entropía cruzada y rendimientos decrecientes al añadir expertos; respalda medir pérdida y no esperar que más checkpoints produzcan ganancias ilimitadas. https://proceedings.mlr.press/v306/wang26bl.html

## Qué significa para el estado actual del repositorio

La búsqueda existente en `scripts/sweep_fusions.py` hace una criba inicial útil, pero su puntuación actual se basa en nueve prompts con comprobaciones de cadenas. Es una prueba de humo, no una métrica de calidad general: puede premiar respuestas que contienen una palabra esperada sin comprobar que el razonamiento sea correcto, y es sensible a la formulación del prompt. Además:
- El barrido de interpolación lineal solo tiene sentido si la arquitectura, los nombres/formas de tensores y el vocabulario/token IDs son realmente compatibles.
- Un checkpoint que gane esa criba no se debe etiquetar como mejora hasta pasar benchmarks independientes.
- Los candidatos con licencias no verificadas o restrictivas no se deben incluir en el artefacto distribuible.
- Los modelos de arquitecturas o tokenizadores diferentes no se vuelven compatibles por promediar pesos. Para ellos hay que estudiar fusión de comportamiento (destilación), adaptación/entrenamiento o una arquitectura MoE explícita.
- La métrica de latencia obtenida en CPU CI no predice por sí sola la latencia Android; hace falta medir el dispositivo y el formato cuantizado final.

## Plan experimental recomendado (orden de coste creciente)

### Fase 0 — Congelar el punto de referencia

1. Fijar ID/revisión de la base, tokenizador, versiones de bibliotecas, semilla, prompts y configuración de generación.
2. Guardar resultados de la base antes de probar candidatos.
3. Separar datos de selección (validación) de datos de confirmación (test). No elegir coeficientes mirando el mismo test con el que luego se declara la mejora.
4. Registrar hashes de pesos/config/tokenizador y licencias de cada padre.

### Fase 1 — Criba barata de compatibilidad y estabilidad

1. Comprobar licencia, arquitectura/config, claves y formas de tensores, vocabulario y asignación exacta de token IDs.
2. Comprobar valores no finitos y tipos de tensores no flotantes.
3. Evaluar padres individualmente antes de fusionar: un especialista que no mejore su dominio no es automáticamente buen candidato.
4. Ejecutar primero Average y una interpolación conservadora de Task Arithmetic sobre checkpoints finetuneados de la misma base. No mezclar checkpoints entrenados independientemente solo porque sus dimensiones coincidan.
5. Probar pocos coeficientes en validación; refinar alrededor de los mejores en vez de multiplicar combinaciones sin límite.

### Fase 2 — Métricas principales

Reportar por tarea, no solo una puntuación global:

- **Exactitud/accuracy o exact match**: ARC-Easy, GSM8K y tareas con respuesta verificable; para matemáticas, extraer y validar la respuesta final.
- **Pass@1 / pruebas ejecutadas**: código; usar tests ocultos y ejecución aislada cuando sea posible.
- **Log-likelihood / cross-entropy (menor es mejor)**: comparación reproducible de probabilidad asignada a texto de referencia, cuando la tarea y el harness lo soporten.
- **TruthfulQA MC2**: como indicador limitado de veracidad, no como certificación general de factualidad.
- **Instrucción y español**: conjunto de prompts con rúbrica, puntuación ciega por evaluadores y muestras publicadas; un LLM juez puede ayudar, pero hay que comprobar sesgo de posición, acuerdo entre jueces y consistencia con evaluación humana.
- **Seguridad**: tasa de cumplimiento correcto de solicitudes benignas, tasa de rechazo apropiado de solicitudes dañinas y tasa de falsos rechazos; no basta con comprobar que aparece una palabra.
- **Retención por dominio**: puntuación fusionada/base por tarea y peor caída de cualquier dominio, además del promedio.
- **Robustez**: varias semillas si hay muestreo, paráfrasis de prompts y varias ejecuciones en los casos ambiguos.

### Fase 3 — Regla de decisión

No declarar ganador por una sola puntuación. Mantener una tabla con base, padres y fusiones que incluya:
- métricas por tarea y delta respecto a la base;
- media normalizada/retención de capacidades y peor regresión;
- coste de descarga, RAM pico, tamaño cuantizado, tiempo de carga y tokens/s;
- licencia, hashes, método y coeficientes;
- intervalo de confianza o variabilidad cuando sea posible.

Una candidata solo pasa a confirmación si la mejora en validación es consistente y no introduce una regresión importante. Confirmar después en datos no usados para elegir coeficientes. Para APK, repetir la evaluación en el modelo cuantizado y en el dispositivo objetivo: la cuantización puede cambiar el orden de los candidatos.

## Próximos experimentos prioritarios

1. **No aumentar ciegamente el número de modelos**: primero obtener y leer el artefacto de la búsqueda ya en cola, y confirmar si alguna combinación compatible ofrece señal.
2. Si existe señal, aplicar el benchmark estandarizado ya presente en el repositorio (`scripts/benchmark_merge_vs_base.py`) a base y candidata, primero con un límite pequeño para depurar y luego con el conjunto completo.
3. Si no hay señal o la fusión empeora, probar Task Arithmetic con checkpoints realmente derivados de la misma base y coeficientes de baja magnitud, con validación separada.
4. Si los candidatos útiles no comparten base/tokenizador, detener la media de pesos: comparar un diseño MoE con router o destilación de comportamiento como líneas distintas, con presupuesto de latencia y memoria Android.
5. Solo empaquetar una fusión tras superar los controles de calidad, licencia, cuantización y dispositivo. En caso contrario, conservar el modelo base y no etiquetar una regresión como mejora.

## Referencias de métricas y recursos

- MergeBench (NeurIPS 2025): https://proceedings.neurips.cc/paper_files/paper/2025/hash/91f7f71cb04699f387dc863da42a1fe3-Abstract-Datasets_and_Benchmarks_Track.html
- Evaluación conductual e interna de fusiones (BlackboxNLP 2025): https://aclanthology.org/2025.blackboxnlp-1.19/
- Mergekit: https://github.com/arcee-ai/mergekit
- lm-evaluation-harness: https://github.com/EleutherAI/lm-evaluation-harness
