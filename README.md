<div align="center">

# RONIN-IA

### Investigación abierta sobre modelos pequeños, corpus trazables y entrenamiento verificable.

**Un modelo propio. Datos auditables. Experimentos sin atajos.**

[Modelo y pesos](weights/) · [Biblioteca de datasets](data/datasets/) · [Experimentos](https://github.com/orbitalronin94/RONIN-IA/actions) · [Grimorio y bitácora](docs/GRIMORIO_DE_DROSOPHILA.md) · [Documentación](docs/)

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
| [Documentación técnica](docs/) | Entrenamiento, evaluación, decisiones y protocolos |\n| [El Grimorio de Drosophila](docs/GRIMORIO_DE_DROSOPHILA.md) | Crónica alquímica, jerarquía infernal, siete pecados y bitácora automática de Actions |

## Estado del modelo

<details>
<summary><strong>Modelo experimental principal: Ronin - Drosophila</strong></summary>

| Propiedad | Valor |
|---|---|
| Identificador | `Ronin-Drosophila-100900160` |
| Parámetros | **100.900.160 (~100,9 M)** |
| Expansión | ×10,17 desde el checkpoint de 9,9 M |
| Pasos de continuación | 500 |
| Checkpoint | [Artefacto del nuevo main — run #42207268776](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42207268776/artifacts/13497987527) |
| SHA-256 | `f3f8e2e75e418f8630372c242378a28010db83148d169d85ad3e4f73114cda9a` |
| Manifiesto | [ronin-drosophila-main.json](weights/ronin-drosophila-main.json) |

El checkpoint de 403.629.045 bytes se conserva como artefacto de GitHub Actions; no se ha copiado a `weights/ronin-main.pt`. El modelo compacto de 9.922.880 parámetros sigue empaquetado como fallback en [weights/ronin-main.pt](weights/ronin-main.pt), con su identidad descrita en [main-model.json](weights/main-model.json).

La expansión conservó la función antes del entrenamiento (diferencia máxima absoluta de logits: 1,4305×10⁻⁶). El nuevo run #42207268776 repitió el entrenamiento de 500 pasos y produjo exactamente el mismo checkpoint que #42203609278: SHA-256 idéntico. En el screening MMLU-Pro pareado obtuvo 5/64 antes y 5/64 después: no se detectó regresión en esa muestra, pero tampoco mejora. Es un screening de validación, no un holdout independiente completo.

</details>

### Proclama de la mosca — De cómo la criatura creció más deprisa que su entendimiento

#### De cómo la mosca, aunque grande, aún no ha aprendido a volar

Sepan cuantos leyeren que la criatura llamada **Ronin - Drosophila**, después de quinientos pasos de continuación, non mostró mejora en el cribado que aquí se declara. En sesenta y cuatro preguntas acertó cinco antes del entrenamiento y cinco después. Non se tenga tal cuenta por prueba de entendimiento, ca solo declara lo que en aquella muestra aconteció; ni se diga que la mosca ha aprendido por haber mudado de cuerpo.

#### De la diferencia entre crecer y aprender

Creció la mosca desde 9.922.880 hasta 100.900.160 parámetros, esto es, unas 10,17 veces; y el checkpoint alcanzó 403.629.045 bytes. Mas el entendimiento non creció con el cuerpo según la evaluación publicada: el screening permaneció en 5/64. Quien viniere a medir la mosca por su peso, sepa que pesa; quien viniere a medirla por su juicio, sepa que el README aún non ofrece prueba de mejora.

#### De los controles que non se ocultan

Non se diga que la mosca vuela limpia cuando el control global G-0 figura como FAIL y los controles de duplicidad cercana y contaminación del holdout aparecen señalados como FAIL o PENDING en el manifiesto. El README non desglosa allí el estado individual de estos dos últimos controles. Mientras tales máculas permanezcan, la elegibilidad global del corpus non puede darse por certificada. Y la cortesía non es prueba.

#### Del que viene a comparar con los grandes

Quien viniere con la tabla de los modelos frontera en la mano, tórnese por do vino: este repositorio non aporta aquí una comparación directa con ellos. La mosca non reclama el trono ni pretende vencer al halcón. Reclama, por agora, que se puedan examinar sus parámetros, hashes, runs, corpus y límites. El que busque una victoria en benchmarks frontera, non la hallará demostrada en estas páginas.

#### De la humildad del número

Non fagamos como los mercaderes que llaman seda al hilo. Un delta máximo absoluto de logits de 1,4305×10⁻⁶ demuestra que la expansión conservó la función antes del entrenamiento; non demuestra que la criatura sepa más. Conservar la función es oficio de cirujano; aprender es oficio de maestro. La mosca ha pasado por el cirujano. El maestro aún non ha llegado.


### Del pacto infernal: PyTorch, Microsoft y la mosca

Y aconteció que, para dar cuerpo a la criatura, hubimos de parlamentar con dos potestades del averno informático. La primera fue **PyTorch**, grimorio tensorial mediante el cual los números obedecen, los gradientes descienden y las matrices reclaman sacrificios de memoria. La segunda fue **Microsoft**, bajo cuya jurisdicción de nubes y Actions se encendieron los hornos donde la criatura fue expandida y sometida a quinientos pasos de penitencia.

No se afirme por ello que PyTorch pertenezca a Microsoft: son entidades distintas; aquí se las reúne por conveniencia literaria y por el común estrépito de sus máquinas. El pacto verdadero, menos sobrenatural y más verificable, fue éste: código ejecutado en PyTorch, cómputo hospedado por GitHub Actions, artefactos sellados con SHA-256 y un manifiesto que deja constancia de lo ocurrido.

**La cláusula más cruel del pacto:** si después de quinientos pasos la mosca no aprende más, los demonios no devuelven el tiempo de CPU. Y si el siguiente ritual produce el mismo hash, tampoco conceden una segunda alma: conceden reproducibilidad.

Que conste, pues, que la criatura no ha vencido al averno. Ha conseguido que el averno le facture el mismo milagro en menos minutos.


### Los siete pecados de la máquina

En este códice se nombran siete faltas que toda criatura artificial debe evitar:

| Pecado | Herejía informática |
|---|---|
| Soberbia | Proclamar superioridad sin benchmark homogéneo |
| Avaricia | Aumentar parámetros sin medir aprendizaje |
| Gula | Ingerir corpus sin auditar |
| Pereza | Delegar toda capacidad en un tutor externo |
| Ira | Entrenar hasta quebrar la estabilidad |
| Envidia | Compararse con modelos frontera sin protocolo común |
| Vanidad | Celebrar una métrica aislada |

El desarrollo de esta mitología, su glosario y las actas experimentales viven en **[El Grimorio de Drosophila](docs/GRIMORIO_DE_DROSOPHILA.md)**. Una bitácora automática añade allí una entrada cuando concluyen workflows de la rama `main`: registra ejecuciones y artefactos, pero no convierte por sí sola un resultado en mejora científica.


---

## Anexo I — Máculas declaradas

| Control o indicador | Estado publicado | Consecuencia práctica |
|---|---|---|
| G-0 global | **FAIL** | El inventario declara 0/64 bibliotecas globalmente training-eligible. |
| Near-duplicates | **FAIL o PENDING**; el README no precisa cuál | No debe afirmarse que el control de duplicidad está superado. |
| Contaminación de holdout | **FAIL o PENDING**; el README no precisa cuál | La limpieza del holdout no puede darse por certificada. |
| Bibliotecas que alcanzan el mínimo Level A | **5/64** | Solo cinco bibliotecas alcanzan ese umbral del inventario. |
| Bibliotecas globalmente training-eligible | **0/64** | No hay bibliotecas con elegibilidad global declarada. |

**Una mácula declarada sigue siendo mácula. Que se vea no la cura.**

El README indica que solo las particiones `train` expresamente admitidas pueden alimentar gradientes y que validation/test permanecen aislados. También advierte que los totales del inventario documental no equivalen al corpus utilizado en todos los entrenamientos.

## Anexo II — Lo que no consta (y debería)

| Dato ausente del README | Por qué importa |
|---|---|
| Tokens vistos en los 500 pasos de Drosophila | Sin batch, longitud de secuencia o tokens procesados no se puede cuantificar el presupuesto efectivo de entrenamiento. |
| Tokens procesados en el run de 10.000 pasos | El README declara 256.612.919 bytes de corpus combinado, no tokens vistos durante el entrenamiento. |
| Checkpoint exacto de partida del run de 10.000 pasos | Sin esa identidad no puede reconstruirse con precisión la relación entre el modelo inicial y el candidato final. |
| Varianza entre seeds para el modelo de 100,9 M | El README identifica un run de Drosophila, pero no publica una evaluación multi-seed de ese modelo. |
| Pares discordantes del cambio MMLU-Pro | Se publican los totales antes/después, pero no cuántas preguntas pasaron de incorrectas a correctas y viceversa. |
| Intervalo de confianza de la diferencia MMLU-Pro | Sin los datos pareados por pregunta no debe inventarse un intervalo ni una prueba de significación. |
| Minutos de GitHub Actions por run | El README no declara el coste temporal de ejecución. |
| Retención exacta del artefacto de 403.629.045 bytes | Se advierte que está sujeto a la retención de GitHub Actions, pero no se indica cuántos días ni una copia espejo. |

**Lo que no consta no es que no exista: es que no se puede auditar desde este README. Y lo que no se audita, no se cita como hecho.**

## Anexo III — La mosca y el azar

El README publica un screening MMLU-Pro de **5/64 antes y 5/64 después**. La proporción observada es **7,81 %** en ambas mediciones (cálculo derivado de 5 dividido entre 64).

Pero el README no declara en este bloque el número de opciones por pregunta ni un modelo nulo de respuesta aleatoria. Por tanto, no corresponde afirmar aquí que 5/64 sea estadísticamente indistinguible del azar, ni que sea significativamente peor. Para sostener cualquiera de esas conclusiones habría que fijar primero el protocolo de azar y disponer de la evaluación detallada.

Tampoco cabe comparar ese resultado con un supuesto 7/50 de un modelo anterior: tal cifra no aparece en el README actual. Lo que sí puede decirse, sin añadir datos, es que **la expansión ×10,17 no produjo una mejora observable en este screening: el resultado publicado permaneció en 5/64**.

**No se probó mejora en esta muestra. Tampoco se ha publicado aquí evidencia suficiente para convertir ese resultado en una conclusión estadística sobre el azar.**

## Anexo IV — El test y el riesgo de selección

El README atribuye al run #42181780771 una evaluación MMLU-Pro de **12.032/12.032** preguntas, con resultado de **1.295/12.032 a 1.314/12.032** (+0,158 puntos porcentuales). También lo identifica expresamente como candidato para revisión que no modifica los pesos de `main`.

Hay, no obstante, una limitación declarada: los controles globales G-0 y de contaminación del holdout no constan como superados. Además, si un conjunto denominado test se consulta repetidamente para escoger entre candidatos, puede acabar influyendo en la selección aunque ningún candidato se promocione automáticamente. El README no permite determinar cuántas veces se utilizó ese conjunto para selección; por ello debe documentarse ese uso antes de tratarlo como evaluación final independiente.

**Mientras el control de contaminación siga sin constar como PASS, no debe presentarse la limpieza del holdout como una garantía.**

## Anexo V — Presupuesto de entrenamiento: lo que sí y lo que no sabemos

Para Drosophila constan **500 pasos**, 100.900.160 parámetros y el screening 5/64 antes y después; no constan tokens procesados. Para el run largo constan **10.000 pasos**, 256.612.919 bytes de corpus combinado, 279.352 unidades train-scoped y la evaluación MMLU-Pro indicada arriba; no constan tokens procesados ni el checkpoint exacto de partida.

El README tampoco proporciona una base para calcular la relación tokens/parámetro ni para juzgar el entrenamiento frente a un óptimo Chinchilla. Los bytes del corpus no son, por sí solos, tokens vistos: no deben convertirse en tokens mediante una equivalencia supuesta.

**La Drosophila puede estar poco entrenada; el README no publica los tokens necesarios para demostrar cuánto. El número debe preceder a la metáfora, no ser sustituido por ella.**

## Anexo VI — El hash sin cuerpo

El checkpoint de **403.629.045 bytes** se conserva como artefacto de GitHub Actions y su SHA-256 está publicado en el manifiesto. El README advierte que el artefacto está sujeto a la retención de GitHub Actions, pero no declara el plazo exacto ni una copia espejo de conservación prolongada.

Si el artefacto caduca, el hash seguirá identificando el contenido esperado, pero no permitirá reconstruirlo por sí solo. Para que la verificación siga siendo posible, hace falta conservar el cuerpo del checkpoint en un almacenamiento duradero y volver a comprobar su hash al recuperarlo.

**Un hash sin cuerpo es un epitafio. Sirve para recordar que existió, no para comprobar que aún poseemos el mismo artefacto.**

## Anexo VII — Catecismo del escéptico

Antes de citar el repositorio, conviene preguntar:

1. ¿Cuál fue el checkpoint exacto de partida del run de 10.000 pasos?
2. ¿Cuántos tokens vio Drosophila durante sus 500 pasos?
3. ¿Cuántos pares discordantes hubo en el cambio de 1.295 a 1.314 respuestas correctas?
4. ¿Cuál es la variación entre varias seeds del modelo de 100,9 M?
5. ¿Cuántos minutos de Actions costó cada run?
6. ¿Qué comprobaciones concretas faltan para que G-0 pase de FAIL a PASS?
7. ¿Qué estado individual tienen near-duplicates y contaminación del holdout?
8. ¿Cuántos días de retención tiene el artefacto de 403 MB?
9. Si el artefacto caduca, ¿dónde se conserva el cuerpo verificable?

**El que non se faga estas preguntas non ha mirado las trazas. Ha mirado la mosca.**

## Anexo VIII — Instrucciones para quien venga a comparar con modelos frontera

Si vienes a comparar la mosca con modelos frontera, advierte primero que este README no publica una evaluación directa y homogénea frente a ellos. No afirmamos victoria ni equivalencia. Lo que sí ofrece el repositorio es trazabilidad declarada: identificadores de runs, hashes, manifiestos de corpus, arquitectura, métricas y límites conocidos. Esa trazabilidad permite inspeccionar el experimento; no sustituye a una comparación de capacidades.

La mosca no reclama ganar la feria. Reclama que se pueda abrir el libro de cuentas.

---

> **El método es largo; el modelo todavía está creciendo. Mas crecer dista de aprender: es solo ocupar más sitio en el artefacto.**

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

La referencia experimental vigente es **Ronin - Drosophila (100.900.160 parámetros)**, promovida como nuevo `main` experimental tras el run [#42207268776](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42207268776). Consulta el [manifiesto principal](weights/ronin-drosophila-main.json) para hashes, corpus, arquitectura y evaluación.

El checkpoint de 403.629.045 bytes se sirve como [artefacto del nuevo main en GitHub Actions](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42207268776/artifacts/13497987527). Por tamaño, no reemplaza el archivo Git [weights/ronin-main.pt](weights/ronin-main.pt): ese paquete de 9,9 M permanece como fallback compacto. La promoción experimental no debe confundirse con sustituir físicamente el paquete distribuido.

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
