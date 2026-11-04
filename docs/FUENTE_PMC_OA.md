# PMC Open Access como fuente de bibliotecas científicas

## Cobertura detectada

El preflight de Europe PMC del 4 de noviembre de 2026 encontró aproximadamente 2,68 millones de resultados para biología/medicina y 471.257 para química bajo la consulta CC BY/CC0. Son resultados potenciales de búsqueda; no equivalen a documentos descargados, elegibles ni admitidos. La muestra de metadatos se verifica además contra el bucket oficial PMC Cloud.

## Ruta vigente

Desde el 26 de agosto de 2026, PMC retiró la distribución antigua FTP/Cloud. RONIN usa el bucket público `pmc-oa-opendata`:

1. Europe PMC pagina identificadores PMCID por dominio.
2. S3 ListObjectsV2 resuelve las versiones disponibles del artículo.
3. Se descarga únicamente el JSON de metadatos de cada versión.
4. Solo tras comprobar licencia, open access y flags de exclusión se solicita el XML JATS de esa versión.
5. Se convierte la URL `s3://` oficial a HTTPS, se verifica el MD5 incluido en la URL y se calcula SHA-256.
6. Se extraen título, abstract, palabras clave y cuerpo; se excluyen figuras, tablas, medios, suplementos, referencias, acknowledgements y otros componentes embebidos.

## Gate por versión

La única allowlist de texto es CC0 y CC BY. Se excluyen CC BY-SA, CC BY-ND, CC BY-NC, TDM, licencias personalizadas y desconocidas. Además, cada versión debe declarar `is_pmc_openaccess=true`, `is_retracted=false`, `is_historical_ocr=false` e `is_manuscript=false`. También se excluyen publicaciones que Europe PMC identifique como retractadas, aunque el flag del bucket no coincida.

La sidecar por documento conserva PMCID, PMID, DOI, título, cita, idioma, versión, ETag de metadatos, hash de metadatos, URL original S3, URL HTTPS, MD5 del XML y SHA-256 del XML y del texto.

## Tamaño y destino

Los workers de biología/medicina y química intentan preparar una biblioteca base y otra HKD por dominio, con un máximo de 8 GiB de texto candidato por dominio y un mínimo de 2,5 GiB de train por biblioteca. El texto se comprime temporalmente en SQLite y se escribe a los splits al finalizar la selección; no se conserva un segundo JSONL completo de entrada.

## Estado jurídico y de entrenamiento

La autorización es limitada a extracción de candidatos CC0/CC BY. Los artefactos siguen marcados `training_eligible=false` y `admitted=false`. G-0 global continúa en FAIL. Cada biblioteca requiere revisión humana de derechos, calidad, datos sensibles y duplicados antes de poder entrar en entrenamiento.

Se conserva la atribución a PMC/NLM y no se implica respaldo de NLM, NIH o los editores. No se reutilizan sus logotipos ni marcas.
