# Entrenamiento oficial desde cero y evaluación MMLU-Pro

## Alcance

La PR #39 integró en `main` la preparación de los corpus autorizados. El workflow oficial es [`ronin-official-training-holdout.yml`](../.github/workflows/ronin-official-training-holdout.yml).

La mezcla de entrenamiento contiene exclusivamente:

1. **Portfolio/Papers:** 48 documentos utilizables, autorización expresa para las aportaciones originales, revisión fijada a `fffc234fdf3f82b6a90d56ae9b190d1c0de79690`. Se usa solo para entrenamiento; las citas, imágenes, código y otros materiales de terceros requieren revisión independiente.
2. **CLiGS Textbox, CoNSSA y ELTeC-spa:** tres fuentes con revisiones inmutables y licencias documentadas. De los 644 documentos preparados, solo los **608 de train** entran en la mezcla.

Los 18 documentos validation y 18 test de literatura se reservan. La mezcla conserva manifiestos, procedencia y SHA-256 por fuente y por salida. No se concatena dos veces el corpus-v2 si sus hashes coinciden con las particiones actuales.

Quedan fuera de este entrenamiento:
- La biblioteca de criptografía/opacidad (6 fuentes y 506 registros) hasta terminar revisión manual de derechos, OCR, edición y evidencia.
- El corpus sintético de pseudopalabras, reservado a smoke tests.
- Las generaciones de Phi-4 u otros tutores hasta revisión humana de calidad y derechos. La auditoría REF valida estructura, no verdad factual ni calidad.
- Todos los splits validation/test y los benchmarks.

RONIN inicializa el estudiante desde cero. Los pesos de tutores no se cargan ni se mezclan con el estudiante.

## Holdout externo: MMLU-Pro completo

- Dataset: [TIGER-Lab/MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro).
- Revisión fijada: `b189ec765aa7ed75c8acfea42df31fdae71f97be`.
- Split: `test`; esperado **12.032 preguntas**.
- Se evalúa el mismo test antes y después del entrenamiento, sin gradientes.
- El muestreo por defecto es el test completo (`mmlu_limit=0`). En ejecuciones parciales se admite una muestra estratificada reproducible.
- El contexto de evaluación es 2.048 bytes. No se truncan preguntas; las que exceden el límite se cuentan como omitidas y reducen la cobertura.
- Se registra exactitud global, desglose por dominio, cobertura, ítems omitidos, revisión y SHA-256 del dataset y checkpoint.

**Importante:** RONIN usa un protocolo propio zero-shot de probabilidad del siguiente byte de la letra de respuesta (A–J), sin CoT ni ejemplos. No es el protocolo oficial de MMLU-Pro y su puntuación **no se compara con el leaderboard oficial**. El benchmark se mantiene fuera de entrenamiento, selección de corpus y ajuste de prompts.

## Parámetros del primer experimento oficial

- Modelo: perfil `tiny`, aproximadamente 9.922.880 parámetros.
- Inicialización: aleatoria, desde cero.
- Pasos: 1.000.
- Semilla: 1337.
- Hardware: runner CPU de GitHub Actions.
- Evaluación: MMLU-Pro test completo, antes/después.
- Timeout: 6 horas.
- Artefacto: informes y manifiestos JSON; no incluye corpus ni checkpoints.

La primera ejecución se lanzó automáticamente al incorporar el workflow: [run #1](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41827976377). Su estado y resultados se deben consultar en Actions; no se publican métricas hasta que el trabajo finalice y el artefacto se valide.

## Cómo lanzar el workflow

GitHub → Actions → **Experimento oficial RONIN desde cero + MMLU-Pro completo** → Run workflow.

- Para el test completo: `mmlu_limit=0` y una sola semilla por ejecución.
- Para una muestra de desarrollo: indicar un límite positivo y hasta cinco semillas.
- El push a `main` que modifica componentes críticos usa por defecto 1.000 pasos, semilla 1337 y el test completo.

El antiguo workflow `portfolio-training-cycle.yml` se retiró para evitar dos ciclos oficiales competidores. Los ciclos sintéticos y el piloto interno de 23 preguntas permanecen como pruebas técnicas, no como benchmark oficial.

## Resultado histórico anterior (no es el experimento oficial)

Un smoke anterior de 100 pasos y 131 preguntas MMLU-Pro obtuvo 11/131 (8,40 %) antes y 10/131 (7,63 %) después. La diferencia de un acierto no demuestra mejora ni regresión; el contraste pareado fue no significativo (p = 1,00). Ese resultado usó un ciclo previo y una muestra limitada, por lo que no debe confundirse con el nuevo holdout completo.

## Interpretación

La primera ejecución oficial es una línea base exploratoria. Una sola semilla, un modelo de 9,9 M de parámetros y un protocolo de selección de letra no demuestran razonamiento general. Para afirmaciones más fuertes harán falta más semillas, mayor escala, tareas abiertas con rúbricas humanas, calibración, análisis de robustez y otros holdouts independientes.

## Ciclo experimental mixto con REF y tutor (PR #41)

Este ciclo es **complementario** al experimento oficial anterior; no lo sustituye ni cambia su protocolo de holdout completo. Su objetivo es medir qué ocurre al añadir datos especializados y propuestas de tutor al estudiante RONIN.

La mezcla experimental contiene:

1. **Portfolio/Papers**: 48 documentos incorporados, con autorización expresa limitada a las aportaciones originales. Citas, imágenes, código y materiales de terceros requieren revisión independiente.
2. **CLiGS Textbox, CoNSSA y ELTeC-spa**: solo los 608 documentos del split `train`; 18 validation y 18 test permanecen reservados.
3. **Casos estructurados de opacidad**: solo 404 registros `train`; 50 validation y 52 test quedan fuera. El train contiene 400 controles sintéticos y cuatro casos no sintéticos, por lo que es un piloto muy desequilibrado.
4. **Phi-4-mini-instruct**: hasta 16 propuestas de tutor, incorporadas solo si la generación nativa y la auditoría REF estructural terminan correctamente. Si falla, el ciclo continúa sin augmentación y lo deja registrado.

Los seis libros y escaneos primarios de criptografía se descargan y verifican por SHA-256, pero no se mezclan como texto completo: siguen pendientes de OCR/transcripción y revisión documental. El corpus sintético de pseudo-palabras solo sirve para smoke tests. MMLU-Pro, benchmarks y todos los holdouts permanecen fuera de los gradientes.

El ciclo mixto usa 100 pasos y una semilla en PR como smoke; al integrarse en `main`, ejecuta 1000 pasos por semilla con `1337, 2027, 42` y una muestra MMLU-Pro de 140 preguntas. No es el test completo ni se compara con el leaderboard oficial. El workflow oficial mantiene el holdout completo de 12.032 preguntas y la mezcla limpia Portfolio + literatura, sin tutor ni casos criptográficos.

El objetivo es comparar dos condiciones claramente separadas: (a) línea base limpia con test externo completo y (b) mezcla enriquecida con REF/tutor y evaluación parcial reproducible. Una diferencia no se atribuirá a la arquitectura sin controles adicionales.
