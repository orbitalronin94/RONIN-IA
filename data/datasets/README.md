# Bibliotecas de datos de RONIN

Este directorio es el espacio canónico para adquirir, revisar, clasificar y versionar los textos de entrenamiento de RONIN.

## Objetivo operativo

La primera arquitectura de corpus se compone de **32 bibliotecas: 16 dominios × General/HKD**. HKD significa *alta densidad de conocimiento*. General y HKD son particiones disjuntas: el material de mayor densidad semántica se asigna a HKD y el resto a General. El reparto se equilibra por bytes de texto UTF-8, no solo por número de documentos.

El catálogo ampliado de 32 dominios y 64 particiones es una hoja de ruta posterior. No sustituye este objetivo operativo de 32 bibliotecas.

## Estado real del corpus

**Estado:** 1 corpus admitido; 32 bibliotecas en implementación parcial.

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
5. Detección de duplicados exactos y aproximados entre las 32 bibliotecas y los corpus de evaluación.
6. Revisión de PII, secretos y contenido sensible.
7. Control de idioma, codificación, OCR, ruido y relevancia temática.
8. Separación determinista de documentos entre train, validation y test.
9. Revisión humana de muestras y decisión registrada.
10. Validación de manifiestos y del gate global G-0.

Una licencia CC0/CC BY en un catálogo no convierte automáticamente en reutilizable el contenido de terceros que ese catálogo describe. Los datos estructurados, metadatos bibliográficos, código, voz, transcripciones y prosa se mantienen separados cuando sus derechos o naturaleza son distintos.

## Ensamblado parcial de las 32 bibliotecas

El workflow \`.github/workflows/assemble-32-libraries.yml\` descarga artefactos fijados de CoVoST, Common Corpus, GPLSI y literatura, verifica sus hashes y genera un paquete candidato con 32 directorios General/HKD.

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

**No se inicia entrenamiento.** El gate global G-0 sigue en FAIL y la única biblioteca/corpus admitido continúa siendo la literatura española de 608 documentos. El objetivo inmediato es convertir candidatos verificables en contenido admitido y completar, de forma equilibrada y trazable, las 32 bibliotecas.


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

## Adquisición ScienceVerse automatizada (2026-11-05)

Se han añadido script y workflow para incorporar a `main` cuatro paperlists de texto completo con manifiestos por artículo: BMC Medicine (1.000), Judgment and Decision Making (855), Journal of Cognition (447) y Open Mind (293). **Objetivo: 2.595 documentos.** El proceso rechaza un corpus si alguna fila del manifiesto no declara CC-BY 4.0; conserva CSV DOI/licencia, payload RDS, procedencia y SHA-256. Solo se sumarán al recuento de admisión cuando el workflow termine correctamente y los ficheros estén verificados. Deduplicación global, retractaciones, privacidad y particiones siguen siendo gates obligatorios.
