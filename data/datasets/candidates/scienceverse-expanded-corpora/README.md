# ScienceVerse / papers — expansión de candidatos de texto científico

**Estado: repositorio y estructura de procedencia verificados; subconjuntos CC BY 4.0 identificados; payloads nuevos aún no descargados ni admitidos.**

## Por qué merece prioridad

El repositorio original mantiene 18 corpus de artículos científicos en acceso abierto, con 15.179 artículos declarados a 21-06-2026. Cada corpus incluye README, manifiesto CSV por artículo (DOI, título, año, nombres de archivo y procedencia), metadatos Dublin Core y script reproducible. Los artículos conservan sus licencias originales. La colección incluye PDFs y objetos paperlist con texto extraído; el propio proyecto permite incorporar formatos de texto plano/JSON.

Fuente: https://github.com/scienceverse/papers

## Subconjuntos prioritarios declarados CC BY 4.0

| Corpus | Revista | Artículos en catálogo | Dominio RONIN provisional |
|---|---|---:|---|
| bmcmed | BMC Medicine | 1.000 | Medicina y salud |
| elife | eLife | 1.000 | Biología / medicina |
| frontiers | Frontiers in Psychology | 1.000 | Ciencias sociales |
| iperc | i-Perception | 496 | Ciencias sociales / percepción |
| jdm | Judgment and Decision Making | 855 | Ciencias sociales / economía conductual |
| joc | Journal of Cognition | 447 | Ciencias sociales / cognición |
| openmind | Open Mind | 293 | Filosofía / ciencias cognitivas |

**Total de catálogo prioritario: 5.091 artículos.** Esta cifra es el tamaño declarado de los corpus, no el número de artículos ya descargados ni una cifra de admisión.

## Condiciones para seleccionar documentos

1. Descargar el manifiesto y fijar la revisión exacta del repositorio y el asset de release.
2. Comprobar para cada DOI la licencia original y excluir cualquier excepción que no sea CC BY 4.0 o CC0 compatible.
3. No asumir que la licencia del repositorio cubre artículos individuales: se conserva la licencia original por artículo.
4. Verificar correspondencia entre DOI, PDF y texto extraído; guardar SHA-256 de ambos.
5. Retirar o revisar PII, datos personales de participantes, correos, afiliaciones sensibles y contenido clínico identificable.
6. Deduplicar frente a Collabra ya procesado y frente a las 32 bibliotecas y los conjuntos de evaluación.
7. Clasificar por tema y densidad; General/HKD se reparte por bytes y sin duplicación.
8. Mantener referencias, figuras y tablas solo cuando su reutilización y extracción estén justificadas; no incorporar material de terceros incrustado sin derechos claros.

## Exclusiones inmediatas

No se aceptan en bloque:
- bmcoral, ijos, natcomm: catálogo declara "Mostly CC BY 4.0".
- ece3 y scan: licencias mixtas, incluyendo variantes NC.
- jssm: CC BY 4.0 o CC BY-NC-ND 4.0.
- psychsci_oa: CC BY 4.0 o CC BY-NC.
- plosbio, plosmed y plosone: mezcla CC BY 4.0/CC0; requiere filtro DOI.
- cualquier PDF/figura con derechos de terceros o sin licencia verificable.

## Decisión RONIN

- Fuente de descubrimiento y estructura de procedencia: **verificada**.
- Licencias declaradas de los siete corpus prioritarios: **CC BY 4.0 según el catálogo upstream**.
- Derechos individuales por DOI: pendientes de extracción y comprobación.
- Payload, hashes, privacidad, calidad, deduplicación y splits: pendientes.
- **Estado final: candidato de alta prioridad; no Grado A, no entrenable todavía.**

Fuente de catálogo y licencia: README upstream, tabla "Available corpora", que identifica 18 colecciones, 15.179 artículos y licencia por corpus: https://github.com/scienceverse/papers

## Adquisición real preparada en RONIN (2026-11-05)

Se ha añadido un proceso de adquisición directa a `main`:

- Workflow: `.github/workflows/ingest-scienceverse-ccby.yml`.
- Script: `scripts/ingest_scienceverse_ccby.py`.
- Cuatro releases de paperlists completos fijados por tag:
  - BMC Medicine: 1.000 artículos → `medicine_health_general`.
  - Judgment and Decision Making: 855 → `social_sciences_general`.
  - Journal of Cognition: 447 → `social_sciences_general`.
  - Open Mind: 293 → `philosophy_general`.
- Total de manifiestos esperados: **2.595 artículos**.
- El script descarga el manifiesto DOI por DOI y rechaza el corpus completo si una sola fila no declara exactamente CC-BY 4.0. Descarga además el asset RDS de texto completo, calcula SHA-256 y escribe procedencia.
- Si pasa la auditoría, el workflow incorpora los RDS, manifiestos y registros de procedencia directamente en `data/datasets/admitted/scienceverse/` y hace commit en `main`.

**No confundir el número esperado con la admisión completada:** el commit de código activa la adquisición; los archivos solo se contabilizarán cuando el workflow haya terminado correctamente y se verifiquen los RDS, manifiestos y hashes. Antes de entrenar hay que ejecutar deduplicación global, control de retractaciones/correcciones, privacidad y particionado por DOI.

Fuente primaria: https://github.com/scienceverse/papers (manifiestos y releases upstream).
