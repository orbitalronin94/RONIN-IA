<div align="center">

# RONIN-IA

### Investigación abierta sobre modelos pequeños, corpus trazables y entrenamiento verificable.

**Un modelo propio. Datos auditables. Experimentos sin atajos.**

[Modelo y pesos](weights/) · [Biblioteca de datasets](data/datasets/) · [Experimentos](https://github.com/orbitalronin94/RONIN-IA/actions) · [Documentación](docs/)

</div>

---

## Aviso del escribano

**Sepan cuantos este aviso leyeren:** RONIN-IA mantiene dos tamaños que no deben confundirse. El modelo actualmente fijado en **main** tiene **9.922.880 parámetros**; **Ronin - Drosophila tiene 100.900.160 parámetros y permanece como candidato experimental, no como modelo promocionado en main**. La expansión ×10,17 conserva funcionalmente los logits antes de continuar el entrenamiento, pero sus 500 pasos posteriores no acreditan por sí solos una mejora de capacidad general.

Las métricas de cada régimen se conservan con su procedencia y no se comparan como si procedieran del mismo presupuesto. El screening de Drosophila no certifica razonamiento general. **Este proyecto documenta experimentos; no proclama capacidades que sus pruebas no han medido.**

## En dos minutos

RONIN es un modelo causal Transformer implementado en PyTorch. Explora cuánto puede aprender un modelo pequeño a partir de corpus abiertos o autorizados, con procedencia documentada y evaluaciones reproducibles.

> **El entrenamiento sigue siendo experimental.** No existe una receta única: pasos, semillas, arquitectura, mezcla de datos y profundidad de evaluación cambian según la hipótesis. El workflow, sus inputs, logs y artefactos son la fuente de verdad de cada ejecución.

### Accesos principales

| Área | Qué encontrarás |
|---|---|
| [Biblioteca de datasets](data/datasets/README.md) | Inventario, bibliotecas, fuentes, derechos, particiones y estado entrenable |
| [Manifiestos](data/datasets/) | Payloads, hashes y trazabilidad por fuente |
| [Pesos de main](weights/ronin-main.pt) | Paquete PyTorch del modelo actualmente fijado en main |
| [Manifiesto de main](weights/main-model.json) | Arquitectura, parámetros, hashes, procedencia y evaluación |
| [Manifiesto Drosophila](weights/ronin-drosophila-100900160-candidate.json) | Identidad, checkpoint, corpus declarado y screening |
| [Experimentos](https://github.com/orbitalronin94/RONIN-IA/actions) | Runs, workflows, logs y artefactos |
| [Historial experimental](docs/EXPERIMENT_HISTORY.md) | Evolución de modelos y evidencia |
| [Reproducibilidad](docs/REPRODUCIBILITY.md) | Checkpoints, hashes, seeds y costes |
| [Procedencia del corpus](docs/CORPUS_PROVENANCE.md) | Fuentes que vio cada checkpoint |
| [Métricas](docs/METRICS.md) | Tokens, BPB, perplexity, holdout y comparabilidad |

## Estado de los modelos

### Modelo fijado en main: línea base compacta

| Propiedad | Valor |
|---|---|
| Identificador | RONIN-tiny-seed95-100-001 |
| Parámetros | **9.922.880 (~9,9 M)** |
| Arquitectura | Transformer causal, RoPE, RMSNorm, SwiGLU y GQA |
| Tokenización | byte-v1 |
| Checkpoint de origen | 100 pasos, seed 95 |
| Pesos | [weights/ronin-main.pt](weights/ronin-main.pt) |
| Manifiesto | [weights/main-model.json](weights/main-model.json) |
| Estado | **Modelo operativo de main** |

La validación interna registrada para ese régimen pasó de **4,5654 a 4,3373 BPB** y de **23,6764 a 20,2137 de perplexity**. Son métricas de predicción sobre la validación interna de aquel experimento; no son métricas de Drosophila ni una evaluación independiente de razonamiento.

Su screening MMLU-Pro fue de 50 preguntas de validation: 5/50 → 7/50. Se etiqueta SCREENING_ONLY; no es el test oficial completo.

### Candidato experimental: Ronin - Drosophila

**Nombre oficial:** **Ronin - Drosophila (100.900.160 parámetros)**  
**Identificador:** Ronin-Drosophila-100900160

| Propiedad | Valor verificado |
|---|---|
| Parámetros | **100.900.160** (×10,168 respecto a la base) |
| Arquitectura | Transformer causal; RoPE, RMSNorm, GQA y SwiGLU ampliado |
| Tokenizador | byte-v1 |
| Ancho SwiGLU | 854 → 12.700 canales |
| Base de expansión | [Run #42181780771](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42181780771), seed 95, 10.000 pasos |
| Continuación | [Run #42198068241](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42198068241), 500 pasos |
| Dispositivo | CPU, GitHub Actions, 2 hilos configurados |
| Checkpoint SHA-256 | 7d9345ecb9e3d7ad22aa628b93324ffd18e7b8a477f2d24c04885eced587d2f3 |
| Artefacto | [Checkpoint e informe](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42198068241/artifacts/13494355120) |
| Manifiesto | [ronin-drosophila-100900160-candidate.json](weights/ronin-drosophila-100900160-candidate.json) |

La expansión superó la prueba de conservación funcional: diferencia máxima absoluta de logits **1,4305×10⁻⁶** antes del entrenamiento. Esto demuestra que la operación de ensanchamiento preservó aproximadamente la función inicial en la prueba declarada; no demuestra que el entrenamiento posterior mejore el modelo.

**Clasificación de evidencia: MODEL_ORGANISM_ONLY + SCREENING_ONLY. No certifica razonamiento general.** El screening pareado MMLU-Pro de 64 preguntas de validation dio **5/64 antes y 5/64 después (0 puntos porcentuales)**. No es un full holdout. G-0 global sigue FAIL; near-duplicates globales y contaminación de holdout siguen PENDING.

Drosophila es un organismo modelo experimental: una arquitectura mayor, investigable en CPU y documentada de forma reproducible, sobre la que estudiar qué cambia al ampliar capacidad. El nombre no implica madurez, superioridad ni transferencia ya demostrada.

### El experimento de 10.000 pasos: evidencia histórica separada

El checkpoint de 10.000 pasos que sirve de origen a Drosophila es una etapa distinta, todavía en el régimen de 9,9M parámetros:

- Run [#42181780771](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42181780771); seed 95; 10.000 pasos; loss final **2,11482**.
- Corpus registrado: **279.352 unidades train-scoped y 256.612.919 bytes combinados**. No atribuirle fuentes incorporadas después.
- MMLU-Pro test pareado: **1.295/12.032 → 1.314/12.032** (10,763 % → 10,921 %; +0,158 puntos porcentuales).
- BPB: **3,8152 → 2,9798**.

Esos resultados pertenecen al checkpoint de 9,9M antes de la expansión. No son resultados de Drosophila. La ganancia MMLU-Pro es modesta y el uso repetido de un holdout para seleccionar experimentos puede producir contaminación por selección.

## Tokens y presupuesto: no confundir corpus con exposición

El corpus declarado en el manifiesto Drosophila contiene **286.468 documentos/segmentos y 685.023.414 bytes**. El script de expansión usa el perfil tiny, cuya longitud de secuencia es **128 bytes/tokens**, batch 1, sin acumulación de gradiente, durante 500 pasos.

La continuación representa **64.000 posiciones de entrada muestreadas** (500 × 128), con ventanas aleatorias y con reemplazo. No significa que el modelo haya recorrido secuencialmente los 685 MB. La razón aproximada de corpus disponible/parámetros (6,79 bytes por parámetro) **no es** la razón de tokens efectivamente entrenados/parámetros. La exposición nominal de esta continuación es aproximadamente **0,00063 posiciones por parámetro**. Véase [MÉTRICAS](docs/METRICS.md).

El modelo de 9,9M llegó a Drosophila desde un entrenamiento anterior de 10.000 pasos. No se debe aplicar Chinchilla de forma mecánica a una continuación de fine-tuning ni sumar presupuestos sin conocer los tokens efectivamente procesados en cada etapa.

## Corpus y bibliotecas

La raíz canónica es [data/datasets](data/datasets/). Consulta el [inventario completo](data/datasets/README.md).

| Indicador documental | Corte del inventario |
|---|---:|
| Unidades train-scoped | **286.468** |
| Texto UTF-8 train-scoped | **684.738.932 bytes** |
| Bibliotecas objetivo | **64** (32 dominios × General/HKD) |
| Bibliotecas que alcanzan el mínimo Level A | **0/64** |
| Bibliotecas globalmente training-eligible | **0/64**; G-0 global sigue FAIL |

El corpus exacto declarado por el manifiesto Drosophila suma **685.023.414 bytes** en sus seis particiones train-scoped. La diferencia frente al corte del inventario debe mantenerse visible: son cifras de ámbitos/cortes distintos, no una corrección silenciosa. El manifiesto candidato no publica una descomposición completa de documentos por fuente; el artefacto del run es la referencia para auditarla.

**Train-scoped no equivale a certificación global.** G-0, near-duplicates y contaminación de benchmarks/holdouts permanecen pendientes o fallidos según el manifiesto. Validation/test no entran en gradientes.

## Cómo trabajamos

1. **Adquirir:** registrar fuente, revisión upstream, licencia y procedencia.
2. **Auditar:** verificar payload, hashes, calidad, privacidad y duplicados dentro del alcance declarado.
3. **Particionar:** mantener train, validation y test separados.
4. **Entrenar:** fijar checkpoint, arquitectura, seed, presupuesto y mezcla efectiva.
5. **Evaluar:** comparar antes/después con los mismos IDs y protocolo.
6. **Publicar:** conservar informes, artefactos, costes y límites; promover solo con decisión explícita.

### Workflows de referencia

| Workflow | Objetivo |
|---|---|
| [Expansión funcional ×10](.github/workflows/expand-10x-from-10k.yml) | Expandir el checkpoint de 10k, verificar equivalencia, entrenar 500 pasos y hacer screening |
| [Cribado nativo sin tutor](.github/workflows/main-native-no-tutor-holdout.yml) | Entrenar y evaluar candidatos con inputs configurables |
| [Torneo adaptativo](.github/workflows/adaptive-50-seed-tournament.yml) | Explorar y comparar semillas |

Los workflows evolucionan. Revisa el YAML, commit, inputs, logs y artefactos de cada run. Sus valores por defecto no constituyen una receta universal.

## Reproducir localmente

Entorno orientativo: Python 3.11 y PyTorch 2.2 o posterior.

~~~bash
python -m pip install -e '.[dev]'
pytest -q
~~~

El entrenador local actual solo expone el perfil tiny (9,9M); no existe un perfil local drosophila equivalente. El ejemplo siguiente es un smoke test de hasta 1.000 pasos, no reproduce el experimento Drosophila:

~~~bash
python scripts/train_text.py \
  --text /ruta/al/corpus-autorizado.txt \
  --profile tiny \
  --steps 500 \
  --seed 20261106 \
  --device cpu \
  --num-threads 2 \
  --metrics-out metrics.json
~~~

La expansión Drosophila requiere el checkpoint exacto de 10.000 pasos, el corpus ensamblado de seis fuentes y el script [expand_and_train_10x.py](scripts/expand_and_train_10x.py). No basta con cambiar el perfil. Consulta [docs/TRAINING.md](docs/TRAINING.md) y [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

## Límites conocidos

- Drosophila tiene diez veces más parámetros que la línea base, pero la continuación documentada solo cubre 500 pasos y 64.000 posiciones de entrada muestreadas.
- El screening de 64 preguntas no demuestra mejora; el resultado observado es empate.
- No hay todavía cuatro seeds Drosophila comparables: el candidato publicado es una ejecución, no una distribución estadística.
- El manifiesto candidato no registra minutos efectivos de runner ni tokens procesados como campo explícito; no se inventan.
- La expansión conserva logits antes del entrenamiento, pero aumenta coste de memoria y cómputo. El modelo pequeño sigue siendo más sencillo de ejecutar, inspeccionar y usar como banco de pruebas.
- G-0 global, near-duplicates y contaminación de holdout no están resueltos.

## Principios

- Evidencia antes que promoción.
- Mismo holdout antes y después, con IDs registrados.
- Datos con procedencia, licencia y hashes.
- Sin atribuciones retroactivas de corpus.
- Sin confundir predicción de texto con razonamiento.
- Sin comparar regímenes distintos como si fueran equivalentes.
- Sin fijar una receta antes de que los experimentos la justifiquen.

---

<div align="center">

**RONIN-IA · El método es largo; el modelo todavía está creciendo.**

</div>
