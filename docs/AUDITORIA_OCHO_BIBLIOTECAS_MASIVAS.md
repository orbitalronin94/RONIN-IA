# Auditoría de fuentes y diseño de las ocho bibliotecas masivas

Actualizado: 4 de noviembre de 2026. Estado: auditoría documental; ninguna fuente nueva queda admitida por este documento.

## Decisión: Portfolio fuera del entrenamiento

Portfolio/Papers deja de formar parte de la mezcla base. No es una novena biblioteca ni una reserva de pesos. Se prepara como índice de recuperación documental (RAG), con fragmentos, metadatos, hashes y citas. RONIN consulta ese índice cuando su estimador de incertidumbre o el enrutador detecta que no puede resolver una pregunta con evidencia suficiente. La respuesta debe separar lo que recuerda el modelo de lo que recupera y citar el documento.

Solo se abrirá una propuesta de entrenamiento con Portfolio si una evaluación identifica una carencia persistente, la recuperación no basta y un experimento controlado demuestra mejora sin regresiones. Requiere aprobación explícita. No se mezcla por defecto.

## Umbral de escala

- Ocho bibliotecas exactas, separadas por dominio.
- Mínimo admitible: 256 MiB de train.txt normalizado y deduplicado por biblioteca.
- Objetivo inicial: 1 GiB por biblioteca.
- Equilibrio: el menor corpus debe representar al menos el 75% del mayor. Bytes son un gate de volumen, no una métrica de calidad.
- Cada biblioteca requiere revisión inmutable, SHA-256, procedencia y licencia por documento, filtros de PII/secretos, deduplicación y splits por documento.
- Holdouts, benchmarks, validation/test y documentos usados para calibrar REF no entran en gradientes.
- No RUN #5 hasta que las ocho pasen validate_eight_libraries.py --require-ready.

## Auditoría por fuente

| Biblioteca | Fuente | Escala publicada | Licencia/acceso | Veredicto |
|---|---|---:|---|---|
| Matemáticas | OpenWebMath | 14,7B tokens / 6,3M docs | ODC-By-1.0; Common Crawl ToU y derechos fuente | Prioridad condicional; inglés, revisar upstream y fijar snapshot. |
| Matemáticas | MathPile | 9,5B tokens | Hereda licencias de fuentes | No admitir entero; solo shards con derechos verificables. |
| Matemáticas/pruebas | ProofPile-2 | gran colección mixta | Licencias heredadas por fuente | No admitir entero; derivar subconjuntos trazables. |
| Lógica/epistemología | Lean mathlib4 | biblioteca extensa de pruebas formales | Apache-2.0 en repo; revisar dependencias | Prioridad condicional; muy útil para estructura formal, no sustituye prosa explicativa. |
| Lógica/epistemología | Common Corpus OpenScience/Semantic | parte de 2,27T tokens globales | Licencia por documento | Prioridad condicional; filtrar tema, idioma y licencia. |
| Filosofía | PleIAs Spanish Public Domain Books | 302.640 obras / 52,1 GB reportados | Dominio público por obra, edición, traducción y jurisdicción | Prioridad alta condicional; auditoría legal y OCR obligatorios. |
| Filosofía | Common Corpus OpenCulture | gran colección cultural | Licencia por documento | Prioridad condicional; filtrar obras y edición. |
| Física | arXiv | archivo científico masivo | Licencia por artículo | Prioridad condicional; no hay licencia global para todos los PDFs. |
| Física | Common Corpus OpenScience | colección científica extensa | Licencia por documento | Prioridad condicional; selección temática, idioma y licencia. |
| Química/materiales | PMC Open Access Subset | colección OA amplia | Licencia por artículo; CC0/CC-BY compatibles | Prioridad condicional; usar solo servicios oficiales OA. |
| Química/materiales | USPTO PatentsView | corpus grande de patentes | Registros oficiales; revisar contenido de terceros | Prioridad condicional; texto técnico, no manuales didácticos. |
| Biología/medicina | PMC OA Subset | gran colección de artículos | CC0/CC-BY por artículo | Prioridad alta condicional; nunca descargar todo PMC. |
| Biología/medicina | Europe PMC OA | colección OA amplia | Licencia por artículo | Prioridad alta condicional; deduplicar contra PMC. |
| Informática/software | The Stack v1 | multi-terabyte | SPDX por archivo, opt-out y atribución | Prioridad condicional; código separado, escaneo de secretos/malware. |
| Informática/software | The Stack v2 | 67,5 TB full / 32,1 TB deduplicados | Licencia original por archivo; resolución SWHID | Escala alta, coste alto; seleccionar shards reproducibles. |
| Derecho/economía/social | Common Corpus OpenGovernment | 579B tokens reportados | Licencia por documento | Prioridad alta condicional; filtrar español, subdominio, PII y vigencia. |
| Derecho | Harvard Caselaw Access Project | colección histórica extensa | Verificar términos exactos del release | Condicional; solo derecho estadounidense. |
| Ciencias sociales | Europarl | corpus parlamentario multilingüe | Verificar términos y versión | Condicional; útil para lenguaje institucional. |

## Hallazgos que cambian decisiones

1. Common Corpus declara 2,27T tokens, trazabilidad documental y seis colecciones: OpenCulture, OpenGovernment, OpenSource, OpenScience, OpenWeb y OpenSemantic. Es el candidato transversal más prometedor, pero no se admite entero: seleccionar por dominio, idioma y licencia exacta.
2. OpenWebMath declara 14,7B tokens y 6,3M documentos; ODC-By-1.0 y términos de Common Crawl. Es el candidato matemático masivo más directo localizado, pero es inglés.
3. MathPile declara 9,5B tokens, pero no sustituye las licencias de las fuentes subyacentes. No usar el paquete entero sin filtrado.
4. NLM indica que no se debe descargar masivamente todo PMC; el acceso programático se limita al Open Access Subset, con licencia por artículo.
5. The Stack v2 informa 67,5 TB full y 32,1 TB deduplicados; la tabla de entrenamiento usa SWHIDs y requiere resolver blobs. Seleccionar shards por lenguaje/licencia, no descargarlo completo en Actions.
6. FineWeb2 declara ODC-By-1.0 y escala masiva, pero es web general de Common Crawl; no equivale a una biblioteca disciplinar y exige filtros de procedencia y calidad.
7. OpenAlex CC0 cubre metadatos, no los artículos enlazados. Úsese para descubrimiento, nunca como licencia de full text.

## Escala sin destruir el presupuesto de Actions

- Descargar en shards con manifiesto inmutable; no reconstruir ni tokenizar el corpus en cada run.
- Mantener raw fuera de Git; publicar solo manifiestos, hashes, estadísticas y muestras autorizadas.
- Construir índice local por dominio, licencia, idioma, longitud y hash; filtrar antes de descargar cuerpos cuando sea posible.
- Deduplicar exacto por SHA-256 normalizado y casi duplicado con MinHash/SimHash entre bibliotecas.
- Medir bytes UTF-8 y tokens reales; tamaño Parquet comprimido no equivale a texto de entrenamiento.
- Declarar composición idiomática. No forzar español si destruye cobertura científica; usar subcorpus inglés técnico explícito.
- Para entrenar, muestrear por dominio y presupuesto de tokens/pasos; no recorrer por defecto varias épocas de corpus multi-GB en CPU.

## Portfolio como recuperación, no como peso

El índice RAG debe guardar document_id, source_path, title, sha256, chunk_id, offsets y permiso de uso. En inferencia: detectar incertidumbre, recuperar top-k, verificar pertinencia, citar y abstenerse si no hay evidencia. No incorporar el texto recuperado a pesos ni gradientes. Registrar consultas y documentos recuperados sin exponer material sensible.

## Estado del gate

El manifiesto data/manifests/eight_libraries.json registra ocho áreas y sus fuentes candidatas. Todas permanecen candidate, training_eligible=false y train_bytes=0. El gate --require-ready debe fallar: una ficha de dataset no demuestra que la biblioteca esté descargada, licenciada y lista.


## Segunda tanda: ocho bibliotecas extraídas por densidad de conocimiento

La petición evoluciona el objetivo de ocho a **dieciséis bibliotecas**: las ocho bases de la tabla anterior más ocho bibliotecas HKD, una por dominio, extraídas de las fuentes masivas con alta concentración de conocimiento. Las segundas no se admiten por el mero hecho de ejecutar el selector.

Fuentes candidatas adicionales y adaptadores:
- Matemáticas: OpenWebMath; MathPile solo shards con licencia heredada trazable.
- Lógica/epistemología: ProofPile-2 solo por fuente; Lean mathlib4 con Apache-2.0 y dependencias auditadas.
- Filosofía: PleIAs Spanish-PD-Books y Common Corpus OpenCulture, obra/edición/licencia verificadas.
- Física: arXiv por artículo y Common Corpus OpenScience.
- Química: PMC OA y PatentsView.
- Biología/medicina: PMC OA y Europe PMC OA.
- Informática: The Stack v2 por archivo SPDX/SWHID y Common Corpus OpenSource.
- Derecho/economía/social: Common Corpus OpenGovernment y Harvard Caselaw Access Project.

El inventario ejecutable está en data/manifests/knowledge_dense_sources.json. Todos los adaptadores empiezan desactivados; cada uno requiere revisión de campos reales, revisión inmutable y allowlist legal antes de habilitarlo. Los paquetes de licencia heterogénea no se admiten enteros.

La métrica RONIN-HKD-0.1 y su protocolo están en docs/METRICA_DENSIDAD_SEMANTICA.md. El selector usa SQLite temporal en disco, IDF de corpus, deduplicación normalizada y puntuación por dominio. No usa tutores ni credenciales. El constructor produce ocho salidas `<dominio>_hkd/train.txt` y reportes hashados. Las ocho deben superar revisión humana, calidad, licencias, 256 MiB train y balance antes de contar como admitidas.

## Gate de dieciséis bibliotecas

El manifiesto oficial pasa a data/manifests/sixteen_libraries.json. El workflow oficial exige scripts/validate_sixteen_libraries.py y 16 ficheros train con hashes exactos. Portfolio/Papers sigue exclusivamente como RAG experto, fuera de las 16 y de los gradientes. No se autoriza RUN #5 ni merge de la PR hasta que las 16 bibliotecas reales pasen el gate.
