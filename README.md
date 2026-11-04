# RONIN-IA

**RONIN** es un proyecto de investigación e ingeniería de modelos de lenguaje. Su propósito es comprobar hasta dónde puede llegar una arquitectura propia entrenada desde una inicialización aleatoria, con un proceso reproducible de datos, entrenamiento, evaluación y despliegue.

- Repositorio: https://github.com/orbitalronin94/RONIN-IA
- Rama principal: `main`
- Fuente de verdad: este repositorio. El código, las pruebas, las configuraciones y la documentación operativa viven aquí.
- Estado: implementación inicial. Ninguna función se considera terminada sin código, pruebas y evidencias.

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

Fichas oficiales: [GPT-2](https://huggingface.co/openai-community/gpt2) · [GPT-Neo 125M](https://huggingface.co/EleutherAI/gpt-neo-125m).

**Advertencia:** ambos son modelos de base principalmente anglófonos. Sirven para probar la descarga, inferencia local, generación y trazabilidad; no se debe presuponer que producirán buenas explicaciones en castellano. La calidad de cada corpus generado debe revisarse antes de entrenar.

Los modelos se descargan una vez en `models/teachers/` y se reutilizan desde disco. No se consulta ninguna API de generación durante el entrenamiento. Las dependencias de tutores son opcionales:

```bash
pip install -e '.[teachers]'
python scripts/download_teacher_models.py --model gpt2
python scripts/download_teacher_models.py --model gpt-neo-125m
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
