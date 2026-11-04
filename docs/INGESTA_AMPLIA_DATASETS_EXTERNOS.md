# Ingesta amplia de datasets externos

## Objetivo

Este registro amplía en una sola iteración el mapa de fuentes de conocimiento de RONIN: ciencia, medicina, derecho, ingeniería, código, humanidades, literatura, economía, política, lingüística, traducción y grafos semánticos.

El registro contiene 21 fuentes. No significa que se hayan descargado 21 corpus ni que todos estén autorizados para entrenamiento. Distingue explícitamente fuentes ya presentes en el proyecto, candidatos descargables, índices de descubrimiento y fuentes condicionadas por derechos.

## Regla G-0: primero los derechos, después el texto

La disponibilidad gratuita o el acceso abierto no equivalen a una licencia de entrenamiento. El manifiesto mantiene `training_eligible=false` para todos los registros hasta que exista una auditoría documental.

Antes de admitir un documento o archivo se debe conservar:

1. URL de origen y versión/release del dataset.
2. Identificador estable del documento, autor/editor y fecha cuando existan.
3. Licencia exacta o fundamento verificable de dominio público, a nivel documento/archivo cuando corresponda.
4. Evidencia de compatibilidad con los usos previstos por RONIN, incluidos usos comerciales potenciales.
5. Revisión de material de terceros, imágenes, anexos, traducciones y aparato editorial.
6. Hash SHA-256, idioma, dominio, formato y resultado de control de calidad.
7. Registro de exclusiones, opt-outs y duplicados.

Las licencias no comerciales, sin obras derivadas, desconocidas, publisher-specific o ambiguas permanecen en cuarentena bajo la política actual. Los requisitos de atribución y share-alike deben conservarse cuando se apruebe una fuente.

## Prioridad de ingestión propuesta

| Prioridad | Fuentes | Motivo |
|---|---|---|
| P0 | Common Corpus, PMC OA, Caselaw Access Project, CLiGS/CoNSSA/ELTeC ya presentes | Gran densidad semántica y dominios complementarios; las tres últimas no se vuelven a importar |
| P1 | Wikidata, Project Gutenberg, PatentsView, OpenAlex metadata, OpenAlex full text filtrado, The Stack, Wikimedia, Stack Exchange, arXiv, OPUS, IULA | Conocimiento estructurado, técnica, ciencia, código, traducción y humanidades |
| P2 | Harvard Dataverse, CORE, Europarl | Descubrimiento y conjuntos específicos que requieren auditoría por depósito/release |
| P3 | Common Crawl | Solo descubrimiento de fuentes hasta resolver derechos de origen |

## Observaciones críticas por fuente

- **Common Corpus**: declara 2,27 billones de tokens y metadatos por documento con licencia, idioma, colección y procedencia. La ingesta debe filtrar explícitamente registros permitidos; no aceptar el dataset completo sin filtro.
- **PubMed Central**: descargar exclusivamente el Open Access Subset. NLM advierte que no se debe descargar masivamente todo PMC, porque gran parte de los artículos conserva restricciones tradicionales.
- **Caselaw Access Project**: Harvard describe sus datos como abiertos para uso sin limitaciones; guardar la declaración y los términos exactos del release usado.
- **OpenAlex**: los metadatos CC0 son un índice, no una licencia sobre el texto completo de los artículos. El texto se evalúa por ubicación/licencia del trabajo.
- **The Stack**: código en una vía separada. Mantener licencia SPDX por archivo, procedencia de repositorio, obligaciones de atribución, exclusiones de seguridad y opt-outs.
- **Wikimedia y Stack Exchange**: preservar atribución y obligaciones de la versión CC BY-SA que corresponda.
- **arXiv, OPUS, IULA, CORE, Harvard Dataverse y Europarl**: no existe una licencia global aplicable automáticamente a todo el contenido; filtrar por documento, subcorpus, depósito o release.
- **Project Gutenberg**: comprobar jurisdicción, obra, traducción y edición; no inferir que cualquier edición del catálogo es de dominio público en todas las jurisdicciones.
- **Wikidata**: los datos estructurados CC0 pueden alimentar un grafo semántico. Si RONIN verbaliza triples, etiquetar esas frases como verbalizaciones derivadas y no como citas de una fuente original.

## Cómo usar el registro

Validación local, sin descargar corpus ni activar entrenamiento:

```bash
python scripts/validate_external_datasets.py
python scripts/validate_external_datasets.py --json-out reports/external-dataset-intake.json
```

El informe contabiliza candidatos por estado/prioridad y enumera qué registros están listos para revisión. No declara elegibilidad de entrenamiento.

## Fases posteriores

1. **Inventario y validación** — cubiertos por esta iteración.
2. **Muestras pequeñas** — descargar muestras de P0/P1 con límites de tamaño, checksum y metadatos; no descargar archivos completos por defecto.
3. **Auditoría G-0** — decisión por documento/archivo y registro de evidencia.
4. **Normalización y deduplicación** — conservar alineaciones, estructura, procedencia y licencia.
5. **Admisión al corpus** — crear manifiestos separados por dominio y split; no modificar el corpus oficial hasta aprobar el lote.
6. **Entrenamiento** — solo tras revisión explícita de los manifiestos admitidos.

## Fuentes oficiales consultadas

- Common Corpus: https://huggingface.co/datasets/PleIAs/common_corpus
- NLM, límites de descarga de PMC: https://support.nlm.nih.gov/knowledgebase/article/KA-03584/en-us
- NLM, definición de PMC OA Subset: https://support.nlm.nih.gov/knowledgebase/article/KA-03253/en-us
- Harvard Library, Caselaw Access Project: https://library.harvard.edu/services-tools/harvard-library-datasets
- USPTO PatentsView: https://www.uspto.gov/ip-policy/economic-research/patentsview
- OpenAlex snapshot/full text: https://help.openalex.org/access/overview/
- OpenAlex vocabulario de licencias: https://help.openalex.org/data/licenses/
- BigCode The Stack: https://www.bigcode-project.org/docs/about/the-stack/
- BigCode opt-out: https://github.com/bigcode-project/opt-out-v2
- Wikimedia dumps: https://dumps.wikimedia.org/
- arXiv bulk data: https://info.arxiv.org/help/bulk_data/index.html
- OPUS: https://opus.nlpl.eu/
- Project Gutenberg: https://www.gutenberg.org/
- IULA ES-EN: https://legacy.lt-innovate.org/lt-observe/resources/iula-es-en-technical-corpus
- Harvard Dataverse: https://dataverse.harvard.edu/
- CORE: https://core.ac.uk/services#api
- Common Crawl: https://commoncrawl.org/
- Europarl: https://www.statmt.org/europarl/
- CLiGS Textbox: https://github.com/cligs/textbox
- CoNSSA: https://github.com/cligs/conssa
- ELTeC-spa: https://github.com/COST-ELTeC/ELTeC-spa
