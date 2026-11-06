# Corpus paralelo de las Naciones Unidas v1.0 — preadmisión

**Estado RONIN: fuente y alcance de derechos verificados; payload pendiente de ingestión. No es todavía Grado A ni entrenable.**

## Fuente primaria y alcance

- Proveedor: Departamento de la Asamblea General y de Gestión de Conferencias de Naciones Unidas (DGACM).
- Versión: UN Parallel Corpus v1.0.
- Periodo documental: 1990–2014.
- Idiomas: árabe, chino, inglés, francés, ruso y español.
- Contenido: registros oficiales y otros documentos parlamentarios de Naciones Unidas, redactados y traducidos manualmente, con alineación por frases.
- Declaración del proveedor: los documentos del corpus son documentos oficiales y parlamentarios de Naciones Unidas que están en dominio público.
- Descarga oficial: https://www.un.org/dgacm/en/content/uncorpus/download
- Descripción oficial en español: https://www.un.org/dgacm/es/content/uncorpus/es
- Artículo técnico y nota legal: https://www.un.org/dgacm/sites/www.un.org.dgacm/files/files/UNCORPUS/un.pdf

La documentación del proveedor declara expresamente el dominio público del material y adjunta un descargo de responsabilidad que debe conservarse. Esta verificación se limita a la colección UN v1.0 y no se extiende a documentos de terceros que pudieran aparecer fuera de ella.

## Descargas y exclusiones

El proveedor publica:
- archivos TEI/XML por idioma, año y símbolo documental;
- bitextos en texto plano por pares de idiomas;
- un subconjunto alineado en los seis idiomas;
- conjuntos oficiales de desarrollo y prueba separados, basados en documentos de 2015.

**RONIN excluye íntegramente los conjuntos oficiales de test/dev de 2015 del entrenamiento.** Se conservarán separados como material de evaluación únicamente si se decide utilizarlos y se registra esa decisión; nunca se mezclarán con train.

Los archivos se distribuyen en fragmentos de hasta 1 GB. La ingestión debe descargar todos los fragmentos del paquete elegido, comprobar tamaño y SHA-256, reconstruir el archivo y validar el contenido antes de extraer textos.

## Decisión de integración

- Derechos de la colección: **verificados en la fuente oficial** para UN Parallel Corpus v1.0.
- Descarga del payload: pendiente.
- Hashes de archivo y de texto normalizado: pendientes.
- Parser TEI/bitext y validación de alineaciones: pendientes.
- Filtrado de PII, ruido y duplicados: pendiente.
- Clasificación temática: pendiente; no asignar automáticamente todo el corpus a Derecho o Ciencias Sociales.
- Revisión humana de muestras: pendiente.
- Particiones internas deterministas: pendientes.

**Destino provisional:** pool transversal de candidatos multilingües. Tras la clasificación documental, los textos pertinentes podrán repartirse entre las bibliotecas General/HKD por tema y densidad. Cada documento se asignará a una sola biblioteca y a una sola partición.

## Atribución

Citar: United Nations, Department for General Assembly and Conference Management, *United Nations Parallel Corpus v1.0*, documentos publicados entre 1990 y 2014. Conservar además el identificador documental, símbolo de publicación, idioma, año y ruta original del archivo.

## Fuentes consultadas

- https://www.un.org/dgacm/es/content/uncorpus/es
- https://www.un.org/dgacm/en/content/uncorpus/download
- https://www.un.org/dgacm/sites/www.un.org.dgacm/files/files/UNCORPUS/un.pdf

## Registro de auditoría

- Fecha de revisión: 2026-11-05.
- Resultado: **apto para iniciar ingestión técnica**, no admitido todavía.
- Motivo del bloqueo: falta inspección del payload descargado, hashes, calidad, privacidad, deduplicación y particionado.

## Ingestión reproducible en-es añadida a RONIN (2026-11-05)

Se ha incorporado directamente a `main`:

- Workflow: `.github/workflows/ingest-un-parallel-en-es.yml`.
- Validador: `scripts/prepare_un_parallel_candidate.py`.
- El workflow descarga las dos partes del bitexto inglés-español, reconstruye el archivo, comprueba gzip, extrae los tres componentes (inglés, español e identificadores), valida UTF-8 estricto y exige igualdad de líneas.
- Publica el payload y un manifiesto SHA-256 como artefacto `ronin-un-parallel-corpus-en-es-candidate` (retención 90 días).
- Los IDs de Google Drive proceden de un script público de descarga fijado a la revisión `e22994bdd64c668dc2360871b7e04c8e9d0a5224`; se usan únicamente como espejo de transporte. La fuente y la declaración de derechos siguen siendo las páginas oficiales de Naciones Unidas.

**Límite importante:** este primer paso genera un paquete candidato, no un corpus admitido. Igualar líneas no demuestra alineación semántica ni calidad. Siguen pendientes auditoría documental, privacidad, deduplicación con los 608 textos admitidos, clasificación temática General/HKD, revisión humana y particionado. Los conjuntos de desarrollo/prueba oficiales de 2015 no se descargan. No usar en entrenamiento hasta completar esos controles.



## Ingestión reproducible en-es añadida (6 de noviembre de 2026)

Se añade el harvester `scripts/ingest_un_parallel_en_es.py` y el workflow `.github/workflows/ingest-un-parallel-en-es.yml`. El workflow localiza los dos fragmentos del bitexto inglés-español desde la página oficial, reconstruye el archivo, comprueba que los tres flujos (inglés, español e identificadores) tengan el mismo número de líneas y genera particiones deterministas train/validation/test agrupadas por símbolo documental cuando el identificador lo permite.

- Solo procesa el corpus 1990–2014; no descarga ni mezcla el set oficial de 2015.
- Conserva IDs de origen, hashes, atribución ONU y evidencia de dominio público.
- Excluye pares vacíos/cortos, emails, URLs, caracteres de reemplazo y duplicados exactos.
- Publica los payloads gzip y el manifiesto como artefacto de Actions durante 90 días.
- El resultado sigue siendo candidato: no se habilita entrenamiento hasta revisión bilingüe, validación del agrupamiento documental, deduplicación global, privacidad y control de contaminación de holdouts.

El objetivo de esta ejecución es convertir una fuente de alto volumen (más de 120.000 alineaciones en-es según las estadísticas oficiales) en un lote auditable, no afirmar de antemano que todos sus segmentos son entrenables.
