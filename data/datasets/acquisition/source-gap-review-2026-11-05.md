# Auditoría de fuentes sin representación en el corpus entrenable

Fecha de corte: 2026-11-05. Revisión documental y de fuentes oficiales; no equivale a una auditoría jurídica ni a una admisión de datos.

## Punto de comparación

El train scoped vigente en `main` contiene 15.762 documentos y 638.969.315 bytes UTF-8: literatura española (608), Mathlib4 (8.498), NASA file-reviewed (6), Papers propios (9) y ScienceVerse (6.641). Esta auditoría busca fuentes con texto no representado en ese inventario. No suma candidatos, metadatos ni subconjuntos solapados.

## Resultado: fuentes nuevas o con contenido no representado

| Prioridad | Fuente | Qué aporta sin representación actual | Evidencia de acceso/derechos | Bloqueo antes de entrenar |
|---|---|---|---|---|
| P0 | BNE/BDH — Documentos en dominio público | Texto histórico en español procedente de obras digitalizadas; distribución TXT y enlaces a OCR por obra | La ficha oficial identifica expresamente las obras incluidas como dominio público y señala reutilización CC BY 4.0. El TXT es una distribución descargable; última actualización declarada: 2024-12-04. | Descargar snapshot y fijar hash; unir registro y URL de texto; confirmar que cada obra pertenece al conjunto PD; OCR, terceros, calidad, PII, dedup exacta/aproximada y splits. El workflow citado anteriormente no existe en `main`. |
| P0 | USGS Publications Warehouse — publicaciones propias USGS | Geología, hidrología, geografía, riesgos naturales, ciencias de la Tierra e informes técnicos | USGS declara de dominio público la información y publicaciones producidas por USGS y pide atribución. Su catálogo también indexa publicaciones de terceros. | Limitarse a informes/publicaciones USGS propios con PDF oficial; excluir artículos externos y activos visuales de terceros; extraer texto, inspeccionar avisos, hashes, OCR, PII, dedup y splits. |
| P1 | PMC Article Datasets — subconjunto CC0/CC BY | Investigación biomédica y ciencias de la vida a gran escala; distinto del conjunto ScienceVerse ya entrenable | NLM indica que solo el subconjunto OA tiene licencias de reutilización; el harvester existente filtra licencia por artículo/versión y descarga por el servicio AWS oficial. | Es candidato, no train. Verificar artefactos y hashes del run, exclusiones NC/ND/SA/TDM/retractados, datos sensibles, near-duplicates y particiones. Mantener el límite del workflow de 2 GiB por ejecución. |
| P1 | CoVoST 2 — traducciones text-only | Texto de traducción español↔inglés/catalán, no presente como corpus específico en el train actual | El README upstream fijado declara CC0 para CoVoST data; el ledger contiene registros de derechos y hashes de archivo/exportación. El export limita los campos a `translation`. | El artefacto anterior no debe promoverse: el split se perdió en un export anterior. La PR #103 corrige la extracción para conservar y filtrar train/train_covost; requiere run/artifact posterior, inspección lingüística, dedup global, aislamiento de validation/test y manifiesto train. No reconstruir pares fuente/objetivo con Common Voice sin una revisión separada. |
| P1 | ParlaIbero-ES v2.0 — intervenciones parlamentarias | Español institucional y político contemporáneo, con vocabulario jurídico/administrativo no cubierto de forma equivalente por literatura | El preflight del repositorio identifica el conjunto y la licencia declarada CC BY 4.0; el payload principal citado es de aproximadamente 1,06 GB. | No descargado en el preflight. Antes de adquirir, confirmar licencia/versión exactas y retirar nombres de oradores, partidos, distritos, IDs persistentes y atributos personales; exportar solo texto, revisar privacidad, hash, dedup y splits. PR #105 no lo admite. |
| P2 | NOAA Institutional Repository — obras gubernamentales seleccionadas | Meteorología, océanos, clima, pesca, atmósfera y documentación técnica | NOAA indica que las obras del Gobierno federal están disponibles bajo CC0; artículos y proceedings mantienen derechos del titular. Si falta aviso explícito de copyright, debe tratarse como protegido. | Selección individual de documentos con aviso gubernamental/CC0 explícito; excluir artículos protegidos y terceros; conservar atribución, extraer texto, revisar PII, dedup y splits. |
| P2 | DReaM-es-open | Gramáticas, documentación lingüística y descripciones de 94 lenguas; 128 documentos indexados | El catálogo de fuentes registra preflight de API y metadatos, pero no una autorización global aplicable a todos los documentos. | Resolver derechos por documento y versión, descargar texto verificable, hashes, revisión de terceros y dedup. No sumar los 128 como textos descargados. |
| P2 | UN Parallel Corpus v1.0 | Texto paralelo oficial multilingüe, incluido español; posible valor de transferencia lingüística | La fuente declara dominio público, pero el registro local aún lo clasifica como candidato pendiente de hash y revisión territorial. | Fijar archivo y hash, comprobar alcance de dominio público para traducciones y jurisdicciones, filtrar encabezados/ruido, revisar calidad y privacidad, deduplicar y separar pares/splits. |
| P3 | Project Gutenberg | Literatura y no ficción histórica multilingüe adicional | El acceso al catálogo no acredita por sí mismo el estado de dominio público en España/UE ni los derechos de traducción/edición. | Admisión por obra y edición, con análisis territorial y de traductor/editor; no importar colecciones completas por el estado de copyright estadounidense. |
| P3 | FineWeb2 / Dolma / Common Pile | Potencial masivo y gran diversidad temática | Son mezclas de procedencia y licencias heterogéneas; la licencia de empaquetado/curación no sanea los derechos de cada documento de origen. FineWeb2 y Dolma siguen en descubrimiento; Common Corpus tiene pipeline candidato en PR #122. | No hacer bulk admission. Solo subconjuntos con cadena de derechos por documento, exclusiones/opt-outs, privacidad, calidad, dedup y splits demostrados. |

## Verificación de las fuentes oficiales

### BNE / BDH

La ficha oficial de datos.gob.es describe la colección de documentos en dominio público, explica que incluye metadatos con enlace al objeto digital y al texto OCR, y ofrece distribución TXT y XML. La ficha publica CC BY 4.0 para la reutilización del conjunto y fecha de actualización 2024-12-04. La colección BNE de ePubs es otra distribución: sus ePubs están corregidos y la ficha se actualizó el 2025-03-05, pero no se debe inferir que todos sus textos son dominio público por la licencia del catálogo. Por tanto, P0 es exclusivamente la colección BDH declarada en dominio público, no el catálogo BNE completo ni cualquier ePub.

- Ficha oficial PD: https://datos.gob.es/es/catalogo/ea0019768-biblioteca-digital-documentos-en-dominio-publico1
- Distribución TXT: https://www.bne.es/media/datosgob/bdh/dominiopublico/dominiopublico_txt.zip
- Ficha de ePubs (línea separada): https://datos.gob.es/es/catalogo/ea0019768-biblioteca-digital-coleccion-epubs

### USGS

La política oficial declara de dominio público los datos e información producidos por USGS, pero advierte que imágenes, gráficos y fotografías de terceros pueden mantener copyright. Publications Warehouse es un índice de publicaciones USGS y también de artículos/libros publicados por terceros; los informes PDF publicados por USGS se ofrecen como dominio público. La ingesta debe seleccionar publicaciones propias, no descargar indiscriminadamente todo el índice.

- Copyrights and credits: https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits
- FAQ Publications Warehouse: https://pubs.usgs.gov/documentation/faq

### NOAA

El repositorio confirma que el acceso público no equivale a permiso general de redistribución. Las obras gubernamentales están bajo CC0, pero los artículos y proceedings pueden conservar copyright. Los documentos sin aviso explícito deben tratarse como protegidos.

- Content and Copyright: https://repository.library.noaa.gov/Content%20and%20Copyright

### PMC

La NLM advierte que no todos los artículos de PMC permiten minería y reutilización. El subconjunto OA distribuye artículos con licencias Creative Commons u otras licencias concretas; el servicio AWS y los canales oficiales son los métodos permitidos para descargas automatizadas. El workflow existente de RONIN aplica una allowlist CC0/CC BY a nivel de versión y excluye licencias restrictivas y retractados, pero los artefactos permanecen candidatos hasta superar G-0 y la revisión global.

- Catálogo oficial de PMC OA: https://catalog.data.gov/dataset/pubmed-central-open-access-subset-pmc-oa
- Política de descarga automatizada: https://pmc.ncbi.nlm.nih.gov/tools/textmining/
- PMC AWS: https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/

### SEC EDGAR: no promover por ahora

EDGAR permite acceso público gratuito y automatización moderada con User-Agent declarado y límite de tasa; eso no constituye por sí solo una licencia de dominio público sobre los textos redactados por empresas privadas. La entrada SEC del catálogo interno necesita una revisión de derechos independiente; no la clasifico como bloque mergeable para entrenamiento.

- Accessing EDGAR Data: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data

## Orden de ejecución recomendado

1. **BNE/BDH**: primera adquisición nueva de español. Es la fuente mejor delimitada para una biblioteca española no literaria/histórica, con una colección explícitamente de dominio público y distribución TXT.
2. **USGS**: segundo bloque, limitado a publicaciones oficiales USGS; alta densidad técnica y buen potencial de volumen.
3. **CoVoST 2**: no descargar de nuevo; recuperar el artefacto de la PR #103 tras corregir splits y cerrar dedup/calidad.
4. **PMC OA**: continuar el harvester existente por lotes y revisar artefactos antes de promover.
5. **ParlaIbero-ES**: solo texto anonimizado y tras cerrar los requisitos de privacidad; no mezclar metadatos de oradores con el corpus.
6. **NOAA / DReaM / UN Parallel**: mantener en preflight y admitir solo registros con evidencia completa.

## Criterio de promoción

Un bloque solo pasa a `admitted/` y aumenta el contador train cuando se conservan, como mínimo:

- revisión upstream inmutable y archivo/fichero exacto;
- licencia o prueba de dominio público aplicable al texto concreto;
- atribución y URL de procedencia;
- SHA-256 de archivo y de cada texto normalizado, con bytes UTF-8;
- idioma, calidad y revisión OCR;
- exclusión de PII, secretos, datos sensibles y contenido de terceros no autorizado;
- deduplicación exacta y aproximada contra todos los train actuales y los holdouts;
- particiones deterministas y disjuntas, con solo train elegible;
- manifiesto reproducible y revisión humana documentada.

**Resultado de esta auditoría:** 0 documentos nuevos promovidos. El objetivo es identificar huecos y ordenar la adquisición; no inflar el corpus con cifras de catálogo. La siguiente acción de código debe materializar BNE/BDH como candidato verificable y solo después ejecutar su promoción por documento.


## Actualización de alcance — 2026-11-06

Se añaden ocho fuentes al registro de adquisición y se documentan puertas de derechos específicas en `new-sources-scope-2026-11-06.md`: BNE/BDH, USGS, NOAA, NIST, DOE OSTI, Europeana, Library of Congress y GovInfo.

### Nuevas decisiones

- BNE/BDH y USGS pasan a P0 para preflight y adquisición piloto.
- NOAA, NIST y GovInfo pasan a P1/P2 con revisión documental de autoría y material de terceros.
- Europeana y LOC requieren rights URI/aviso por objeto; CC0 de metadatos no autoriza reutilizar el payload.
- DOE OSTI sigue discovery-only: acceso público no equivale a dominio público.
- OpenStax se excluye del corpus general por CC BY-NC-SA y su restricción no comercial.

**Resultado de esta actualización:** 8 fuentes nuevas scopeadas; 0 documentos nuevos descargados o promovidos; 0 bytes nuevos entrenables. No se modifica la cifra de train scoped ni el holdout.
