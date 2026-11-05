# Bibliotecas de datos de RONIN

Este directorio es el espacio canónico para adquirir, revisar, clasificar y versionar los textos de entrenamiento de RONIN.

## Objetivo operativo actual

El objetivo canónico es **64 bibliotecas: 32 dominios × General/HKD**. El inventario de referencia es libraries/manifest-64.json; libraries/manifest-32.json conserva el estado parcial del pipeline legado RUN5 de 16 dominios y no representa el objetivo final.

General y HKD deben ser disjuntas globalmente, sin duplicados exactos ni near-duplicates compartidos. HKD se selecciona por densidad semántica RONIN, con desempate estable por identificador documental, y el reparto se equilibra por bytes de texto UTF-8.

Cada biblioteca necesita al menos **1 MiB de texto admitido Level A**; el objetivo posterior es **10 GiB por biblioteca**. Por tanto, el mínimo total es 64 MiB y el objetivo de escala es 640 GiB. Solo cuentan bytes de texto admitido con evidencia Level A; no cuentan metadatos, candidatos, RDS comprimidos ni corpus legacy sin reconciliación territorial.

G-0 es independiente: mientras permanezca en FAIL, ninguna biblioteca puede ser training-eligible aunque su fuente tenga una licencia compatible.

## Estado real del corpus

**Estado:** 32 dominios y 64 bibliotecas catalogados; **0/64** alcanzan el mínimo Level A; **0 bytes** de texto Level A admitido en el inventario; G-0 sigue en FAIL.

- **Único corpus admitido:** \`admitted/literature-es-v1/\`, con 608 documentos de entrenamiento en español. Sus particiones de validación y prueba permanecen fuera del entrenamiento.
- **CoVoST 2:** la exportación exacta contiene solo el campo \`translation\` de tres archivos fijados, bajo la declaración CC0 del conjunto. El control de calidad retuvo 337.973 traducciones únicas; la partición train contiene 270.244 filas, validation 34.051 y test 33.678. Tres filas con patrón telefónico se revisaron: dos eran rangos de curso académico y una era una cantidad en euros por hora; se conservan como falsos positivos. Sigue pendiente la revisión humana final de muestras. Es un candidato con registro de derechos de alcance exacto, no un corpus admitido.
- **Common Corpus:** en una muestra acotada de 20.000 filas se conservaron 2.149 CC0, 4 CC BY 3.0 y 6 CC BY 4.0. Se rechazaron 17.472 por licencia, 311 por patrones básicos de privacidad y 8 por estructura/tamaño. El origen de cada documento, la privacidad multilingüe y la calidad siguen pendientes. La parte CC0 incluye VoxPopuli y datos estructurados de Wikidata; ninguno se promociona automáticamente a prosa de entrenamiento.
- **GPLSI ClearText:** 11 documentos CAS en español y 6 VAL en catalán están descargados como candidatos. La declaración CC BY 4.0 de la colección no resuelve los derechos de los documentos originales. Dos textos oficiales del BOE (BOE-A-1983-6317 y BOE-A-2015-11430) tienen una base de dominio público por el artículo 13 registrada en nivel B; falta firma jurídica humana y limpieza de extracción. Un documento con aviso NC-ND se mantiene en cuarentena.
- **ScienceVerse Collabra:** 749 DOI fijados; Crossref declara CC BY 4.0 para 748 y se excluye un artículo con licencia no comercial. La extracción corporal produjo 747 textos; el filtro retiró 70 con correos/contacto y dejó 677 candidatos (541 train, 72 validation y 64 test). Faltan revisión humana de menciones a participantes, privacidad y deduplicación global. La metadata de licencia es evidencia por DOI, no una garantía absoluta de titularidad.
- **ParlaIbero-ES:** preflight público de Dataverse; no se ha incorporado el payload de aproximadamente 1 GB. Requiere revisión de privacidad, campos de hablante, procedencia y calidad.
- **DReaM-es-open:** preflight de 9.115.151 tokens, 717.854 frases y 128 documentos. No se ha exportado texto; la muestra contiene material de idiomas y fuentes mezcladas, y exige revisión por documento.
- **VoxPopuli:** los 1.041 registros inspeccionados siguen retenidos por el alcance de derechos del material parlamentario, atribución y privacidad.

## Estados que no se deben confundir

| Estado | Significado | ¿Puede entrenar? |
|---|---|---|
| Admitido | Versión, alcance de derechos, calidad, privacidad, deduplicación y particiones revisados y registrados | Sí, solo la partición train |
| Implementado parcialmente | Hay textos, metadatos o un adaptador reproducible, pero falta alguna comprobación | No |
| Candidato | Descargado o localizado, aún sin completar los controles | No |
| Cuarentena / rechazado | Derechos incompatibles, privacidad, procedencia o integridad sin resolver | No |
| Solo metadatos | Índices, catálogos o grafos sin permiso para usar el texto enlazado | No |

## Estructura

- \`admitted/\`: únicamente corpus con manifiesto inmutable y controles aprobados.
- \`candidates/\`: descargas, muestras y artefactos que todavía no han superado todas las comprobaciones.
- \`quarantine/\`: material bloqueado o incompatible.
- \`rights_registry/\`: registro de derechos de alcance exacto por versión/payload.
- \`libraries/\`: inventario de las 32 bibliotecas, sus README y estado de implementación.
- \`catalog/\`: mapa ampliado de fuentes y dominios.

Los payloads grandes se publican como artefactos versionados de GitHub Actions, no como blobs gigantes en Git. Cada artefacto debe acompañarse de hashes, manifiesto, versión de fuente y decisión.

## Controles obligatorios antes de admitir una biblioteca

1. Descarga pública anónima, sin credenciales, acuerdos privados ni condiciones de acceso restringidas.
2. Revisión de licencia y derechos del documento/versión exactos; no basta una etiqueta global del repositorio.
3. Conservación de atribución, autoría, fuente, URL y revisión inmutable.
4. SHA-256 de payload, texto normalizado y particiones.
5. Detección de duplicados exactos y aproximados entre las 64 bibliotecas y los corpus de evaluación.
6. Revisión de PII, secretos y contenido sensible.
7. Control de idioma, codificación, OCR, ruido y relevancia temática.
8. Separación determinista de documentos entre train, validation y test.
9. Revisión humana de muestras y decisión registrada.
10. Validación de manifiestos y del gate global G-0.

Una licencia CC0/CC BY en un catálogo no convierte automáticamente en reutilizable el contenido de terceros que ese catálogo describe. Los datos estructurados, metadatos bibliográficos, código, voz, transcripciones y prosa se mantienen separados cuando sus derechos o naturaleza son distintos.

## Ensamblado parcial del pipeline legado de 32 bibliotecas

El workflow \`.github/workflows/assemble-32-libraries.yml\` descarga artefactos fijados de CoVoST, Common Corpus, GPLSI y literatura, verifica sus hashes y genera un paquete candidato con 32 directorios para los 16 dominios originales. Este paquete legado no sustituye el inventario canónico de 64 bibliotecas.

- Los textos CoVoST con señal temática suficiente se asignan a un único dominio; no se fuerzan textos ambiguos a una temática incorrecta.
- Las traducciones sin señal temática suficiente se conservan en un pool transversal no asignado.
- Los textos de Common Corpus con derechos, privacidad, idioma o tipo de contenido pendientes se conservan en un fichero de revisión, fuera de las bibliotecas entrenables.
- GPLSI se conserva como candidato jurídico hasta resolver los derechos de cada fuente original.
- Los 608 documentos admitidos de literatura española se incorporan ahora a Humanidades, repartidos entre General/HKD por densidad y bytes. Se reconstruyen desde el manifiesto documental, se verifica el SHA-256 de cada fragmento y se conserva estrictamente su partición original train: no se generan validation/test a partir de esos textos.

El paquete resultante se llama \`ronin-32-libraries-partial-candidates\`. Su manifiesto registra el número de documentos, bytes y SHA-256 por biblioteca y partición. **El paquete es candidato: no habilita entrenamiento.**

## Registro de derechos de nivel A

El registro \`rights_registry/records.jsonl\` conserva ocho evidencias de alcance exacto, incluidas CoVoST 2 y varias fuentes de metadatos CC0. Las entradas de OpenAlex, Crossref, DataCite, ROR y OpenCitations son metadatos; no cuentan como texto sustantivo de preentrenamiento.

Ejecutar \`python scripts/validate_rights_registry.py\` para validar el registro. Un registro de derechos no sustituye los controles de calidad, privacidad, deduplicación, atribución, integridad de particiones ni G-0.

## Decisión actual

**No se inicia entrenamiento.** El gate global G-0 sigue en FAIL y la única biblioteca/corpus admitido continúa siendo la literatura española de 608 documentos. El objetivo inmediato es convertir candidatos verificables en contenido admitido y reconciliar derechos y completar, de forma equilibrada y trazable, las 64 bibliotecas.


## Nuevo bloque revisado — Corpus paralelo de Naciones Unidas v1.0 (2026-11-05)

- **Resultado:** fuente oficial y alcance de derechos verificados para la colección UN Parallel Corpus v1.0; apta para iniciar ingestión técnica, pero todavía no admitida ni entrenable.
- Contiene documentos oficiales y parlamentarios de Naciones Unidas redactados y traducidos manualmente entre 1990 y 2014, en seis idiomas, incluido español, con alineación por frases. El proveedor declara que los documentos de esta colección están en dominio público.
- Se ha creado el expediente `candidates/un-parallel-corpus-v1/README.md` con fuentes oficiales, alcance, atribución, exclusiones y controles pendientes.
- Los conjuntos oficiales de desarrollo/prueba de 2015 quedan fuera de train. El corpus se mantendrá en un pool transversal hasta clasificar cada documento por temática; no se asignará todo en bloque a Derecho o Ciencias Sociales.
- **Pendiente antes de Grado A:** descarga completa de los fragmentos, SHA-256, validación TEI/bitext y alineaciones, privacidad, calidad, deduplicación global, asignación General/HKD y revisión humana.
- Fuentes: https://www.un.org/dgacm/es/content/uncorpus/es · https://www.un.org/dgacm/en/content/uncorpus/download · https://www.un.org/dgacm/sites/www.un.org.dgacm/files/files/UNCORPUS/un.pdf


## Nuevo bloque revisado — ScienceVerse / papers (expansión científica)

- **Resultado:** repositorio, estructura de procedencia y siete corpus declarados CC BY 4.0 identificados. Son **5.091 artículos de catálogo** en BMC Medicine (1.000), eLife (1.000), Frontiers in Psychology (1.000), i-Perception (496), Judgment and Decision Making (855), Journal of Cognition (447) y Open Mind (293).
- El upstream conserva manifiesto por artículo con DOI, título, año, archivo y procedencia; cada corpus tiene documentación y script reproducible. Las licencias originales se mantienen por artículo.
- Expediente: `candidates/scienceverse-expanded-corpora/README.md`.
- **No son 5.091 artículos admitidos:** falta descargar manifests/assets, verificar cada DOI y PDF/texto, hashes, privacidad, deduplicación y particiones. Los corpus con licencias mixtas o NC/ND quedan excluidos salvo filtro individual inequívoco.
- Fuente: https://github.com/scienceverse/papers


## Nuevo bloque revisado — repositorios técnico-científicos públicos

- **NASA NTRS:** catálogo con más de 200.000 documentos completos. Solo se aceptarán documentos públicos con metadatos de copyright inequívocos como “Work of the US Gov. Public Use Permitted”; se excluye cualquier material registrado, privado, mixto o de terceros no autorizado. Expediente: `candidates/nasa-ntrs-public-use/README.md`.
- **NIST Technical Series/PDR:** política oficial concede derechos mundiales sobre trabajos/datos propios de NIST en los términos publicados y exige atribución; los trabajos de terceros se excluyen. Cada documento/dataset requiere comprobación de autoría y titularidad. Expediente: `candidates/nist-technical-series/README.md`.
- **Estado de ambos:** candidatos de alta prioridad; todavía sin payload, hashes, revisión de privacidad/calidad, deduplicación ni particiones. No entrenables.
- Fuentes: https://sti.nasa.gov/disclaimers/ · https://ntrs.nasa.gov/ · https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications · https://data.nist.gov/pdr/about


## Bloque Humanidades — BNE y Project Gutenberg

- **BNE / Biblioteca Digital Hispánica:** catálogo y licencia CC BY 4.0 de metadatos verificados. Los enlaces OCR no heredan automáticamente esa licencia; solo se extraerán obras con derechos individuales claros. Expediente: `candidates/bne-bdh-ocr/README.md`.
- **Project Gutenberg:** fuente de descubrimiento, no licencia global. El proveedor advierte que dominio público en EE. UU. no equivale a dominio público en España/UE y que permisos individuales no se transfieren. Expediente: `candidates/project-gutenberg/README.md`.
- Ambas quedan en implementación parcial; sin texto admitido adicional hasta superar la revisión por obra/edición.

## ScienceVerse — adquisición candidata verificada (5 de noviembre de 2026)

Se descargaron cinco de los siete corpus prioritarios desde la revisión upstream 3a6ac0125e576423300a8996e9ad4c5d65ef9fe2. Son 3.091 filas DOI elegibles y 95.948.088 bytes de assets RDS comprimidos, no texto extraído:

| Corpus | Filas elegibles | Bytes RDS | SHA-256 |
|---|---:|---:|---|
| BMC Medicine | 1.000 | 30.450.200 | fe81c3c6688cb007ccdbbd082b22e74bdaa17ce2e9735ddc276e083108d8d000 |
| Judgment and Decision Making | 855 | 24.875.707 | 3381725686b9b1bae2a2c764ea87fdf52b8575cf8d87902388abd333319d3aa6 |
| Journal of Cognition | 447 | 15.559.915 | 12766fe41d80dcffc1da26056c929c7e39fb56be772809fa1620887df8838ae5 |
| Open Mind | 293 | 12.639.050 | c27fd53e8e640f7ac4cb3cfe43d04bfdc8a80c050956df3ec8abc6931d796feb |

JOC tiene 448 filas de manifiesto; se excluyó el DOI 10.5334/joc.316 porque xml_exists=FALSE e in_rds=FALSE. La fila declara CC BY 4.0, pero no está convertida ni en el RDS. Los tres corpus restantes del bloque prioritario (eLife, Frontiers in Psychology e i-Perception) siguen sin payload.

Los manifiestos, hashes completos y exclusión exacta están en candidates/scienceverse-expanded-corpora/README.md y en cada provenance.json. La adquisición se incorporó en el commit 68497f153e06c18cd693c3ef77e229bfd3defbb8.

La inspección RDS está pendiente de una ejecución verde. Los runs 42001889049 y 42001946701 fallaron por un límite de recorrido estructural y por instalación de jsonlite en una biblioteca R no escribible. Los commits 1df303a y fd61d25 acotan el muestreo y usan el paquete de sistema r-cran-jsonlite; la siguiente ejecución debe confirmar el arreglo.

**No son Level A ni entrenables:** faltan inspección estructural, exportación a texto, verificación de licencia del editor por artículo/versión, titularidad y terceros, retractaciones, privacidad, calidad, deduplicación global y splits por DOI. Los 83.524.872 bytes RDS no se suman al contador de texto admitido.

## Adquisición documental verificada — corte 2026-11-05

Estos recuentos separan material descargado de material admitido:

| Línea | Documentos candidatos | Payload descargado |
|---|---:|---:|
| ScienceVerse (BMC Medicine, JDM, Journal of Cognition, Open Mind, i-Perception) | 3.087 DOI únicos en manifiestos elegibles | 95.948.088 bytes RDS |
| NASA NTRS public-use | 189 textos completos | 15.417.212 bytes UTF-8 |
| ScienceVerse Crossref (eLife + Frontiers) | 824 DOI únicos | 87.589.919 bytes RDS |\n| **Total candidato adquirido** | **4.100 registros** | **198.955.219 bytes** |

ScienceVerse conserva manifiestos, procedencia y hashes por paquete; eLife y Frontiers se admiten al nivel candidato solo cuando Crossref confirma CC-BY 4.0; cuatro filas JDM con DOI duplicado/conflictivo y una fila de Journal of Cognition sin conversión se excluyen de los manifiestos elegibles. NASA exige metadatos por documento de uso público, sin material de terceros, sin control de exportación y sin indicador de información sensible. Ambos conjuntos siguen en `candidates/`: no se suman a bytes Level A ni habilitan entrenamiento. La deduplicación cruzada, revisión humana de derechos/atribución, privacidad, calidad y clasificación General/HKD siguen pendientes.

El único conjunto admitido sigue siendo `literature-es-v1`: 608 documentos en train y 140.295.523 bytes en su artefacto de materialización. Validation y test no se entrenan.
