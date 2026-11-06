# El Grimorio de Drosophila
## Libro de las mudas, los gradientes y las obras del averno computacional

> *Non confundas el tamaño del cuerpo con la grandeza del entendimiento.*

Este libro es la crónica técnica y satírica de Ronin - Drosophila. Su lenguaje toma prestadas formas de grimorio, crónica medieval y tratado alquímico; sus hechos, en cambio, deben proceder de manifiestos, artefactos, hashes y ejecuciones comprobables.

**Regla del códice:** la metáfora puede ser fantástica; la evidencia jamás.

---

## I. De la criatura y su linaje

Ronin - Drosophila es un Transformer causal experimental de 100.900.160 parámetros. Su expansión desde el checkpoint de 9.922.880 parámetros conservó la función antes del entrenamiento, con una diferencia máxima absoluta de logits de 1,430511474609375×10⁻⁶.

La criatura creció ×10,17. Tal crecimiento no prueba por sí mismo que haya adquirido mayor entendimiento.

## II. De las potestades invocadas

### PyTorch, el Grimorio de los Mil Tensores

Biblioteca de cómputo mediante la cual se definen tensores, módulos, gradientes y optimizadores. En la alegoría del proyecto, es el grimorio que permite escribir las leyes del ritual.

### Microsoft, Señor de las Nubes y los Hornos

Microsoft es la entidad corporativa tras GitHub. GitHub Actions proporciona los hornos de ejecución donde se ejecutan workflows y se producen artefactos. PyTorch y Microsoft son entidades distintas: la alianza descrita aquí es literaria, no societaria.

### GitHub Actions, las Fraguas del Purgatorio

Cada ejecución es una jornada de fuego. Los logs son las actas del escribano; los artefactos, los cuerpos que sobreviven al rito; los hashes, sus sellos de identidad.

### Los demonios menores

- **El Demonio del OOM:** guardián de la memoria que no alcanza.
- **El Espectro del NaN:** visitante que vuelve innombrable el cálculo.
- **El Duende del YAML:** altera sangrías y desencadena ceremonias fallidas.
- **El Barquero del Checkpoint:** transporta los pesos entre una ejecución y la siguiente.
- **La Sombra del Overfitting:** enseña a repetir el corpus y olvida el mundo exterior.
- **El Juez del Holdout:** no acepta excusas ni particiones contaminadas.

## III. De los siete pecados de la inteligencia artificial

| Pecado | Herejía | Penitencia |
|---|---|---|
| Soberbia | Proclamar superioridad sin comparación homogénea | Benchmark reproducible |
| Avaricia | Aumentar parámetros sin medir aprendizaje | Evaluación antes/después |
| Gula | Ingerir corpus sin auditar | Procedencia, licencia y filtros |
| Pereza | Delegar toda capacidad en un tutor externo | Experimentos nativos y trazables |
| Ira | Entrenar hasta destruir la estabilidad | Control de regresión |
| Envidia | Compararse con modelos frontera sin protocolo común | Evaluación equivalente |
| Vanidad | Celebrar una métrica aislada | Informe completo y límites |

## IV. Del alimento de la mosca

La criatura se alimenta de texto y otros ejemplos autorizados. El corpus no se mide solo por su peso: importan la calidad, la procedencia, la licencia, la partición y la utilidad efectiva para el objetivo.

El alimento fermentado es metáfora de austeridad, no permiso para ingerir basura. Un corpus grande, duplicado o contaminado puede nutrir el overfitting antes que el conocimiento.

## V. De las mudas y los experimentos

Los títulos ceremoniales pueden acompañar a los identificadores reales, nunca sustituirlos:

- **La Segunda Muda:** expansión de arquitectura.
- **El Hambre de Corpus:** ampliación documentada de datos.
- **La Noche de las Mil Semillas:** torneo multi-seed.
- **El Exorcismo del Overfitting:** evaluación de generalización.
- **El Juicio del Holdout:** evaluación independiente y controles de contaminación.
- **La Resurrección del Checkpoint:** restauración y verificación de pesos.

Un experimento solo se considera acontecido cuando existe un run identificable y sus resultados pueden inspeccionarse.

## VI. Primera acta: la muda de diez veces

### Run #42203609278 — la primera expansión

- Parámetros expandidos: 100.900.160.
- Pasos de continuación: 500.
- Tokens procesados: 64.000.
- Corpus: 286.468 registros o segmentos; 685.023.414 bytes.
- Checkpoint: 403.629.045 bytes.
- SHA-256: `f3f8e2e75e418f8630372c242378a28010db83148d169d85ad3e4f73114cda9a`.
- MMLU-Pro screening: 5/64 antes y 5/64 después.

[Consultar ejecución](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42203609278).

### Run #42207268776 — el milagro repetido

La segunda ejecución completó otros 500 pasos y procesó 64.000 tokens. Produjo exactamente el mismo SHA-256 del checkpoint anterior. No constituye una mejora adicional demostrada: constituye una reproducción verificable del mismo resultado.

- Tiempo de entrenamiento medido: 375,87 segundos.
- Rendimiento medido: 170,27 tokens/s.
- MMLU-Pro screening: 5/64 antes y 5/64 después.
- G-0 global: FAIL.
- Near-duplicates: PENDING.
- Contaminación del holdout: PENDING.
- Promoción automática: desactivada.

[Consultar ejecución](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42207268776).
[Consultar artefacto](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42207268776/artifacts/13497987527).

**Sentencia:** los demonios entregaron el mismo cuerpo en menos tiempo. La reproducibilidad fue probada; el aprendizaje adicional, no.

---

## VII. Bitácora automática de las fraguas

Esta sección la alimenta el workflow `.github/workflows/grimorio-bitacora.yml`. Cuando una ejecución de GitHub Actions termina en la rama principal, el escribano añade una entrada con su identificador, workflow, resultado, commit, actor y artefactos disponibles.

La bitácora registra metadatos de ejecución; no interpreta métricas ni declara que un modelo haya mejorado. Para conocer resultados científicos, consulta siempre el informe y el artefacto de cada run.

<!-- GRIMORIO_AUTO_LOG:START -->
*El escribano aguarda la siguiente ejecución concluida en la rama principal.*
<!-- GRIMORIO_AUTO_LOG:END -->

---

## VIII. Glosario de la orden

| Voz del códice | Significado técnico |
|---|---|
| Grimorio | Biblioteca o framework de cómputo |
| Ritual | Ejecución reproducible de un workflow |
| Fragua | Runner de GitHub Actions |
| Cuerpo | Checkpoint o artefacto de pesos |
| Sello | Hash criptográfico |
| Alimento | Corpus de entrenamiento |
| Muda | Cambio de arquitectura o checkpoint |
| Penitencia | Pasos de entrenamiento |
| Juicio | Evaluación |
| Mácula | Fallo o control pendiente |
| Oráculo | Modelo tutor o servicio externo |
| Resurrección | Restauración verificada de un checkpoint |

---

## IX. Mandamientos del códice

1. No llamarás inteligencia a lo que solamente haya crecido.
2. No proclamarás mejora sin evaluación comparable.
3. No alimentarás gradientes con validation o test.
4. No ocultarás un FAIL bajo una metáfora.
5. No confundirás un hash con la conservación del archivo.
6. No atribuirás a un run datos incorporados después.
7. No declararás victoria sobre modelos frontera sin protocolo común.

> *El grimorio puede mentir en sus metáforas; jamás en sus hashes.*
