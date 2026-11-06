# RONIN-IA

**Un modelo propio. Un pipeline experimental. Un corpus trazable.**

RONIN es un modelo causal Transformer implementado en PyTorch. El proyecto investiga cómo mejorar un modelo pequeño mediante entrenamiento reproducible, adquisición de corpus abiertos y evaluación pareada.

> **El proceso de entrenamiento todavía es experimental.** No existe una receta única ni un protocolo definitivo fijado. Cambiamos pasos, semillas, mezclas de datos, estrategias de selección y profundidad de evaluación entre experimentos. La configuración efectiva de cada ejecución está en su workflow, en los inputs del run y en sus artefactos.

## Estado del proyecto

### Modelo de referencia en `main`

El checkpoint versionado en `main` es la **línea base operativa**, no una afirmación de que sea el mejor candidato posible ni una receta de entrenamiento que debamos repetir sin cambios.

- Nombre: **RONIN-tiny-seed95-100-001**.
- Arquitectura: Transformer causal con RoPE, RMSNorm, SwiGLU, GQA y tokenización byte-v1.
- Parámetros: 9.922.880.
- Checkpoint de origen: 100 pasos, semilla 95; el manifiesto conserva hashes, procedencia y configuración.
- Pesos compactos: `weights/ronin-main.pt`; identidad y procedencia: `weights/main-model.json`.

La evaluación que acompañó a esa línea base registró:

| Métrica | Antes | Después | Lectura |
|---|---:|---:|---|
| Validación interna BPB | 4,5654 | 4,3373 | Mejora en el corpus de validación interna |
| Validación interna PPL | 23,6764 | 20,2137 | Mejora en predicción del texto evaluado |
| MMLU-Pro validation (50 preguntas) | 5/50 | 7/50 | Screening pequeño; no es el test oficial |

El screening de 50 preguntas se clasificó como `SCREENING_ONLY`. No demuestra razonamiento general ni sustituye una evaluación completa e independiente. Los detalles y hashes vigentes están en [`weights/main-model.json`](weights/main-model.json).

### Entrenamiento: experimentación, no receta fija

Los workflows son experimentos con objetivos y presupuestos diferentes. No deben interpretarse como etapas obligatorias de un único pipeline ni como una configuración estable:

| Workflow | Propósito | Qué puede variar |
|---|---|---|
| [Cribado multi-semilla sin tutor](.github/workflows/main-native-no-tutor-holdout.yml) | Partir de los pesos propios, entrenar candidatos y compararlos con los mismos holdouts | Pasos, semillas y límite/profundidad de evaluación mediante inputs |
| [Torneo adaptativo de 50 semillas](.github/workflows/adaptive-50-seed-tournament.yml) | Explorar distintas semillas y seleccionar candidatos para análisis posterior | Estrategia y selección del torneo según el workflow versionado |
| [Corpus semilla 202, 500 pasos](.github/workflows/micro-corpus-4-seeds.yml) | Experimento específico asociado a cambios de corpus | Semilla y presupuesto están fijados por el diseño de este experimento |

También pueden existir ejecuciones experimentales lanzadas desde ramas o PR que no estén integradas en `main`. Por ejemplo, los experimentos de mayor duración —como el de 10.000 pasos— deben leerse desde su ejecución concreta y no confundirse con el workflow general disponible en la rama principal.

**Consulta el [historial de GitHub Actions](https://github.com/orbitalronin94/RONIN-IA/actions) para conocer qué se ha ejecutado realmente.** Cada run es la referencia para su commit, workflow, inputs, pasos, conclusión y artefactos. Un nombre de workflow o un valor por defecto no define por sí solo el proceso completo del proyecto.

### Cómo interpretamos los resultados

- Una ejecución correcta de Actions significa que el workflow terminó; no significa que el modelo haya mejorado.
- Una bajada de loss, BPB o perplexity es evidencia sobre la distribución evaluada, no prueba suficiente de razonamiento.
- Los candidatos no sustituyen automáticamente al checkpoint de `main`.
- La promoción exige revisar el benchmark pareado, el holdout, la integridad del checkpoint y las métricas relevantes.
- No se deben comparar puntuaciones obtenidas con diferentes preguntas, splits o protocolos como si fueran equivalentes.
- Los resultados de screening se etiquetan como tales; no se presentan como certificación oficial.

## Corpus y datos entrenables

La raíz canónica de datos es `data/datasets/`. Su [README de corpus](data/datasets/README.md) mantiene el inventario detallado de fuentes, documentos, bytes, bibliotecas, particiones y controles.

El corpus de entrenamiento evoluciona a medida que se adquieren y admiten fuentes. Por eso, los recuentos del inventario son una fotografía documental y no deben atribuirse retroactivamente a checkpoints entrenados con cortes anteriores.

Un documento descargado no es automáticamente entrenable. Se requiere procedencia, derechos compatibles, integridad del payload, controles aplicables y asignación explícita a la partición train. Validation y test deben permanecer fuera de los gradientes. Los límites de admisión por fuente no equivalen a una certificación global del corpus: los manifiestos describen exactamente qué controles han pasado y cuáles siguen pendientes.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `weights/` | Identidad, procedencia, hashes y pesos del modelo de referencia |
| `data/datasets/` | Corpus, bibliotecas, particiones, manifiestos y registros de derechos |
| `ronin/` | Arquitectura, tokenizador, datos, entrenamiento y evaluación |
| `scripts/` | Herramientas para entrenar, preparar datos y evaluar |
| `configs/` | Configuraciones de arquitectura |
| `.github/workflows/` | Experimentos, adquisición de datos y controles automatizados |
| `docs/` | Protocolo, decisiones y documentación técnica |

## Entrenamiento local

Requisitos orientativos del entorno actual: Python 3.11 y PyTorch 2.2 o posterior.

```bash
python -m pip install -e '.[dev]'
pytest -q
```

El script `scripts/train_text.py` permite ejecutar un entrenamiento local sobre texto UTF-8 autorizado:

```bash
python scripts/train_text.py --text /ruta/al/corpus.txt --profile tiny --steps 500
```

Este comando es una vía de ejecución local, no el protocolo oficial ni una configuración recomendada para todos los experimentos. Consulta [docs/TRAINING.md](docs/TRAINING.md) y el workflow concreto antes de interpretar o reproducir un resultado.

Para el protocolo de evaluación externo, consulta [MMLU-Pro y su protocolo](docs/HOLDOUT_EXTERNO_MMLU_PRO.md).

## Principios

- **Evidencia antes que promoción.** Ningún candidato pasa a ser modelo principal solo por completar el entrenamiento.
- **Experimentos explícitos.** Cada run debe poder relacionarse con su workflow, commit, inputs, corpus y artefactos.
- **Mismo holdout antes y después.** Las comparaciones pareadas deben mantener preguntas, splits y protocolo.
- **Datos trazables.** Adquisición, admisión y elegibilidad de entrenamiento son estados diferentes.
- **Sin atribuciones retroactivas.** Un corpus incorporado después no se atribuye a entrenamientos anteriores.
- **Sin receta prematura.** El proceso seguirá cambiando mientras estemos explorando qué configuración mejora realmente el modelo.

## Aviso

> Sepan cuantos este repositorio vieren que aquí se hace escarnio de cuanto los doctos predicaron sobre acrecentar modelos. Non hay hueste de tarjetas gráficas, nin caudal de dineros, nin ley del escalado que valga. Hay un ingenio de nueve millones que apenas distingue el saludo del mandado, y un artificio de trazas que non se rompe.
>
> Al modelo non le tengo ley, ca es ruin y él lo sabe. Al artificio se la tengo entera.
>
> Quien viniere por el modelo, tórnese por do vino, que aquí non hay sino el método. Quien viniere por las trazas, quédese, mas sepa desde luego que el método es largo y el modelo, corto. Non me pidáis que lo aderece, que quien se consuela con el modelo es porque non ha mirado las trazas.
