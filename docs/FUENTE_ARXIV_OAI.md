# Fuente arXiv OAI — preflight de licencias por artículo

## Alcance de esta fase

El workflow `.github/workflows/preflight-arxiv-oai.yml` consulta exclusivamente los metadatos públicos OAI-PMH de arXiv. No descarga PDF, e-print, archivos TeX, texto completo ni adjuntos.

El adaptador usa el formato `arXiv`, que expone la URI de licencia de cada artículo. El preflight solo clasifica como candidatos potencialmente reutilizables las URI exactas de CC BY 4.0 y CC0 1.0. La licencia por defecto de distribución de arXiv no concede permiso general para republicar el texto y queda fuera.

## Dominios inspeccionados

El selector usa los sets de categoría OAI disponibles y muestrea matemáticas, lógica, filosofía de la física/ciencias sociales, física, química, biología cuantitativa, informática y economía/finanzas. Los resultados son muestras, no un censo completo; el informe guarda los setSpec, recuentos y ejemplos de metadatos sin abstracts. El muestreo sigue los `resumptionToken` OAI hasta alcanzar el límite configurado, en vez de truncar silenciosamente en la primera página. La ejecución programada inspecciona hasta cuatro sets por dominio y 1.000 registros por set.

## Límites y gates

- Se respeta una separación mínima de tres segundos entre peticiones OAI y no se realizan peticiones concurrentes. La paginación conserva el mismo control de ritmo y registra cuántas páginas se inspeccionaron por set.
- La URI de licencia debe coincidir exactamente con CC BY 4.0 o CC0 1.0; no se infiere permiso a partir de que el artículo sea accesible.
- El CC0 de los metadatos no se interpreta como licencia CC0 del artículo.
- No se descarga contenido y el informe fija `candidate_text_downloads_authorized=false`, `training_eligible=false` y `admitted=false`.
- Antes de cualquier descarga futura se necesitará una autorización limitada explícita, versión del artículo fijada, verificación de licencia, revisión de contenido de terceros y deduplicación con PMC/Common Corpus.

## Referencias oficiales

- OAI-PMH y formatos de metadatos: https://info.arxiv.org/help/oa/index.html
- Reutilización institucional y verificación de la licencia por artículo: https://info.arxiv.org/help/license/reuse.html
- Acceso a metadatos y texto completo y límites de acceso: https://info.arxiv.org/help/bulk_data.html
