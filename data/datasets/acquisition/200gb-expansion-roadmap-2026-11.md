# Plan de adquisición: 200 GB de corpus textual

Fecha de corte: 2026-11-05. Este plan separa la capacidad potencial de las fuentes del texto realmente incorporado y de la partición finalmente entrenable.

## Objetivo y contabilidad

- Objetivo de programa: **200 GB de texto UTF-8 único, con procedencia y derechos revisados**, repartido entre las 32 bibliotecas General/HKD.
- Primer hito: **2 GB de texto UTF-8 incorporado** (1 % del objetivo decimal). El contador se basa en `text_bytes` de cada documento, no en el tamaño comprimido del shard.
- El árbol `data/datasets/` en `main` medía 803.757.132 bytes (0,749 GiB) antes de introducir el harvester PMC; incluye candidatos, manifiestos y datos admitidos, y no equivale a bytes entrenables.
- No se sumarán los mismos documentos en varias fuentes. Cada registro conserva SHA-256, URL, identificador de origen, licencia, fecha de captura y partición.
- Los documentos nuevos permanecen `training_eligible=false` hasta pasar G-0 global, deduplicación exacta/aproximada, privacidad, calidad, atribución y aislamiento de particiones.

## Fuentes prioritarias y cómo se van a incorporar

| Fuente | Aporte potencial | Regla de incorporación |
|---|---|---|
| PMC Article Datasets (AWS) | Millones de versiones de artículos biomédicos y de ciencias de la vida | Solo versiones PMC OA con licencia individual CC0 o CC BY; excluir NC, ND, SA, TDM-only, retractados y contenido con señales de datos sensibles. Descargar únicamente por el servicio AWS/eSearch documentado. |
| ScienceVerse | 446.092.799 bytes ya extraídos y 7.365 registros scoped | Desbloquear la deduplicación global y el particionado; no volver a descargar duplicados ni contar los 446 MB como train-ready. |
| NASA NTRS | Colección pública grande de informes aeroespaciales | Consultar la API y permitir solo registros con derechos public-use explícitos, sin material de terceros, con texto íntegro y redistribución verificada. |
| arXiv bulk | Amplia colección de investigación matemática, física, informática y otras disciplinas | Inventariar licencia por artículo/versión; incorporar solo licencias compatibles (prioridad CC0/CC BY), conservar fuente y versión. No tratar “open access” como licencia uniforme. |
| NOAA, USGS, NIST, DOE OSTI y repositorios federales | Informes técnicos, ciencia, ingeniería, clima, geología, energía y estándares | Priorizar obras del Gobierno federal de EE. UU. con aviso de dominio público explícito; excluir contenido de terceros, artículos editoriales y materiales con derechos reservados. |
| FineWeb2, Dolma y Common Pile | Fuentes agregadas de gran escala y diversidad temática | No importar mezclas completas por su licencia de conjunto. Auditar componentes y documentos de origen, exclusiones, opt-outs, privacidad y solapamiento; importar solo subconjuntos cuya cadena de derechos esté demostrada. |
| OpenAlex | Snapshot público de metadatos académicos de cientos de millones de registros | Usarlo para descubrimiento, enlazado y procedencia. No contarlo como corpus de texto de entrenamiento: sus registros son principalmente metadatos, no artículos completos. |

## Implementación actual: PMC OA

El workflow `.github/workflows/harvest-pmc-oa-training-candidates.yml` utiliza la distribución oficial de PMC en AWS y un límite de 2 GiB de texto por ejecución. El script `scripts/harvest_pmc_oa_cc0_ccby.py`:

1. consulta ESearch por ventanas mensuales para respetar el límite de 9.999 resultados de ESearch;
2. consulta metadatos por versión de artículo;
3. verifica `is_pmc_openaccess`, `license_code` CC0/CC BY y el indicador de retractación;
4. descarga exclusivamente el texto extraído, no PDFs, imágenes ni suplementos;
5. aplica controles conservadores de tamaño y patrones sensibles;
6. guarda shards JSONL gzip y un manifiesto de procedencia con SHA-256 y bytes originales;
7. deja todos los registros como candidatos no entrenables.

El workflow puede escribir los shards y manifiestos en `main/data/datasets/candidates/pmc-oa-cc0-ccby-v2/`. Los shards se limitan para respetar el límite por archivo de GitHub. El tamaño comprimido del repositorio y el total de texto UTF-8 se informan por separado.

## Límites de almacenamiento

Git no es un almacén de objetos de 200 GB. El repositorio ya contiene cientos de MB y crecerlo hasta 200 GB degradaría clones, CI y mantenimiento. Este plan usa Git para código, manifiestos, hashes, índices y lotes pequeños. Para superar varios GB de payloads será necesario un almacén de objetos/dataset externo (por ejemplo, bucket S3 compatible o repositorio de datasets con almacenamiento LFS) y mantener aquí los manifiestos, checksums y scripts de descarga. No se afirmará que 200 GB están incorporados en Git mientras no exista un destino persistente con verificación de integridad.

## Fuentes oficiales de referencia

- PMC AWS y sus filtros de licencia comercial: https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/
- README de la distribución PMC AWS (estructura, metadatos, inventario, ESearch-S3 y filtros de licencia): https://pmc-oa-opendata.s3.amazonaws.com/README.txt
- Reglas de recuperación automatizada de PMC y variación de licencias: https://pmc.ncbi.nlm.nih.gov/tools/textmining/
- Acceso bulk de arXiv y términos: https://info.arxiv.org/help/bulk_data.html
- Common Crawl: https://www.commoncrawl.org/get-started
- OpenAlex snapshot y tamaños: https://help.openalex.org/access/snapshot/
- OpenAlex licencia CC0: https://github.com/ourresearch/openalex-docs/blob/main/license.md

## Estado

El objetivo de 200 GB es un objetivo de adquisición, no una cifra ya conseguida. El hito del 1 % solo se marcará cuando los manifiestos sumen al menos 2.000.000.000 bytes de texto incorporado y los shards correspondientes existan en un almacenamiento persistente verificable. La elegibilidad para entrenamiento se contabiliza aparte.
