# ScienceVerse / papers — expansión de candidatos de texto científico

**Estado a 5 de noviembre de 2026:** cinco de los siete corpus prioritarios ya tienen su asset RDS completo en candidates/scienceverse-fulltext/. Son **3.091 filas DOI elegibles** y **95.948.088 bytes de RDS**. Continúan como candidatos: el RDS no es texto plano, no se ha ejecutado todavía una exportación textual ni se ha completado el gate jurídico Level A, calidad, privacidad, deduplicación o particionado. No son bytes de texto admitido.

## Fuente y revisión fijada

- Repositorio: https://github.com/scienceverse/papers
- Revisión exacta del manifiesto upstream: 3a6ac0125e576423300a8996e9ad4c5d65ef9fe2.
- Cada carpeta descargada conserva manifest.csv, eligible-manifest.csv, provenance.json y el asset RDS.
- El manifiesto upstream declara CC BY 4.0 por artículo en estos cuatro corpus. Esa declaración por DOI es evidencia de candidato; no demuestra por sí sola titularidad, derechos sobre elementos de terceros ni el cumplimiento completo de Level A.

## Cobertura del catálogo prioritario

| Corpus | Artículos en catálogo | Estado RONIN | Dominio provisional |
|---|---:|---|---|
| BMC Medicine (bmcmed) | 1.000 | Descargado: 1.000 elegibles | medicine_health_general |
| eLife (elife) | 1.000 | Catálogo; payload pendiente | biología / medicina |
| Frontiers in Psychology (frontiers) | 1.000 | Catálogo; payload pendiente | ciencias sociales |
| i-Perception (iperc) | 496 | Descargado: 496 elegibles | social_sciences_general |
| Judgment and Decision Making (jdm) | 855 | Descargado: 855 elegibles | social_sciences_general |
| Journal of Cognition (joc) | 447 elegibles de 448 filas | Descargado; 1 fila excluida por conversión incompleta | social_sciences_general |
| Open Mind (openmind) | 293 | Descargado: 293 elegibles | philosophy_general |
| **Total** | **5.091** | **3.091 elegibles descargados; 2.000 aún sin payload** | |

## Assets adquiridos y hashes verificados en el expediente

Los siguientes tamaños son del RDS comprimido, no del texto extraído.

| Corpus / release | Filas de manifiesto | Filas elegibles | Excluidas | Bytes RDS | SHA-256 del RDS |
|---|---:|---:|---:|---:|---|
| bmcmed-2026-06-19 | 1.000 | 1.000 | 0 | 30.450.200 | fe81c3c6688cb007ccdbbd082b22e74bdaa17ce2e9735ddc276e083108d8d000 |
| jdm-2026-06-21 | 855 | 855 | 0 | 24.875.707 | 3381725686b9b1bae2a2c764ea87fdf52b8575cf8d87902388abd333319d3aa6 |
| joc-2026-06-20 | 448 | 447 | 1 | 15.559.915 | 12766fe41d80dcffc1da26056c929c7e39fb56be772809fa1620887df8838ae5 |
| openmind-2026-06-21 | 293 | 293 | 0 | 12.639.050 | c27fd53e8e640f7ac4cb3cfe43d04bfdc8a80c050956df3ec8abc6931d796feb |
| i-Perception (iperc-2026-06-21) | 496 | 496 | 0 | 12.423.216 | SHA-256 en provenance.json |\n| **Total** | **3.092** | **3.091** | **1** | **95.948.088** | — |

Hashes SHA-256 de los manifiestos y manifiestos elegibles, junto con el tamaño y hash de cada RDS, están en el provenance.json de cada corpus. El commit de adquisición es https://github.com/orbitalronin94/RONIN-IA/commit/68497f153e06c18cd693c3ef77e229bfd3defbb8.

### Exclusión exacta de Journal of Cognition

El manifiesto contiene 448 filas; la fila 10.5334/joc.316 declara CC BY 4.0, pero xml_exists=FALSE e in_rds=FALSE. Se excluyó del manifiesto elegible por conversión ausente, no por una licencia incompatible. No se cuenta como documento descargado/elegible y no se fuerza su inclusión.

## Revisión de derechos: todavía no Level A

- El filtro conserva únicamente filas cuya licencia declarada es exactamente CC-BY 4.0.
- Se conserva el DOI, título, año, rutas PDF/XML y los indicadores de conversión del manifiesto por artículo.
- La procedencia fija el commit del manifiesto y el tag de release; se calculan hashes SHA-256 de payload, manifiesto original y manifiesto elegible.
- Falta comprobar la declaración de licencia del editor en cada artículo/versión, el titular/proveedor y su alcance, atribución completa y contenido de terceros incrustado.
- Crossref puede corroborar DOI/licencia; no sustituye la declaración del editor ni prueba titularidad.
- Se mantienen pendientes retractaciones/correcciones, privacidad de participantes, datos clínicos identificables, secretos, malware, calidad, extracción textual y revisión humana.

## Inspección RDS y siguientes gates

- Adquisición: .github/workflows/ingest-scienceverse-ccby.yml y scripts/ingest_scienceverse_ccby.py.
- Inspección: .github/workflows/inspect-scienceverse-rds.yml y scripts/inspect_scienceverse_rds.R. El inspector verifica los hashes y recuentos de los cuatro manifiestos y examina la estructura sin imprimir contenido textual.
- Runs de inspección fallidos: https://github.com/orbitalronin94/RONIN-IA/actions/runs/42001889049 (el recorrido recursivo excedió el límite de 5.000 nodos) y https://github.com/orbitalronin94/RONIN-IA/actions/runs/42001946701 (el paquete CRAN no pudo instalarse en la biblioteca R de solo lectura). Se acotó el muestreo estructural y se cambió a r-cran-jsonlite del sistema en los commits 1df303a y fd61d25; la nueva ejecución debe confirmar el arreglo.
- Después de inspeccionar la estructura: exportar texto y metadatos por DOI, validar hashes de texto, comparar DOI contra retractaciones/correcciones, hacer deduplicación exacta y near-duplicate global, revisar PII/secrets/malware, idioma/calidad, atribución y asignar splits agrupados por DOI.
- Solo entonces se podrá clasificar cada documento entre General/HKD mediante ranking RONIN reproducible. Los dominios de destino de la tabla son provisionales, no una asignación ya realizada.

**Estado final:** 2.595 documentos candidatos en cuatro assets RDS; 83.524.872 bytes comprimidos; 0 bytes de texto admitido Level A; 0 bibliotecas completadas por esta fuente; G-0 global continúa FAIL; training_eligible=false.
