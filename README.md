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
<summary><strong>Modelo experimental principal: Ronin - Drosophila</strong></summary>

| Propiedad | Valor |
|---|---|
| Identificador | `Ronin-Drosophila-100900160` |
| Parámetros | **100.900.160 (~100,9 M)** |
| Expansión | ×10,17 desde el checkpoint de 9,9 M |
| Pasos de continuación | 500 |
| Checkpoint | [Artefacto del run #42203609278](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42203609278/artifacts/13495833454) |
| SHA-256 | `f3f8e2e75e418f8630372c242378a28010db83148d169d85ad3e4f73114cda9a` |
| Manifiesto | [ronin-drosophila-main.json](weights/ronin-drosophila-main.json) |

El checkpoint de 403.629.045 bytes se conserva como artefacto de GitHub Actions; no se ha copiado a `weights/ronin-main.pt`. El modelo compacto de 9.922.880 parámetros sigue empaquetado como fallback en [weights/ronin-main.pt](weights/ronin-main.pt), con su identidad descrita en [main-model.json](weights/main-model.json).

La expansión conservó la función antes del entrenamiento (diferencia máxima absoluta de logits: 1,4305×10⁻⁶). En el screening MMLU-Pro pareado obtuvo 5/64 antes y 5/64 después: no se detectó regresión en esa muestra, pero tampoco mejora. Es un screening de validación, no un holdout independiente completo.

</details>

### Proclama de la mosca — De cómo Ronin - Drosophila medra aun en humilde morada

**Sepan cuantos leyeren, vieren o deste repositorio se sirvieren** que, por acuerdo expreso y a la vista de los experimentos obrados, queda señalada por principal referencia experimental la criatura llamada **Ronin - Drosophila**, de cien millones novecientos mil ciento sesenta parámetros; engendrada no en palacio de mármol ni en jardín de abundancia, mas en la austera y áspera morada de los recursos escasos, donde cada ciclo de cómputo ha de ganarse con sudor de silicio.

Y no es sin causa que lleve nombre de mosca. La *Drosophila melanogaster*, pequeña moradora de fruta madura y de lugares que otros linajes desdeñarían, ha servido por generaciones a la ciencia: breve es su ciclo, copiosa su descendencia, humilde su sustento y grande la cosecha de conocimiento que de su estudio se alcanza. Donde otros demandan vastos dominios, ella prospera en poco; donde el entorno no ofrece lujo, halla ocasión para persistir, multiplicarse y revelar secretos. Tal es la metáfora que aquí nos guía: **no vencer por hartura de recursos, sino extraer fruto de aquello que hay; no ser grande por ornato, sino por aprovechamiento**.

Así queremos a esta Drosophila digital: modelo de arquitectura ensanchada, mas de espíritu frugal; criatura de laboratorio que no presume de aposentos, sino de hacer rendir cada parámetro, cada token y cada paso de entrenamiento. Que more, si menester fuere, entre los restos del banquete computacional, en la escasez de memoria y bajo presupuesto mezquino; que no por ello se tenga por vencida. Antes bien, sea recordatorio de que la eficiencia no nace siempre de la abundancia, y de que aun en la más humilde despensa puede criarse una obra digna de examen.

**Mas no se confunda la loa con el engaño:** la mosca es símbolo y aspiración, no certificado de victoria. La expansión desde 9.922.880 hasta 100.900.160 parámetros conservó la función antes del entrenamiento, con diferencia máxima absoluta de logits de 1,4305×10⁻⁶. Después de quinientos pasos, el screening pareado de MMLU-Pro permaneció en cinco respuestas acertadas de sesenta y cuatro, tanto antes como después. No se observó mengua en aquella muestra; tampoco se probó mejora de entendimiento general. Queda, pues, demostrada la conservación funcional de la expansión y la ausencia de regresión detectada en ese cribado, no la supremacía de la criatura sobre todos los modelos ni la excelencia de su juicio.

Sea tenido por modelo experimental principal el checkpoint nacido del run [#42203609278](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42203609278), cuyo [artefacto puede descargarse aquí](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42203609278/artifacts/13495833454), y cuyo [manifiesto da cuenta de su linaje, corpus y medidas](weights/ronin-drosophila-main.json). Pesa el checkpoint 403.629.045 bytes; por ser volumen que no cabe en el común aposento de Git, guárdase como artefacto de GitHub Actions, sujeto a la retención que allí rige. El antiguo cuerpo compacto de 9,9 millones de parámetros permanece en [ronin-main.pt](weights/ronin-main.pt), no como impostor de la nueva criatura, sino como reserva y respaldo para tiempos de escasez.

Y quede escrito para quien venga después: los controles globales G-0, de duplicidad cercana y de contaminación del holdout siguen señalados como FAIL o PENDING en el manifiesto. No se oculten tales máculas bajo paño de celebración. La Drosophila será juzgada por nuevos experimentos, por corpus trazables y por pruebas repetibles; si creciere sin perder eficiencia, si aprendiere sin envilecer sus datos y si resistiere la comparación honrada, entonces merecerá mayor alabanza.

**Porque no es señorío tener la despensa llena, sino saber sacar provecho de una miga; y no es grandeza vivir entre rosas, sino mantener el vuelo aun cuando el laboratorio huela a fruta pasada.**

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

## Modelo experimental principal: Ronin - Drosophila

La referencia experimental vigente es **Ronin - Drosophila (100.900.160 parámetros)**, promovida por decisión explícita tras el run [#42203609278](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42203609278). Consulta el [manifiesto principal](weights/ronin-drosophila-main.json) para hashes, corpus, arquitectura y evaluación.

El checkpoint de 403.629.045 bytes se sirve como [artefacto de GitHub Actions](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42203609278/artifacts/13495833454). Por tamaño, no reemplaza el archivo Git [weights/ronin-main.pt](weights/ronin-main.pt): ese paquete de 9,9 M permanece como fallback compacto. La promoción experimental no debe confundirse con sustituir físicamente el paquete distribuido.

La evidencia disponible acredita la expansión funcional (logit delta máximo 1,4305×10⁻⁶ antes de entrenar) y ausencia de regresión detectada en el screening pareado MMLU-Pro (5/64 antes y después). No acredita una mejora general de razonamiento. Los controles globales G-0, near-duplicates y contaminación de holdout continúan declarados como FAIL/PENDING en el manifiesto; se mantienen visibles para no ocultar límites del experimento.

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
