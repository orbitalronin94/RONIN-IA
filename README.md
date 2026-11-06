<div align="center">

# RONIN-IA

### Investigación abierta sobre modelos pequeños, corpus trazables y entrenamiento verificable.

**Un modelo propio. Datos auditables. Experimentos sin atajos.**

[Modelo y pesos](weights/) · [Biblioteca de datasets](data/datasets/) · [Experimentos](https://github.com/orbitalronin94/RONIN-IA/actions) · [Documentación](docs/)

[![GitHub Actions](https://img.shields.io/badge/experimentos-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/orbitalronin94/RONIN-IA/actions)
[![PyTorch](https://img.shields.io/badge/framework-PyTorch-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![License](https://img.shields.io/badge/license-MIT-0A7B55.svg)](LICENSE)

</div>

---

## En dos minutos

RONIN es un modelo causal Transformer implementado en PyTorch. El proyecto explora cuánto puede aprender un modelo pequeño a partir de corpus abiertos o autorizados, con procedencia documentada y evaluaciones reproducibles.

> **El entrenamiento sigue siendo experimental.** No existe todavía una receta única: pasos, semillas, arquitectura, mezcla de datos y profundidad de evaluación cambian según la hipótesis de cada experimento. El workflow, sus inputs, logs y artefactos son la fuente de verdad de cada run.

### Accesos principales

| Área | Qué encontrarás |
|---|---|
| [Biblioteca de datasets](data/datasets/README.md) | Inventario, bibliotecas, fuentes, derechos, particiones y estado entrenable |
| [Manifiestos de datasets](data/datasets/) | Payloads y manifiestos por fuente; hashes y trazabilidad |
| [Pesos versionados](weights/ronin-main.pt) | Paquete compacto PyTorch del modelo fijado en `main` |
| [Manifiesto del modelo](weights/main-model.json) | Arquitectura, parámetros, hashes, procedencia y evaluación |
| [Historial de experimentos](https://github.com/orbitalronin94/RONIN-IA/actions) | Runs, workflows, inputs, logs y artefactos descargables |
| [Documentación técnica](docs/) | Entrenamiento, evaluación, decisiones y protocolos |

## Estado del modelo

<details>
<summary><strong>Modelo de referencia en main</strong></summary>

| Propiedad | Valor |
|---|---|
| Identificador | `RONIN-tiny-seed95-100-001` |
| Parámetros | **9.922.880 (~9,9 M)** |
| Arquitectura | Transformer causal, RoPE, RMSNorm, SwiGLU y GQA |
| Tokenización | byte-v1 |
| Checkpoint de origen | 100 pasos, seed 95 |
| Pesos | [weights/ronin-main.pt](weights/ronin-main.pt) |
| Manifiesto | [weights/main-model.json](weights/main-model.json) |

La evaluación asociada a esta línea base fue un screening MMLU-Pro de 50 preguntas: 5/50 → 7/50. Se clasifica como `SCREENING_ONLY`; no demuestra razonamiento general ni equivale al test independiente completo.

</details>

### Candidato mergeable actual: Ronin - Drosophila

<badge> Candidato mergeable · no sustituye todavía los pesos versionados en main </badge>

**Nombre oficial:** **Ronin - Drosophila (100.900.160 parámetros)**  
**Identificador técnico:** `Ronin-Drosophila-100900160`

- Origen: ganador del entrenamiento de 10.000 pasos, run [#42181780771](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42181780771).
- Expansión y continuación: run [#42198068241](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42198068241), 500 pasos.
- Arquitectura: Transformer causal con RoPE, RMSNorm, GQA y SwiGLU ampliado a 12.700 canales.
- Parámetros: **100.900.160** (desde 9.922.880; ×10,17).
- Conservación funcional previa al entrenamiento: diferencia máxima absoluta de logits **1,4305×10⁻⁶**; comprobación superada.
- Screening MMLU-Pro pareado: **5/64 antes y 5/64 después**. No se observa mejora en esta muestra.
- Checkpoint SHA-256: `7d9345ecb9e3d7ad22aa628b93324ffd18e7b8a477f2d24c04885eced587d2f3`.
- [Artefacto del checkpoint](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42198068241/artifacts/13494355120) · [Manifiesto del candidato](weights/ronin-drosophila-100900160-candidate.json).

El candidato queda identificado con el nombre Drosophila y está preparado para revisión/merge como candidato. La etiqueta *mergeable* no significa que haya demostrado una mejora de capacidad: el screening no cambió y los gates globales G-0, near-duplicates y contaminación de holdout siguen pendientes. El modelo empaquetado en `main` continúa siendo la línea base anterior hasta que se promocionen explícitamente los nuevos pesos.

### Último experimento largo: 10.000 pasos

<details>
<summary><strong>Run #42181780771 — candidato experimental, no promocionado</strong></summary>

- [Ejecución en GitHub Actions](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42181780771)
- [Artefacto descargable (checkpoint + informes)](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42181780771/artifacts/13489465699)
- Rama: `experiment/seed95-10000-full-holdout`
- Seed: 95 · pasos completados: 10.000 · loss final: **2,11482**
- Corpus realmente ensamblado en este run: **279.352 unidades train-scoped**, 256.612.919 bytes combinados. No atribuirle retroactivamente las fuentes incorporadas después.
- MMLU-Pro test: **1.295/12.032 → 1.314/12.032** (10,763 % → 10,921 %; +0,158 puntos porcentuales).
- Bits per byte: **3,8152 → 2,9798**.
- Cobertura: 12.032/12.032; evaluación pareada antes/después.
- Estado: candidato para revisión; no modifica los pesos de `main`.

La reducción de BPB es una señal de mejor predicción en la distribución evaluada. La ganancia en MMLU-Pro es modesta y no basta por sí sola para afirmar una mejora general de razonamiento.

</details>

## Corpus y bibliotecas

La raíz canónica de datos es [`data/datasets/`](data/datasets/). Consulta su [inventario completo](data/datasets/README.md) antes de interpretar cifras.

| Indicador del inventario | Último corte documentado |
|---|---:|
| Unidades train-scoped | **286.468** |
| Texto UTF-8 train-scoped | **684.738.932 bytes** |
| Bibliotecas objetivo | **64** (32 dominios × General/HKD) |
| Bibliotecas que alcanzan el mínimo Level A | **5/64** |
| Bibliotecas globalmente training-eligible | **0/64**; G-0 global sigue FAIL |

Fuentes train-scoped registradas: literatura española, Mathlib4, NASA file-reviewed, Papers propios, ScienceVerse y CoVoST 2. Estos totales son del inventario documental, **no** el corpus usado en todos los entrenamientos. Los manifiestos de cada fuente mandan.

**No confundimos estados:** candidato descargado ≠ admitido ≠ train-eligible. Solo particiones `train` expresamente admitidas pueden alimentar gradientes. Validation/test permanecen aislados. Los controles globales pendientes se declaran; no presentamos el corpus completo como certificado.

## Cómo trabajamos

1. **Adquirir:** registrar fuente, revisión upstream, licencia y procedencia.
2. **Auditar:** verificar payload, hashes, calidad, privacidad y duplicados según el alcance declarado.
3. **Particionar:** mantener train, validation y test separados.
4. **Entrenar:** fijar checkpoint de partida, arquitectura, seed, presupuesto y mezcla efectiva.
5. **Evaluar:** comparar antes/después con el mismo holdout, IDs y protocolo.
6. **Revisar:** conservar informes y pesos candidatos; promover solo con decisión explícita.

### Workflows de referencia

| Workflow | Objetivo |
|---|---|
| [Cribado nativo sin tutor](.github/workflows/main-native-no-tutor-holdout.yml) | Entrenamiento de candidatos y evaluación pareada |
| [Torneo adaptativo de semillas](.github/workflows/adaptive-50-seed-tournament.yml) | Explorar y comparar semillas |
| [Experimentos de corpus](.github/workflows/micro-corpus-4-seeds.yml) | Probar mezclas y presupuestos concretos |

Los workflows evolucionan. Revisa el YAML y los inputs del run concreto; sus valores por defecto no constituyen una receta universal.

## Modelo mergeable: Ronin - Drosophila

El candidato actual de referencia para revisión es **Ronin - Drosophila (100.900.160 parámetros)**. Su expansión ×10,17 y continuación de 500 pasos se ejecutaron en el run [#42198068241](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42198068241). El manifiesto reproducible está en [weights/ronin-drosophila-100900160-candidate.json](weights/ronin-drosophila-100900160-candidate.json).

La condición de mergeable identifica el candidato que queremos integrar como modelo de trabajo; no equivale a una promoción automática de pesos ni a una mejora demostrada en razonamiento. El screening MMLU-Pro permaneció en 5/64 antes y después, y los gates globales siguen pendientes. La promoción a pesos principales requiere resolver esos controles y actualizar de forma atómica el paquete y el manifiesto principal.

## Reproducir localmente

Entorno orientativo: Python 3.11 y PyTorch 2.2 o posterior.

```bash
python -m pip install -e '.[dev]'
pytest -q
```

Entrenamiento local de texto autorizado (ejemplo, no receta oficial):

```bash
python scripts/train_text.py --text /ruta/al/corpus.txt --profile tiny --steps 500
```

Consulta [docs/TRAINING.md](docs/TRAINING.md) y [el protocolo MMLU-Pro](docs/HOLDOUT_EXTERNO_MMLU_PRO.md) antes de comparar resultados.

## Principios

- Evidencia antes que promoción.
- Mismo holdout antes y después.
- Datos con procedencia, licencia y hashes.
- Sin atribuciones retroactivas de corpus.
- Sin confundir predicción de texto con razonamiento.
- Sin fijar una receta antes de que los experimentos la justifiquen.

---

<div align="center">

**RONIN-IA · El método es largo; el modelo todavía está creciendo.**

</div>
