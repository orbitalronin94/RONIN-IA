# Nuevas fuentes scopeadas para ampliar el corpus

Fecha: 2026-11-06. Esta PR amplía el registro de adquisición; **no incorpora todavía documentos al corpus entrenable**. Los volúmenes son potenciales y no se cuentan hasta descargar texto, verificar derechos por documento, deduplicar y generar manifiestos.

## Fuentes prioritarias

| Fuente | Biblioteca objetivo | Potencial útil | Estado y puerta de derechos |
|---|---|---|---|
| BNE / Biblioteca Digital Hispánica (BDH) | Historia y fuentes primarias en español | Colección de obras históricas en dominio público; distribución TXT y OCR | P0. Limitarse estrictamente a la colección catalogada como dominio público; verificar que cada OCR corresponde a una obra incluida. |
| USGS Publications Warehouse | Geología, hidrología, geografía y riesgos naturales | Catálogo técnico extenso con API y enlaces a publicaciones | P0. Solo informes/datos producidos por USGS; el índice también incluye obras de terceros. Excluir figuras/fotos de terceros. |
| NOAA Institutional Repository | Clima, océanos, atmósfera y pesca | Repositorio científico-técnico con texto completo | P1. Solo obras federales/CC0 o licencia permisiva explícita. Artículos y proceedings pueden conservar copyright. |
| NIST Publications | Informática, metrología, ciberseguridad e ingeniería | Publicaciones técnicas de alta densidad | P1. Revisar cada documento: no asumir que normas externas, figuras o material editorial están en dominio público. |
| Europeana | Historia y cultura europeas, lenguas | Agregador de objetos digitales y transcripciones de instituciones culturales | P1. Consultar edm:rights por objeto; admitir solo PDM, CC0 y CC BY compatible. La licencia CC0 de los metadatos no cubre el objeto digital. |
| Library of Congress | Historia, derecho y documentos gubernamentales | Colecciones digitalizadas y OCR | P2. No usar el catálogo completo: seleccionar obras gubernamentales de EE. UU. o ítems con derechos PDM/CC0 explícitos; revisar derechos de terceros y privacidad. |
| GovInfo | Legislación, política pública e informes federales | Paquetes oficiales XML/HTML/PDF | P2. Solo obras de autoría gubernamental; revisar inserciones, fotografías y material de terceros. |
| DOE OSTI | Energía, física y materiales | Gran índice de información científica y técnica financiada por DOE | Discovery-only. OSTI advierte expresamente que acceso público no significa dominio público; solo incorporar documentos con aviso/permiso de reutilización explícito. |

## Fuentes descartadas o restringidas

- **OpenStax**: no se incorpora al corpus general. Sus libros se publican bajo CC BY-NC-SA, que prohíbe usos comerciales; no satisface una política de reutilización comercialmente neutral. Solo reconsiderar si el proyecto acepta expresamente esa restricción y puede cumplir ShareAlike.
- **DOE OSTI**: no se hará descarga masiva por el mero hecho de que el repositorio sea público.
- **Europeana y Library of Congress**: metadatos, OCR y objeto digital son capas de derechos distintas; no se inferirá licencia del texto a partir de la licencia de los metadatos.
- **FineWeb2, Dolma, Common Pile y Common Crawl**: continúan en discovery hasta que cada componente/fuente tenga una cadena de derechos verificable.

## Reglas de admisión comunes

1. Guardar identificador upstream, URL del registro, URL del payload, fecha de captura y versión.
2. Guardar licencia/rights URI y evidencia de derechos asociada al documento, no solo al repositorio.
3. Descargar texto completo y calcular SHA-256 del archivo original y del texto UTF-8 normalizado.
4. Conservar autoría, título, institución y atribución requerida; no incorporar metadatos personales innecesarios.
5. Excluir contenido de terceros, datos personales/sensibles, documentos retractados y OCR ilegible.
6. Ejecutar deduplicación exacta y aproximada contra train, validation y test; ningún documento puede cruzar particiones.
7. Dejar training_eligible=false hasta superar G-0 y revisión humana. Los candidatos no suman al contador entrenable.

## Próximos lotes de adquisición

1. BNE/BDH: descargar snapshot TXT y medir número de obras, OCR disponible, bytes UTF-8 y distribución por idioma/año.
2. USGS: consultar API, seleccionar publicaciones propias y comprobar PDF/texto y avisos de derechos.
3. NOAA/NIST/GovInfo: extraer inventarios y filtrar por autoría y avisos de derechos.
4. Europeana/LOC: usar derechos por ítem y exigir OCR/transcripción descargable.
5. DOE OSTI: solo preflight, sin bulk download hasta resolver derechos.

## Resultado de esta PR

- Fuentes nuevas añadidas al registro: 8.
- Documentos descargados en esta PR: 0.
- Documentos nuevos admitidos como entrenables: 0.
- Bytes nuevos contabilizables: 0.
- No se modifica el modelo ni el holdout.
