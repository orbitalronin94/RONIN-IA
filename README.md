# RONIN-IA

**RONIN** es un proyecto de investigación e ingeniería de modelos de lenguaje. Su propósito es comprobar hasta dónde puede llegar una arquitectura propia entrenada desde una inicialización aleatoria, con un proceso reproducible de datos, entrenamiento, evaluación y despliegue.

- Repositorio: https://github.com/orbitalronin94/RONIN-IA
- Rama principal: `main`
- Fuente de verdad: este repositorio. El código, las pruebas, las configuraciones y la documentación operativa viven aquí.
- Estado: ya existe un modelo estudiante propio, implementado en PyTorch, y se ha completado un primer ciclo de entrenamiento experimental. El proyecto sigue en fase de investigación; no se afirma todavía competencia general.

## Estado actual del modelo

**RONIN ya tiene modelo propio.** No es únicamente una hoja de ruta ni una colección de especificaciones: el repositorio contiene un Transformer causal decoder-only implementado en PyTorch, con inicialización propia y **9.922.880 parámetros en el perfil `tiny`**. Su arquitectura actual combina RoPE, RMSNorm, SwiGLU y GQA configurable.

También se ha ejecutado un primer ciclo reproducible de entrenamiento desde inicialización aleatoria. En el smoke test de CI (100 pasos, CPU, una semilla y corpus artificial aislado) se observó:

| Medición | Antes | Después |
|---|---:|---:|
| Bits por byte (BPB) | 7,9281 | 2,2395 |
| Aciertos en el piloto multidominio | 0/23 | 8/23 (34,78 %) |

La evaluación de lenguaje utilizó 32.768 bytes de validación. El benchmark multidominio contiene 23 preguntas de opción múltiple y se puntúa mediante predicción del siguiente byte.

**Cómo interpretar estos datos:** son evidencia de que el código de entrenamiento y evaluación funciona y de que el modelo aprende regularidades del corpus sintético. No demuestran conocimiento general, razonamiento, dominio de 15 disciplinas ni rendimiento comparable al de otros modelos. El corpus artificial y el benchmark pequeño no permiten esas conclusiones. Hace falta repetir con varias semillas, ampliar las pruebas independientes y evaluar tareas abiertas con criterios explícitos.

Los ciclos sintéticos no descargan corpus externos y no eluden el bloqueo G-0 de licencias. Los informes se publican como artefactos de GitHub Actions; los checkpoints no se publican ni se conservan como pesos descargables. Por tanto, **hay un modelo implementado y entrenado experimentalmente, pero todavía no distribuimos un checkpoint entrenado como versión utilizable**.

Workflow: [Ciclos sintéticos de entrenamiento RONIN](https://github.com/orbitalronin94/RONIN-IA/actions/workflows/synthetic-training-cycles.yml). Para lanzar experimentos más largos, abre el workflow en GitHub Actions y usa «Run workflow» (hasta 1.000 pasos y cinco semillas).



## La advertencia del README

> Sepan cuantos este repositorio vieren que aquí se hace escarnio de cuanto los doctos predicaron sobre acrecentar modelos. Non hay hueste de tarjetas gráficas, nin caudal de dineros, nin ley del escalado que valga. Hay un ingenio de cuarenta y cuatro millones que apenas distingue el saludo del mandado, y un artificio de trazas que non se rompe.
>
> Al modelo non le tengo ley, ca es ruin y él lo sabe. Al artificio se la tengo entera.
>
> Quien viniere por el modelo, tórnese por do vino, que aquí non hay sino el método. Quien viniere por las trazas, quédese, mas sepa desde luego que el método es largo y el modelo, corto. Non me pidáis que lo aderece, que quien se consuela con el modelo es porque non ha mirado las trazas.

### Nota de léxico

*Sepan cuantos… vieren* abre como las cartas de privilegio y las Partidas, y avisa de que lo que sigue no es un README sino un edicto. *Escarnio* es burla pública, no ironía fina. *Non* en vez de *no* es licencia arcaizante, no error: aparece en Berceo y en el Cantar. *Ca* por *porque* es la conjunción causal del mester de clerecía. *Do vino* por *de donde vino*. *Aderezar* por *arreglar o maquillar* es el uso de los plateros y los cocineros del XVII. Y *tener ley a alguien* es tenerle lealtad, que es lo que se le niega al modelo y se le concede al pipeline.

El cierre es la única línea que no es arcaica, y está puesta a propósito: el que llega al final ya no necesita el disfraz.


## Principios irrenunciables

1. **RONIN aprende desde cero.** Todos los pesos del modelo estudiante se inicializan aleatoriamente. No se importan, mezclan ni ajustan pesos de modelos externos dentro de RONIN.
2. **Tutores locales, no dependencias remotas.** Se permiten modelos auxiliares descargables, gratuitos y con licencia MIT verificada. Se ejecutan localmente y solo aportan texto de entrenamiento. Sus pesos nunca se incorporan al estudiante.
3. **Licencia comprobada antes de descargar.** El descargador consulta la ficha del modelo, exige la etiqueta exacta `mit`, fija una revisión inmutable y guarda huellas SHA-256. Si la licencia no se verifica, cancela la descarga.
4. **Un proceso, varias escalas.** Los perfiles tiny, seed-0, seed-1 y seed-2 comparten la misma canalización. El tamaño se define mediante configuraciones validadas.
5. **Reproducibilidad.** Cada experimento registra semillas, manifiestos de datos, versión del tokenizador, configuración, versiones de software y hardware.
6. **Evidencias antes que etiquetas.** Una función solo está activa cuando existe implementación y pruebas. Una declaración en el manifiesto no demuestra que funcione.
7. **Honestidad experimental.** No se presentan pruebas sintéticas ni ejecuciones diminutas como modelos competentes. No se inventan métricas, velocidad, costes ni resultados.
8. **Gobernanza de datos.** Cada corpus registra procedencia, licencia, permisos, filtrado y deduplicación.

## Modelos auxiliares MIT

El punto de partida incluye dos modelos de tamaño reducido, disponibles en Hugging Face bajo licencia MIT:

| Alias | Modelo | Parámetros aproximados | Licencia declarada |
|---|---|---:|---|
| `gpt2` | `openai-community/gpt2` | 124 M | MIT |
| `gpt-neo-125m` | `EleutherAI/gpt-neo-125m` | 125 M | MIT |
| `phi-4-mini-instruct` | `microsoft/Phi-4-mini-instruct` | 3,8 B | MIT |

Fichas oficiales: [GPT-2](https://huggingface.co/openai-community/gpt2) · [GPT-Neo 125M](https://huggingface.co/EleutherAI/gpt-neo-125m) · [Phi-4 mini instruct](https://huggingface.co/microsoft/Phi-4-mini-instruct).

**Advertencia:** GPT-2 y GPT-Neo 125M son modelos de base principalmente anglófonos. Phi-4 mini instruct está ajustado para seguir instrucciones y declara soporte para español, pero su entrenamiento también es predominantemente inglés y no es un experto infalible. Las salidas son propuestas sintéticas: REF solo comprueba su estructura, no su verdad. La licencia MIT corresponde al modelo y no se atribuye automáticamente al texto generado; no se publican esos lotes sin una revisión independiente de sus derechos.

Los modelos se descargan una vez en `models/teachers/` y se reutilizan desde disco. No se consulta ninguna API de generación durante el entrenamiento. Las dependencias de tutores son opcionales:

```bash
pip install -e '.[teachers]'
python scripts/download_teacher_models.py --model gpt2
python scripts/download_teacher_models.py --model gpt-neo-125m
python scripts/download_teacher_models.py --model phi-4-mini-instruct
```

La guía completa está en [Modelos auxiliares locales](docs/TEACHER_WORKFLOW.md).

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

Los perfiles son objetivos de arquitectura, no garantías de memoria, duración ni rendimiento. Los recuentos deben verificarse con `ronin count-params --profile PERFIL`. El concepto MoE de 2,8 billones de parámetros queda fuera de la primera escalera.

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
