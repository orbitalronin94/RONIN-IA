# Plan de expansión masiva del corpus entrenable

Corte: 2026-11-05. Este documento prioriza adquisición y desbloqueo de texto real. No cambia por sí solo ningún estado de admisión ni autoriza entrenamiento.

## 1. Base verificable del repositorio

La fuente canónica es `data/datasets/README.md` y sus manifiestos. A este corte:

| Corpus | Documentos / bytes | Estado real |
|---|---:|---|
| Literatura española | 608 train / 140.295.523 bytes | Train habilitado dentro de su manifiesto scoped |
| Lean mathlib4 | 8.498 train / 97.629.252 bytes | Train habilitado dentro de su manifiesto scoped; Apache-2.0 |
| **Base train scoped** | **9.106 documentos / 237.924.775 bytes** | No equivale a validación global del inventario de 64 bibliotecas |
| ScienceVerse | 7.365 admitidos scoped / 446.092.799 bytes | No entrenable todavía: deduplicación global, splits y validaciones pendientes |
| NASA NTRS | 813 admitidos scoped / 32.313.859 bytes | No entrenable como corpus completo; recheck de redistribución y controles globales pendientes. Solo 2 documentos file-reviewed se habilitaron |
| Papers propios | 9 documentos / 750.857 bytes | Autorizados por el propietario; controles globales y splits pendientes |
| CoVoST 2 | 432.475 filas / 86.874.752 bytes en un run | Solo traducciones CC0; reconciliar snapshots, splits y deduplicación antes de admitir |
| PleIAs Common Corpus | 2.159 filas / 5.971.320 bytes en un run | 2.149 CC0, 4 CC BY 3.0 y 6 CC BY 4.0; revisión humana, privacidad, calidad y splits pendientes |
| BNE/BDH | Distribución TXT/XML identificada | Workflow de adquisición ya documentado; candidatos hasta cerrar hashes, enlace registro-texto, revisión y splits |

No sumar lotes/snapshots solapados. El número de documentos encontrados, descargados o con licencia aparente no es el número entrenable.

## 2. Objetivos de volumen

- Corto plazo: desbloquear primero los corpus ya descargados y con auditorías avanzadas; objetivo operativo de superar **1 GiB de texto train único**.
- Medio plazo: **10 GiB** de texto train, equilibrado por dominio y calidad.
- Largo plazo: **100 GiB** únicamente si el coste de almacenamiento, limpieza, entrenamiento y evaluación lo justifica.

Los objetivos son metas, no resultados actuales. Para un modelo de 10–100M parámetros, no conviene volcar terabytes sin muestreo, calidad y mezcla controlada.

## 3. Orden de adquisición / desbloqueo

### P0 — Convertir candidatos ya materializados en train real

1. **ScienceVerse:** 7.365 documentos / 446.092.799 bytes admitidos scoped. Resolver deduplicación near-duplicate contra todos los corpus y holdouts, inspección de muestras por colección, particiones deterministas y validación de atribución. Mantener los 38 retenidos fuera.
2. **NASA NTRS:** conservar los 813 admitidos scoped y los 11 retenidos; revalidar derechos de redistribución por documento. Los dos file-reviewed no se cuentan otra vez. Excluir imágenes, artículos de terceros y cualquier copyright no despejado.
3. **Papers propios:** incorporar los nueve Markdown con SHA-256, deduplicación, revisión de calidad/PII y splits.
4. **CoVoST 2:** usar únicamente el campo translation de los tres TSV fijados con CC0. Reconciliar el run de 432.475 filas con el snapshot anterior; excluir audio, source sentences, speaker IDs, rutas y metadatos no necesarios.
5. **PleIAs Common Corpus:** revisar los 2.159 registros, aceptar únicamente los 2.149 CC0 y los 10 CC BY bajo atribución y términos compatibles, con revisión humana y PII; no usar filas excluidas ni patrones sospechosos.

### P1 — Fuentes abiertas con texto completo y escala

| Fuente | Potencial | Decisión de adquisición |
|---|---|---|
| **Common Pile v0.1** | Colección publicada de 8 TB y más de 30 fuentes: investigación, código, libros, educación, transcripciones y gobierno | Prioridad máxima como mapa de fuentes. No descargar/admitir el agregado entero a ciegas: desglosar las 30 fuentes, fijar licencia/versión por componente y usar solo componentes con derechos verificables |
| **BNE / BDH — documentos en dominio público** | Distribuciones TXT/XML de obras históricas y literarias | Ejecutar y auditar el workflow existente. Validar obra, autor, traductor, edición y jurisdicción; el catálogo no sustituye el estado de derechos de cada obra |
| **PMC Open Access Subset** | Miles de artículos científicos con acceso programático | Descargar solo subconjuntos OA y versiones con licencia que permita reutilización para el uso previsto (CC0/CC BY y equivalentes aprobados). PMC completo no es open access; excluir artículos con copyright tradicional |
| **NIST Technical Series / Public Data Repository** | Informes y publicaciones de ciencia, metrología, informática e ingeniería | Selección por registro y documento. Retirar material de terceros y conservar atribución; no asumir que todo lo alojado es reutilizable |
| **USGS Publications Warehouse** | Geología, geografía, hidrología, riesgos naturales y ciencias de la Tierra | Priorizar informes producidos por USGS; excluir figuras/fotos/material de terceros no aclarado |
| **NOAA Institutional Repository** | Clima, meteorología, océanos y ciencias ambientales | Selección por copyright: el repositorio incluye tanto obras gubernamentales reutilizables como artículos cuyos titulares conservan derechos |
| **OpenWebMath / FineMath** | Corpus matemáticos de gran escala | Candidato de alto valor; auditar licencia del dataset, condiciones de Common Crawl y derechos subyacentes. No confundir ODC-By del conjunto con licencia individual de cada página |
| **Mathlib4** | Código y documentación formal de matemáticas | Ya hay 8.498 train en mathlib4-v1. Ampliar solo desde revisión inmutable Apache-2.0, evitando duplicar lo existente |
| **UN Parallel Corpus v1.0** | Traducciones multilingües institucionales | Workflow de ingestión existente; confirmar licencia declarada para la versión exacta, hashes, calidad, privacidad y splits |
| **Repositorios de datos públicos de la UE / España** | Derecho, administración, economía y ciencias sociales | Solo documentos cuya licencia cubra expresamente el texto y permita el uso previsto; no inferir permiso por ser información pública |

### P2 — Grandes corpus web

FineWeb / FineWeb-Edu tienen decenas de billones de tokens y ODC-By 1.0 para la colección, pero proceden de Common Crawl. No deben incorporarse como si cada página web fuera de dominio público. Solo considerar muestras si el uso previsto supera revisión jurídica y de términos, se conserva atribución/procedencia y se puede filtrar contenido de terceros. No priorizar RedPajama ni Common Crawl sin una política de derechos más fuerte.

## 4. Mezcla de 32 dominios × General/HKD

Mantener las 64 bibliotecas objetivo y no promover bibliotecas vacías artificialmente. Los dominios con prioridad inicial son:

- Ciencias formales: matemáticas, lógica, estadística.
- STEM: física, química, biología, astronomía, geología, clima, oceanografía.
- Computación: informática, ingeniería del software, datos y ciberseguridad.
- Ingeniería: eléctrica, mecánica, civil y robótica.
- Sociedad: derecho, economía, ciencias sociales, psicología y ciencia política.
- Humanidades: historia, filosofía, lingüística, literatura, educación, geografía y arte.

General conserva cobertura amplia. HKD se construye por densidad de conocimiento medida con criterios reproducibles, no por duplicar los mejores documentos. Ambas particiones deben ser globalmente disjuntas.

## 5. Gates obligatorios

Un documento solo puede entrar en train cuando consten todos estos puntos:

1. Payload y versión exactos, URL de origen y revisión inmutable.
2. Licencia del texto/documento, no solo de metadatos o del portal.
3. Derechos compatibles con el uso de entrenamiento previsto y atribución.
4. SHA-256 del payload y del texto normalizado.
5. Extracción reproducible y calidad mínima; OCR ruidoso a cuarentena.
6. Filtros de PII, datos sensibles, secretos, malware y contenido de terceros.
7. Deduplicación exacta y near-duplicate contra todos los corpus y splits externos.
8. Revisión humana documentada por fuente y muestreo por colección.
9. Splits deterministas train/validation/test; test y holdout nunca entrenan.
10. Manifiesto validado y asignación única a dominio/General/HKD.

Estados explícitos: `discovered`, `downloaded_candidate`, `rights_verified`, `text_extracted`, `quality_privacy_passed`, `deduplicated`, `split_validated`, `training_eligible`. Ningún paso automático debe saltarse estados.

## 6. Métricas obligatorias en cada ejecución

Publicar en JSON y resumen Markdown:

- documentos únicos por fuente, dominio y estado;
- bytes comprimidos descargados y bytes de texto normalizado;
- bytes y documentos realmente habilitados en train;
- porcentaje retenido y motivo;
- duplicados exactos y near-duplicates;
- idiomas, longitud, calidad y ruido OCR;
- distribución General/HKD y balance por dominio;
- SHA-256 de fuentes, manifiestos y artefactos;
- comparación neta con la ejecución anterior.

No reportar un único “total corpus” si mezcla candidatos, validation/test o snapshots solapados.

## 7. Implementación inmediata

1. Mantener payloads grandes como artefactos versionados de Actions; Git guarda manifiestos, índices, hashes y auditorías.
2. Ejecutar primero los workflows existentes de BNE/BDH, UN Parallel, ScienceVerse, NASA, CoVoST y PleIAs; no duplicar adquisiciones.
3. Crear un workflow de expansión por fuente con caché, reanudación, límites de tamaño, hashes y artefactos por lote.
4. Priorizar desbloquear ScienceVerse y los corpus existentes antes de descargar terabytes nuevos.
5. No iniciar un entrenamiento grande hasta que el incremento train neto esté validado y se haya fijado una mezcla reproducible.

## Referencias externas

- Common Pile v0.1, 8 TB y fuentes/licencias por componente: https://huggingface.co/common-pile y https://proceedings.neurips.cc/paper_files/paper/2025/hash/52acc050138d6f40dad6f12f91a4ce22-Abstract-Datasets_and_Benchmarks_Track.html
- PMC: el subconjunto Open Access es la excepción para descarga programática; no todo PMC es Open Access: https://support.nlm.nih.gov/knowledgebase/article/KA-03253/en-us y https://support.nlm.nih.gov/knowledgebase/article/KA-03584/en-us
- NASA NTRS: más de 200.000 documentos full text; el catálogo ofrece acceso público, no una licencia universal para cada documento: https://data.nasa.gov/dataset/nasa-technical-reports-server-ntrs
- NOAA copyright y repositorio: https://repository.library.noaa.gov/Content%20and%20Copyright
- FineWeb: ODC-By 1.0 y condiciones Common Crawl; revisar derechos de páginas subyacentes: https://huggingface.co/datasets/HuggingFaceFW/fineweb
- Project Gutenberg: comprobar copyright territorial y condiciones por ebook, especialmente fuera de EE. UU.: https://www.gutenberg.org/policy/terms_of_use.html
- mathlib4: licencia Apache-2.0: https://github.com/leanprover-community/mathlib4
- OpenStax: CC BY-NC-SA; no incluir en corpus con uso comercial previsto sin permiso adicional: https://help.openstax.org/s/article/Licensing-information-of-OpenStax-textbooks
