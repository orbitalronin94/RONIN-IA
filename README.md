# RONIN-IA


## Admisión legacy compatible y entrenamiento documental (5 de noviembre de 2026)

Se habilita una vía **scoped legacy** para entrenar con el corpus histórico ya auditado, sin esperar al G-0 global de las 64 bibliotecas. No se rebajan los requisitos legales o de privacidad para fuentes nuevas: se reutiliza exactamente el perímetro probado del manifiesto legacy (tres repositorios fijados, derechos de texto declarados como dominio público, revisiones inmutables, procedencia y hashes por documento, 608 registros train y cero duplicados exactos). Esta excepción no convierte el corpus en Level A ni lo contabiliza en el inventario de las 64 bibliotecas.

- Corpus: 608 documentos / 140.295.523 bytes; SHA-256 train `9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78`.
- Fuentes fijadas: CLiGS Textbox (355), CLiGS CONSSA (165) y ELTeC español (88).
- Entrenamiento: workflow [legacy-document-training.yml](.github/workflows/legacy-document-training.yml), perfil RoninLM `tiny`, CPU GitHub Actions, 500 pasos por defecto.
- La validación interna se deriva determinísticamente del train legacy. Los 18 documentos legacy de validation y los 18 de test no se descargan ni se leen en esta run.
- El workflow verifica manifiesto, estado scoped, número de documentos, bytes y SHA-256 antes de entrenar. Publica métricas, throughput, split manifest y checkpoint.
- La run no declara G-0 global, no promueve el checkpoint automáticamente y no autoriza mezclar candidatos de las otras bibliotecas.

La política de las 64 bibliotecas sigue exigiendo verificación de derechos por documento, payload, privacidad, calidad, deduplicación y particiones. El ajuste es de **alcance y proporcionalidad de evidencia**, no una autorización general para aceptar candidatos.

## Estado documental verificado — 5 de noviembre de 2026, 11:20 CET

Este corte corrige y amplía los resúmenes históricos que aparecen más abajo. El inventario canónico vigente es de **32 dominios × General/HKD = 64 bibliotecas** (\`data/datasets/libraries/manifest-64.json\`):

- **608 documentos / 140.295.523 bytes** de train en `literature-es-v1`, ahora contados como Level A scoped-equivalent en Humanidades — General. Sus 18 validation y 18 test permanecen excluidos del entrenamiento.
- **4.855 registros candidatos adquiridos por fuente**: 3.087 ScienceVerse, 824 DOI de ScienceVerse/Crossref, 267 textos NASA NTRS y 677 textos ScienceVerse Collabra. Es una suma por fuente, no un total global deduplicado ni documentos Level A admitidos.
- **608 documentos y 140.295.523 bytes Level A** dentro del inventario canónico; **1/64** alcanza el mínimo (Humanidades — General). G-0 sigue FAIL y bloquea el entrenamiento global. G-0 continúa en FAIL y no se autoriza entrenamiento documental con estos candidatos.

La ejecución [RUN 5 #41904620741](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41904620741) terminó sin consolidar bibliotecas: su índice maestro declara 0/16 encontradas, 0 documentos y 0 bytes. Los diagnósticos muestran que el umbral heredado de 2.560 MiB por biblioteca bloqueó, entre otros, una salida de 9.019 bytes y otra de 39.308.151 bytes. Los artefactos de índice no son payloads documentales. Esta ejecución no incrementa el contador de admitidos ni el de bibliotecas Level A.

**Regla de lectura:** “adquirido”, “candidato”, “admitido legacy” y “Level A” son estados diferentes. Level A aplica el estándar scoped que admitió `literature-es-v1`: fuente pública fijada, derechos/procedencia por documento, payload y SHA-256, particiones disjuntas, cero duplicados exactos en train y auditorías previas de calidad/privacidad. No se exige una nueva reconciliación territorial general; se mantienen exclusiones de terceros y controles de integridad.

**RONIN** es un proyecto de investigación e ingeniería de modelos de lenguaje. Su propósito es comprobar hasta dónde puede llegar una arquitectura propia entrenada desde una inicialización aleatoria, con un proceso reproducible de datos, entrenamiento, evaluación y despliegue.

- Repositorio: https://github.com/orbitalronin94/RONIN-IA
- Rama principal: `main`
- Fuente de verdad: este repositorio. El código, las pruebas, las configuraciones y la documentación operativa viven aquí.
- Estado: ya existe un modelo estudiante propio, implementado en PyTorch, y se ha completado un primer ciclo de entrenamiento experimental. El proyecto sigue en fase de investigación; no se afirma todavía competencia general.

## Pipeline único de fine-tuning GPU (5 de noviembre de 2026)

La nueva línea de entrenamiento selecciona **un único modelo: Qwen3.5-4B**, con Unsloth y adaptadores LoRA en BF16/FP16. Se evita QLoRA de 4 bits porque la guía actual de Unsloth desaconseja esa cuantización para Qwen3.5. El perfil inicial usa contexto 2.048, microbatch 1, acumulación 8 y 1.000 pasos.

- Preparación de corpus: [workflow Qwen3.5](.github/workflows/qwen35-prepare-corpus.yml).
- Entrenamiento GPU: [notebook Colab](https://colab.research.google.com/github/orbitalronin94/RONIN-IA/blob/main/notebooks/ronin_qwen35_4b_training.ipynb).
- Implementación: [scripts/train_qwen35_unsloth.py](scripts/train_qwen35_unsloth.py).
- Diseño y protocolo: [docs/QWEN35_TRAINING_PIPELINE.md](docs/QWEN35_TRAINING_PIPELINE.md).

El workflow recupera el artefacto del único corpus documental admitido actualmente (literatura española, 608 documentos), verifica UTF-8 y SHA-256 y publica un paquete listo para Colab. El notebook ejecuta el entrenamiento en GPU cuando Colab concede una; el runner estándar de GitHub no se presenta como GPU. La evaluación iterativa utiliza MMLU-Pro validation; el test queda reservado para una comprobación final independiente. Los adaptadores son candidatos y no se promocionan sin evidencia de mejora.

## Estado actual del modelo

**RONIN ya tiene modelo propio.** No es únicamente una hoja de ruta ni una colección de especificaciones: el repositorio contiene un Transformer causal decoder-only implementado en PyTorch, con inicialización propia y **9.922.880 parámetros en el perfil `tiny`**. Su arquitectura actual combina RoPE, RMSNorm, SwiGLU y GQA configurable.

También se ha ejecutado un primer ciclo reproducible de entrenamiento desde inicialización aleatoria. El resultado siguiente es el baseline histórico del primer smoke test (100 pasos, CPU, una semilla y corpus sintético de control); no corresponde todavía al currículo estructurado que se incorpora en el siguiente ciclo:

| Medición | Antes | Después |
|---|---:|---:|
| Bits por byte (BPB) | 7,9281 | 2,2395 |
| Aciertos en el piloto multidominio | 0/23 | 8/23 (34,8 %; IC95 % exacto de Clopper–Pearson ≈ [16 %, 57 %]) |

La evaluación de lenguaje utilizó 32.768 bytes de validación. El benchmark multidominio contiene 23 preguntas de opción múltiple y se puntúa mediante predicción del siguiente byte.

**Cómo interpretar estos datos:** son evidencia de que el circuito de entrenamiento y evaluación funciona; no demuestran conocimiento general ni razonamiento. El siguiente ciclo sustituye el texto sin semántica por un currículo sintético estructurado, con tareas calculables de ocho dominios, corpus nuevo por ejecución y tres semillas. Es una mejora del warm-start técnico, no un corpus factual externo ni una prueba de competencia general.

Los ciclos sintéticos no descargan corpus externos y no eluden el bloqueo G-0 de licencias. Los informes se publican como artefactos de GitHub Actions; los checkpoints no se publican ni se conservan como pesos descargables. Por tanto, **hay un modelo implementado y entrenado experimentalmente, pero todavía no distribuimos un checkpoint entrenado como versión utilizable**.

Workflow principal: [Experimento oficial RONIN desde cero + MMLU-Pro completo](https://github.com/orbitalronin94/RONIN-IA/actions/workflows/ronin-official-training-holdout.yml). Los ciclos sintéticos estructurados son un warm-start técnico con promoción conservadora; no sustituyen al entrenamiento oficial ni a las bibliotecas documentales autorizadas.

**Ritmo de iteración:** el ciclo programado ejecuta 500 pasos por semilla (tres semillas) y evalúa la semilla principal antes/después en una muestra estratificada de 140 preguntas de `validation` de MMLU-Pro. Un checkpoint solo se conserva si reduce bits por byte en la validación sintética y no empeora ni el benchmark multidominio interno ni MMLU-Pro `validation`. El split `test` queda reservado para la verificación final y nunca guía selección de pesos. La métrica de MMLU-Pro sigue siendo el protocolo propio de RONIN por siguiente byte, no el leaderboard oficial.

### Barrido experimental de 500 semillas

Se añade un experimento independiente para medir la sensibilidad a la inicialización del mejor modelo propio disponible: `tiny`, **9.922.880 parámetros**. El workflow genera un corpus sintético original de **1 GiB**, sin descargas, textos de terceros ni salidas de tutores, y ejecuta 500 inicializaciones independientes con 100 pasos por semilla (50.000 actualizaciones en total). Compara BPB y el benchmark multidominio interno antes/después; conserva los cinco candidatos mejor situados y los contrasta en una muestra fija de 140 preguntas de **MMLU-Pro validation**. El split `test` no se consulta.

**Límite esencial:** este corpus es legalmente controlable porque se genera desde plantillas procedurales propias, pero es un currículo sintético, no un gran corpus factual externo. El resultado mide aprendizaje de tareas sintéticas y variación entre semillas; no demuestra adquisición de conocimiento general. El entrenamiento documental externo seguirá dependiendo de G-0 y de la admisión de las bibliotecas.

### Ciclos rápidos de aprendizaje abierto

Se incorpora un segundo carril experimental: [Ciclos rápidos RONIN — corpus abierto](.github/workflows/rapid-open-training-cycles.yml). Ejecuta hasta tres iteraciones cortas por tanda y, al terminar correctamente, **se relanza automáticamente** mediante `workflow_run`: no hay que activar cada ciclo manualmente. Un arranque periódico de recuperación evita que la cadena quede abandonada tras una interrupción. Recupera el último checkpoint aceptado y solo promueve uno nuevo si mejora la accuracy de MMLU-Pro validation sin empeorar BPB. El test final de MMLU-Pro queda fuera del bucle y reservado para la evaluación de release.

**Referencia experimental del modelo:** `ronin-open-warmstart` (caché de GitHub Actions; último checkpoint aceptado, no release público). Los informes de cada ejecución incluyen hashes, métricas y decisión de promoción. El workflow está automatizado cada seis horas, pero no descargará ni entrenará corpus documentales mientras G-0 no esté en PASS. Por tanto, hasta que exista aprobación legal humana, el carril documental permanecerá bloqueado y no se afirmará que ha comenzado ese entrenamiento.




## Estado de datos y experimento oficial (4 de noviembre de 2026)

La [PR #39](https://github.com/orbitalronin94/RONIN-IA/pull/39) ya está fusionada en `main` (merge commit `ba22ed03fd76b3543f32ce301b8bbd0da6a714f9`).

### Dieciséis bibliotecas masivas + Portfolio experto

**Portfolio/Papers queda fuera de pretraining y SFT.** Se reserva como índice RAG de experto: RONIN lo consulta cuando detecte incertidumbre, recupera fragmentos con procedencia y cita la fuente. No cuenta entre las bibliotecas ni se añade a los pesos preventivamente. Solo se reconsideraría su entrenamiento si una carencia demostrada no se resuelve con recuperación y un A/B controlado prueba mejora, con aprobación explícita.

El gate previo al próximo entrenamiento exige **16 bibliotecas independientes**: ocho base (matemáticas; lógica/epistemología; filosofía; física; química/materiales; biología/medicina; informática/software; derecho/economía/ciencias sociales) y otras ocho derivadas de fuentes masivas mediante selección de conocimiento de alta densidad, una por cada dominio. Cada una necesita al menos **2,5 GiB de train** normalizado y deduplicado. RUN 5 limita a 8 GiB el texto candidato por dominio antes de selección base/HKD. Bytes no sustituyen calidad, cobertura, diversidad ni revisión de derechos.

Las ocho adicionales se construirán con `RONIN-HKD-0.1`: relevancia del dominio, densidad de unidades de conocimiento, especificidad, contenido informativo IDF y estructura. La métrica está inspirada en HKS (AAAI 2025), DSIR (NeurIPS 2023) y métricas de diversidad/densidad/homogeneidad (LREC 2020); es un prototipo heurístico propio y debe validarse con revisión humana y ablaciones antes de admitir datos.

**Estado real: 0/16 bibliotecas admitidas para entrenamiento.** Common Corpus y PMC Cloud están habilitados solo para extraer candidatos bajo autorizaciones limitadas; PMC aporta texto JATS CC0/CC BY por versión para biología/medicina y química. La [RUN 5 actual](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41904620741) está en ejecución. Sus salidas seguirán bloqueadas hasta revisión humana, hashes, auditoría legal, deduplicación cruzada, calidad, PII/secretos y splits sin fugas. G-0 global continúa FAIL: no se entrena con estos textos.

- Manifiesto de las 16: [sixteen_libraries.json](data/manifests/sixteen_libraries.json).
- Adaptadores y allowlists: [knowledge_dense_sources.json](data/manifests/knowledge_dense_sources.json).
- [Ingesta PMC Cloud por versión y licencia](docs/FUENTE_PMC_OA.md).
- [Métrica y protocolo HKD](docs/METRICA_DENSIDAD_SEMANTICA.md).
- [Auditoría de las fuentes masivas](docs/AUDITORIA_OCHO_BIBLIOTECAS_MASIVAS.md).
- [Programa bibliográfico y glosario técnico](docs/PROGRAMA_BIBLIOGRAFICO_Y_GLOSARIO.md).
- [Plan de aceleración CPU](docs/PLAN_ACELERACION_ENTRENAMIENTO_CPU.md).

El carril anterior de GPT-2/GPT-Neo/Phi-4 queda como referencia histórica. La nueva tutoría principal es local y dual: Qwen3.6-27B (Apache-2.0) + DeepSeek-R1-Distill-Qwen-32B (MIT), ambos cuantizados localmente a 4 u 8 bits. Se ejecutan secuencialmente, no se usa inferencia por API y sus pesos nunca se transfieren al estudiante.

### Tutoría dual local y primer entrenamiento socrático verificable

La implementación está en [docs/LOCAL_DUAL_TEACHERS.md](docs/LOCAL_DUAL_TEACHERS.md). Incluye descarga con revisión y SHA-256 fijados, verificación de licencias, inferencia GGUF local con llama.cpp enlazado a loopback, comparación entre ambos tutores y filtro contra la etiqueta gold de MMLU-Pro validation. Solo se entrena con ejemplos en los que ambos coinciden entre sí y con el oráculo independiente. El estudiante se inicializa desde cero. La ejecución completa se lanza desde una máquina local con GPU CUDA mediante `scripts/prepare_and_train_local_dual_tutors.py`; no se suben prompts ni corpus a GitHub Actions ni a APIs externas.

### Workflow oficial: entrenamiento desde cero + holdout externo

<badge color="success">Primera ejecución completada</badge>

[Experimento oficial RONIN desde cero + MMLU-Pro completo](https://github.com/orbitalronin94/RONIN-IA/actions/workflows/ronin-official-training-holdout.yml)

La [ejecución oficial #1](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41827976377) terminó correctamente: 1.000 pasos, semilla 1337 y modelo tiny de 9.922.880 parámetros en CPU. El artefacto contiene informes y manifiestos, no pesos ni corpus.

**Resultado MMLU-Pro (protocolo propio RONIN):**

| Medición | Inicial | Final |
|---|---:|---:|
| Aciertos | 1.299/11.687 | 1.283/11.687 |
| Accuracy | 11,115 % | 10,978 % |

- Diferencia global: **−0,137 puntos porcentuales**.
- Seleccionados: 12.032; evaluados: 11.687; omitidos por exceder 2.048 bytes: 345.
- Cobertura: 97,13 %. `complete_test_set=false`; por tanto, no se debe describir como cobertura completa.
- La mezcla de entrenamiento fue 94,53 % literatura abierta y 5,47 % Portfolio por bytes.

**Variación observada por dominio** (diferencia de accuracy antes/después, en puntos porcentuales):

| Dominio | Antes → después (aciertos) | Diferencia |
|---|---:|---:|
| Biology | 83 → 78 | −0,707 pp |
| Business | 85 → 84 | −0,127 pp |
| Chemistry | 113 → 108 | −0,442 pp |
| Computer Science | 69 → 42 | **−6,618 pp** |
| Economics | 98 → 104 | +0,715 pp |
| Engineering | 107 → 112 | +0,521 pp |
| Health | 93 → 103 | +1,225 pp |
| History | 31 → 44 | **+4,221 pp** |
| Law | 79 → 121 | **+4,762 pp** |
| Math | 146 → 111 | −2,593 pp |
| Other | 106 → 101 | −0,548 pp |
| Philosophy | 78 → 54 | **−4,810 pp** |
| Physics | 136 → 127 | −0,695 pp |
| Psychology | 75 → 94 | +2,405 pp |

El patrón relevante no es solo el delta global negativo: aparece una **asimetría entre dominios**. Derecho e historia suben más de cuatro puntos, mientras informática y filosofía retroceden con fuerza. Es una señal que merece un experimento dirigido de retención y mezcla de datos, no una demostración de olvido catastrófico ni de su causa. Con una sola semilla, resultados agregados y sin predicciones pareadas por pregunta, no podemos separar variación muestral, sensibilidad del evaluador y efecto real del entrenamiento. La composición del corpus es una hipótesis que debe probarse mediante ablations y varias semillas, no una causa establecida.

### Límite de interpretación

Este resultado **no es el protocolo oficial de MMLU-Pro** y **no es comparable con su leaderboard**: RONIN puntúa la probabilidad del siguiente byte de las opciones A–J, sin cadena de razonamiento CoT. Es **una sola semilla** (1337), en un modelo tiny de **9.922.880 parámetros**, entrenado en **CPU** durante 1.000 pasos. Además, se evaluaron 11.687 de los 12.032 ítems seleccionados: 345 se omitieron por superar el contexto de 2.048 bytes, de modo que la cobertura fue 97,13 % y `complete_test_set=false`. Los resultados son una observación preliminar de este protocolo y esta ejecución; no prueban mejora general, causalidad por dominio ni superioridad frente a otros modelos.

Consulta el [artefacto de la ejecución](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41827976377/artifacts/13325455883) y el [protocolo de benchmarks](docs/BENCHMARKS_MULTIDOMINIO.md).

### Siguiente ciclo: benchmark reducido e instrumentación CPU

El workflow [RONIN + MMLU-Pro reducido](.github/workflows/ronin-small-mmlu-pro.yml) ya está integrado en `main` mediante la [PR #44](https://github.com/orbitalronin94/RONIN-IA/pull/44). Sus valores manuales por defecto son 1.000 pasos, semilla 1337 y muestra estratificada de 1.400 preguntas. **El workflow reducido todavía no se ha lanzado; requiere `Run workflow` manual.**

La preparación técnica incorpora:

- Muestreo de ventanas de tokens vectorizado, conservando el generador y el orden determinista de muestras.
- Control explícito de hilos PyTorch CPU: 4 intra-op y 1 inter-op en el runner estándar.
- Métricas por entrenamiento: duración total, latencia media/mediana/p95 por paso, mediana de estado estable, ejemplos/s, tokens/s y tiempo acumulado de checkpoints.
- Registro del hardware y de la configuración de PyTorch en el log de Actions.
- Prueba de regresión para comprobar que el sampler vectorizado conserva las mismas muestras.
- [Diseño técnico, métricas y criterios A/B de aceleración CPU](docs/OPTIMIZACION_ENTRENAMIENTO_CPU.md).
- [Plan de aceleración del entrenamiento CPU](docs/PLAN_ACELERACION_ENTRENAMIENTO_CPU.md): el perfilado real de RUN #4 mostró que 42 min 52 s de 46 min 51 s (91,5 %) fueron evaluaciones MMLU-Pro; los 1.000 pasos de entrenamiento ocuparon unos 2 min 26 s. La prioridad de ahorro de tiempo es el batching de evaluación, sin reducir el holdout final.

Los cambios están integrados y la CI de la revisión fusionada ha pasado. Aún no existe una medición A/B del speedup en el runner. No se afirma un factor de aceleración antes de comparar el mismo hardware, corpus, semilla y presupuesto. El sampler vectorizado reduce trabajo Python; las métricas y el control explícito de hilos quedan instrumentados en el workflow reducido, cuyo rendimiento todavía debe medirse. Esto no demuestra por sí solo que el forward/backward del Transformer sea más rápido.

Los cambios ya están integrados. El workflow reducido se inicia manualmente desde Actions; el test MMLU-Pro sigue siendo solo evaluación, nunca datos de entrenamiento. El artefacto publicará métricas e informes, no checkpoints.

### Últimas ejecuciones observadas

- [Experimento oficial #3](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41842575826): iniciado automáticamente al fusionar la PR #44; entrenamiento desde cero con 1.000 pasos y test MMLU-Pro completo. Está en curso. Este workflow oficial no pasa todavía `--metrics-out` ni los argumentos de hilos; las métricas nuevas están activadas en el workflow reducido, pendiente de dispatch manual.
- [CI #420](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41842364060): correcta sobre la revisión final de la PR #44.
- [PR #44](https://github.com/orbitalronin94/RONIN-IA/pull/44): fusionada en `main`; merge commit `3a47956f130262916e558094b4b09c9498f2bb3f`.
- El workflow reducido MMLU-Pro de 1.400 preguntas está integrado, pero sigue pendiente de ejecución manual.
El inventario completo, con procedencia, revisiones, licencias, particiones, exclusiones y hashes, está en [Inventario de corpus y materiales](docs/INVENTARIO_CORPUS_Y_MATERIALES.md) y en el [manifiesto JSON](data/manifests/corpus_inventory.json).

## Principios irrenunciables

1. **RONIN aprende desde cero.** Todos los pesos del modelo estudiante se inicializan aleatoriamente. No se importan, mezclan ni ajustan pesos de modelos externos dentro de RONIN.
2. **Tutores locales, no dependencias remotas.** Se permiten modelos auxiliares descargables, gratuitos y con licencia MIT verificada. Se ejecutan localmente y solo aportan texto de entrenamiento. Sus pesos nunca se incorporan al estudiante.
3. **Licencia comprobada antes de descargar.** El descargador consulta la ficha del modelo, exige la etiqueta exacta `mit`, fija una revisión inmutable y guarda huellas SHA-256. Si la licencia no se verifica, cancela la descarga.
4. **Un proceso, varias escalas.** Los perfiles tiny, seed-0, seed-1 y seed-2 comparten la misma canalización. El tamaño se define mediante configuraciones validadas.
5. **Reproducibilidad.** Cada experimento registra semillas, manifiestos de datos, versión del tokenizador, configuración, versiones de software y hardware.
6. **Evidencias antes que etiquetas.** Una función solo se declara activa cuando existe una implementación ejecutable y pruebas que la cubren. Una declaración en el manifiesto, una interfaz o una hoja de ruta no demuestran que funcione.
7. **Honestidad experimental.** No se presentan pruebas sintéticas ni ejecuciones diminutas como modelos competentes. No se inventan métricas, velocidad, costes ni resultados.
8. **Gobernanza de datos.** Cada corpus registra procedencia, licencia, permisos, filtrado y deduplicación.

## Modelos auxiliares MIT

El ecosistema incluye tres modelos auxiliares descargables, con licencia MIT verificada:

| Alias | Modelo | Parámetros aproximados | Licencia declarada |
|---|---|---:|---|
| `gpt2` | `openai-community/gpt2` | 124 M | MIT |
| `gpt-neo-125m` | `EleutherAI/gpt-neo-125m` | 125 M | MIT |
| `phi-4-mini-instruct` | `microsoft/Phi-4-mini-instruct` | 3,8 B | MIT |

Fichas oficiales: [GPT-2](https://huggingface.co/openai-community/gpt2) · [GPT-Neo 125M](https://huggingface.co/EleutherAI/gpt-neo-125m).

**Advertencia:** GPT-2 y GPT-Neo son modelos de base principalmente anglófonos; Phi-4 es instruct y multilingüe, pero su calidad en castellano debe medirse. Todos sirven como tutores auxiliares locales, no como pesos del estudiante. La calidad y los derechos de cualquier texto generado deben revisarse antes de entrenar.

Los modelos se descargan una vez en `models/teachers/` y se reutilizan desde disco. No se consulta ninguna API de generación durante el entrenamiento. Las dependencias de tutores son opcionales:

```bash
pip install -e '.[teachers]'
python scripts/download_teacher_models.py --model gpt2
python scripts/download_teacher_models.py --model gpt-neo-125m
python scripts/download_teacher_models.py --model phi-4-mini-instruct
```

La guía completa está en [Modelos auxiliares locales](docs/TEACHER_WORKFLOW.md). Phi-4 utiliza `trust_remote_code=True`; su código remoto requiere revisión y aislamiento. La licencia MIT del modelo no se atribuye automáticamente al texto generado.

## Arquitectura del estudiante

El modelo estudiante es un Transformer causal decoder-only implementado en PyTorch. La arquitectura incorpora RoPE, RMSNorm, SwiGLU y atención agrupada por consultas (GQA configurable). Los embeddings de tokens y la proyección de salida comparten pesos.

Todos los pesos se inicializan localmente. No se cargan pesos de tutores ni checkpoints externos en el constructor del modelo. Los tutores aportan, como máximo, ejemplos de texto con procedencia registrada.

## Escalera de desarrollo de RONIN

El entorno operativo de referencia es GitHub Actions estándar para repositorios públicos (`ubuntu-latest`): 4 vCPU, 16 GB de RAM y 14 GB SSD nominales, sin GPU CUDA. Cada trabajo usa una máquina virtual nueva y efímera. Las cifras publicadas son especificaciones de referencia; el workflow registra los recursos observados en cada ejecución. Consulta [Hardware y runners gratuitos](docs/HARDWARE.md).

| Perfil | Parámetros objetivo | Situación actual |
|---|---:|---|
| tiny | 9.922.880 | Perfil de referencia para pruebas y experimentos CPU pequeños |
| seed-0 | 147.092.736 | No validado para entrenamiento en el runner gratuito |
| seed-1 | 955.221.504 | Fuera del entorno operativo actual |
| seed-2 | 6.976.598.016 | Fuera del entorno operativo actual |

Los perfiles son objetivos de arquitectura, no garantías de memoria, duración ni rendimiento. Los recuentos deben verificarse con `ronin count-params --profile PERFIL`.

## Filtro epistémico REF

RONIN incorpora el diseño inicial del **Filtro Epistémico de RONIN (REF)** para distinguir afirmaciones contrastables, contenido simbólico, formulaciones no falsables y casos indeterminados. REF mantiene separados el género textual y el estado de codificación: un texto extraño o arcaico puede contener nomenclatura técnica, cifrado o convenciones históricas aún no interpretadas. No se clasifica una obra entera por su género y no se trata ningún contenido como «negativo» por ser religioso o metafórico. Consulta [la política y el esquema REF](docs/FILTRO_EPISTEMICO_REF.md).

## Implementación inicial

- Transformer causal decoder-only en PyTorch con RoPE, RMSNorm, SwiGLU y GQA configurable.
- Tokenizador de bytes y lotes deterministas para predicción del siguiente token.
- Entrenador AdamW compartido, acumulación de gradientes, recorte, calentamiento y decaimiento coseno.
- Protección ante pérdidas y gradientes no finitos.
- Guardado atómico de checkpoints y reanudación con estado del optimizador y generadores aleatorios.
- Generación autorregresiva, métricas de pérdida, perplejidad y bits por byte.
- Registro de capacidades con evidencias y comandos de diagnóstico.
- Pruebas unitarias y flujo de integración continua.

La canalización completa de corpus con procedencia, el tokenizador aprendido, el entrenamiento distribuido y la evaluación de producción siguen pendientes. Un objetivo declarado no equivale a una función implementada.

## Inicio rápido

Se requiere Python 3.11 o posterior.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e '.[dev]'
pytest
ruff check ronin tests scripts
```

Comandos útiles:

```bash
ronin info --profile tiny
ronin count-params --profile tiny
ronin features
ronin readiness --profile tiny
ronin matrix
ronin roadmap
```

Entrenamiento del perfil tiny con un corpus UTF-8 autorizado:

```bash
python scripts/train_text.py --text /ruta/corpus-aprobado.txt --profile tiny --steps 100
```

El tokenizador de bytes es una base provisional. Este comando no crea una separación entre entrenamiento, validación y prueba; su pérdida no es una evaluación independiente.

## Estructura del repositorio

```text
configs/                 Perfiles versionados de modelo y entrenamiento
data/manifests/          Manifiestos de procedencia y licencias de corpus
data/raw/                Datos locales (no subir datos privados)
data/processed/          Fragmentos procesados locales
docs/                    Arquitectura, datos, entrenamiento y hoja de ruta
models/teachers/         Modelos auxiliares MIT descargados (no versionar)
ronin/manifest/          Registro de funciones y estado de preparación
ronin/models/            Arquitectura Transformer y recuento de parámetros
ronin/tokenizer/         Implementaciones de tokenizadores
ronin/data/              Lectura de conjuntos de datos y generación tutorizada
ronin/training/          Entrenador, optimizador, planificadores y checkpoints
ronin/evaluation/        Métricas y utilidades de evaluación
ronin/inference/         Muestreo y generación
ronin/utils/             Utilidades de reproducibilidad
scripts/                 Comandos reproducibles para desarrollo y operación
tests/                   Pruebas unitarias y de integración
.github/workflows/       Integración continua
```

## Documentación principal

- [Arquitectura](docs/ARCHITECTURE.md)
- [Manifiesto de capacidades](docs/MANIFEST.md)
- [Gobernanza de datos](docs/DATA.md)
- [Operaciones de entrenamiento](docs/TRAINING.md)
- [Evaluación](docs/EVALUATION.md)
- [Planificación de hardware](docs/HARDWARE.md)
- [Hoja de ruta](docs/ROADMAP.md)
- [Modelos auxiliares locales](docs/TEACHER_WORKFLOW.md)
- [Auditoría e integración del código de referencia](docs/AUDIT_INTEGRATION.md)

## Reglas de evaluación

- Informar pérdida de validación y perplejidad junto con la identidad del tokenizador y corpus.
- Usar BPB al comparar tokenizadores; la perplejidad no es directamente comparable entre tokenizadores distintos.
- Mantener separados los datos de entrenamiento, validación y prueba.
- Una prueba diminuta de memorización no demuestra generalización.
- Informar referencias y variabilidad cuando proceda.
- No fabricar resultados de benchmarks.

## Reglas de contribución

Trabajar en ramas pequeñas y commits secuenciales. Leer el contenido actual antes de sustituir un archivo. Ejecutar las pruebas pertinentes tras cada cambio coherente. No subir secretos, corpus privados, checkpoints ni conjuntos de datos generados. Si no se puede ejecutar un comando en el entorno disponible, indicarlo y proporcionar el comando exacto para una máquina adecuada.

## Licencia

Consultar [LICENSE](LICENSE). Las licencias de los datos y de cada modelo auxiliar son independientes de la licencia del software y deben registrarse por separado.


## Biblioteca de codificación documentada

El catálogo crítico de criptografía, esteganografía y acrósticos históricos y literarios está en [`docs/CASOS_CODIFICACION_DOCUMENTADA.md`](docs/CASOS_CODIFICACION_DOCUMENTADA.md). Distingue descifrados documentados, interpretaciones de acrósticos, criptogramas ficticios y afirmaciones pendientes de verificación; no es todavía un corpus de entrenamiento.

## Biblioteca de patrones de opacidad y codificación

RONIN mantiene una biblioteca separada del corpus lingüístico general y del
router. Su unidad es el par **fragmento opaco + evidencia de interpretación**,
con mecanismo, estado de evidencia, procedencia, licencia, SHA-256, confianza
y partición. El contrato está en `ronin/epistemic/obfuscation.py` y la primera
construcción reproducible en
`scripts/build_obfuscation_cases.py`. Consulta
[la documentación de casos y criterios](docs/CASOS_CODIFICACION_DOCUMENTADA.md).

Los negativos de esta primera tanda son controles sintéticos con semilla
reproducible y sin carga útil insertada. Un texto histórico no resuelto —como
el manuscrito Voynich— no se convierte en negativo por defecto. Las
transcripciones sin licencia compatible quedan fuera del entrenamiento.

## Cierre: la advertencia del README

> Nota editorial: se conserva aquí como texto satírico heredado, no como especificación técnica. La referencia histórica a «cuarenta y cuatro millones» no describe el perfil tiny actual, que tiene 9.922.880 parámetros.

> Sepan cuantos este repositorio vieren que aquí se hace escarnio de cuanto los doctos predicaron sobre acrecentar modelos. Non hay hueste de tarjetas gráficas, nin caudal de dineros, nin ley del escalado que valga. Hay un ingenio de cuarenta y cuatro millones que apenas distingue el saludo del mandado, y un artificio de trazas que non se rompe.
>
> Al modelo non le tengo ley, ca es ruin y él lo sabe. Al artificio se la tengo entera.
>
> Quien viniere por el modelo, tórnese por do vino, que aquí non hay sino el método. Quien viniere por las trazas, quédese, mas sepa desde luego que el método es largo y el modelo, corto. Non me pidáis que lo aderece, que quien se consuela con el modelo es porque non ha mirado las trazas.

### Nota de léxico

*Sepan cuantos… vieren* abre como las cartas de privilegio y las Partidas, y avisa de que lo que sigue no es un README sino un edicto. *Escarnio* es burla pública, no ironía fina. *Non* en vez de *no* es licencia arcaizante, no error: aparece en Berceo y en el Cantar. *Ca* por *porque* es la conjunción causal del mester de clerecía. *Do vino* por *de donde vino*. *Aderezar* por *arreglar o maquillar* es el uso de los plateros y los cocineros del XVII. Y *tener ley a alguien* es tenerle lealtad, que es lo que se le niega al modelo y se le concede al pipeline.

El cierre es la única línea que no es arcaica, y está puesta a propósito: el que llega al final ya no necesita el disfraz. 


## Registro ampliado de datasets externos (4 de noviembre de 2026)

Se ha añadido un inventario de **21 fuentes** para ampliar la cobertura semántica en ciencia, medicina, derecho, ingeniería, código, humanidades, economía, lingüística, traducción y conocimiento estructurado. Consulta el [manifiesto](data/manifests/external_datasets.json) y la [política de ingesta y derechos](docs/INGESTA_AMPLIA_DATASETS_EXTERNOS.md).

Este inventario no significa que los 21 corpus estén descargados o admitidos: distingue fuentes ya presentes, candidatos, índices y recursos condicionados por licencia. Todos permanecen con `training_eligible=false` hasta superar la puerta G-0. El validador [scripts/validate_external_datasets.py](scripts/validate_external_datasets.py) comprueba el manifiesto sin descargar datos ni iniciar entrenamiento.


## Libro de ejecuciones y nuevas ingestas

El historial cronológico de experimentos, validaciones e ingestas está en el [Libro de runs](docs/RUNS.md). Los workflows enlazan allí desde su resumen y el registrador automático añade cada ejecución al terminar, incluidos fallos y cancelaciones.

El inventario externo contiene ahora 22 fuentes. La ingesta candidata combina Common Corpus, datos CC0 de Wikidata y texto completo JATS de PMC Cloud bajo CC0/CC BY verificado por versión; los candidatos permanecen fuera del entrenamiento hasta superar la revisión G-0. Consulta [el pipeline de muestras](docs/INGESTA_AMPLIA_DATASETS_EXTERNOS.md#primera-ingesta-automatizada-de-muestras) y [el adaptador PMC](docs/FUENTE_PMC_OA.md).
