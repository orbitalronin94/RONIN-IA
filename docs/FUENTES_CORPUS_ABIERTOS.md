# Fuentes abiertas de corpus para RONIN IA

Actualizado: 2026-11-04.

## Alcance de la auditoría G-0

El informe `reports/license_audit.json` y su gate G-0 se refieren a cuatro colecciones candidatas concretas: Project Gutenberg, Internet Archive, Common Corpus y BookCorpusOpen. Su estado FAIL bloquea esas colecciones, no constituye una autorización general ni un bloqueo automático de las tres fuentes literarias ya integradas (CLiGS Textbox, CoNSSA y ELTeC-spa). Estas últimas tienen revisiones, licencias declaradas, manifiestos y validación específica por documento; el workflow de entrenamiento las admite mediante una lista cerrada de repositorios y commits. Cualquier fuente nueva necesita su propia revisión antes de entrar.

## Regla de admisión

Una fuente solo puede pasar a entrenamiento si cumple simultáneamente:

1. Descarga pública directa por HTTPS o repositorio público, sin cuenta, inicio de sesión, token, clave API ni secreto.
2. Licencia explícita y compatible con el uso previsto. El dominio público debe estar respaldado por procedencia y fechas de fallecimiento/publicación; no basta con que una web sea pública.
3. Versión fijable (commit, DOI o versión) y huellas SHA-256 del material descargado.
4. Posibilidad de identificar la procedencia por documento y excluir duplicados, datos personales, credenciales y material con derechos no verificados.
5. Separación por documento entre entrenamiento, validación y prueba.

No se admiten licencias NC o ND. Una licencia de metadatos no se confunde con la licencia del texto subyacente.

## Fuentes seleccionadas para la primera integración

| Fuente | Contenido | Licencia declarada | Acceso | Estado |
|---|---|---|---|---|
| [CLiGS Textbox](https://github.com/cligs/textbox) | 39 novelas españolas, 24 hispanoamericanas y 302 cuentos individuales agrupados en 20 colecciones TEI | Textos de dominio público; marcado/metadatos CC BY 4.0 | HTTPS público por archivo | Integrada; 364 documentos preparados |
| [CoNSSA](https://github.com/cligs/conssa) | 217 novelas disponibles de la Edad de Plata española (1880–1939); el corpus total declara 358, pero parte no puede publicarse por derechos | Textos de dominio público; TEI/metadatos CC BY 4.0 | HTTPS público por archivo | Integrada; 184 documentos preparados |
| [ELTeC-spa](https://github.com/COST-ELTeC/ELTeC-spa) | 83 novelas españolas en la versión 0.9.1 | Textos de dominio público; marcado CC BY 4.0 | HTTPS público por archivo | Integrada; 96 documentos preparados |

Los repositorios se fijan a commits concretos en `scripts/prepare_open_corpora.py`. CLiGS Textbox incluye también `spanish/cuentos-espanoles/tei/`, además de las colecciones de novelas. El preparador consulta el árbol Git de cada commit fijado y descarga únicamente los XML TEI seleccionados desde `raw.githubusercontent.com`, sin enviar credenciales ni bajar ZIP completos. Verifica el tamaño y el SHA-1 de objeto Git de cada archivo, calcula SHA-256, extrae el elemento TEI `text` y separa cada `div type="short-story"` como relato individual. Deduplica por contenido y asigna todos los fragmentos de un mismo archivo de origen a una sola partición para evitar fugas entre train, validation y test. El manifiesto JSONL conserva la procedencia, el hash del archivo original, la licencia y la partición de cada obra. La primera referencia es literaria e histórica; no debe presentarse como corpus general o representativo del español actual.

## Resultado de adquisición reproducible

La auditoría de GitHub Actions del 4 de noviembre de 2026 descargó y verificó
las tres fuentes fijadas, sin credenciales y sin descargar archivos ZIP completos.
Resultado medido:

- **644 documentos preparados**: 364 de CLiGS Textbox, 184 de CoNSSA y 96 de
  ELTeC-spa.
- **608 train, 18 validation y 18 test**; las obras y colecciones se mantienen
  agrupadas para impedir fugas entre particiones.
- 40 archivos o fragmentos se excluyeron por los filtros de calidad, duplicación
  o seguridad.
- Los archivos originales se verifican por tamaño, SHA-1 de objeto Git y
  SHA-256; el manifiesto conserva procedencia, licencia, revisión y partición.

Ejecución verificable:
- [Auditoría completa de descargas (run 41801074425)](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41801074425)
- [Artefactos de adquisición y manifiestos](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41801074425/artifacts)

Los originales y particiones se conservan como artefactos temporales de Actions,
no en Git. El corpus sigue siendo una biblioteca literaria histórica; no es una
muestra representativa del español actual.

## Candidatas para siguientes iteraciones

| Fuente | Tamaño / contenido publicado | Licencia y acceso | Decisión |
|---|---|---|---|
| [Spanish Public Domain Books — PleIAs](https://huggingface.co/datasets/PleIAs/Spanish-PD-Books) | 302.640 obras, 13.900 millones de palabras; 52,1 GB publicados | La ficha declara dominio público en todas las regiones; repositorio público | Prioridad alta, pero descarga por fragmentos y comprobación de derechos/OCR antes de integrarlo |
| [Spanish Public Domain Newspapers — PleIAs](https://huggingface.co/datasets/PleIAs/Spanish-PD-Newspapers) | Prensa histórica española | Dominio público según el proyecto; repositorio público | Prioridad media; verificar fechas, derechos de cada cabecera y calidad OCR |
| [Biblioteca Digital Hispánica — BNE, obras en dominio público](https://datos.gob.es/es/catalogo/ea0019768-biblioteca-digital-documentos-en-dominio-publico1) | Metadatos y enlaces a digitalización/OCR de obras en dominio público | BNE declara reutilización CC BY | Prioridad alta; descargar solo registros y OCR de la colección en dominio público |
| [Corpus Adela Zamudio](https://labtecnosocial.org/adela-zamudio/datos/) | 70 textos, 88.069 palabras | Obras en dominio público; transcripción y metadatos CC BY 4.0 | Candidata pequeña; verificar URL de descarga y SHA antes de incorporar |
| [Estilometría — obras en español](https://github.com/Jero2760/estilometria) | 345 comedias, 22 entremeses y 42 novelas | Repositorio CC BY; afirma usar textos de dominio público | Prioridad media; auditar cada fuente original y deduplicar con CLiGS/CoNSSA |
| [Maria Silvia v1](https://huggingface.co/datasets/gia-uh/maria-silvia-v1) | Conversaciones/instrucciones sobre cultura cubana, con train/validation/test | CC0-1.0 | Candidata para una fase posterior de ajuste instructivo, no para mezclar sin más con el preentrenamiento |
| [Common Voice 17 — español (espejo público)](https://huggingface.co/datasets/Thermostatic/CommonVoice-17.0-Spanish) | 2.008.575 filas; 65,9 GB, texto y audio | CC0-1.0 según el espejo | Solo transcripciones; demasiado grande para la primera iteración CPU y requiere auditoría del espejo |
| [BNE — Biblioteca Digital, set completo](https://datos.gob.es/es/catalogo/ea0019768-biblioteca-digital-set-completo1) | Metadatos de la colección completa y enlaces a OCR | CC BY 4.0 | No incorporar indiscriminadamente: usar únicamente obras con derechos comprobados |
| [BOE — API de datos abiertos](https://www.boe.es/datosabiertos/api/api.php?lang=es) | Legislación consolidada y sumarios | Reutilización sujeta a condiciones publicadas; acceso sin clave API | Candidata para corpus jurídico; revisar condiciones y automatización antes de usar |
| [Congreso de los Diputados — datos abiertos](https://www.congreso.es/es/datos-abiertos) | Datos XML, JSON y CSV sobre actividad parlamentaria | La página anuncia descarga abierta; licencia de reutilización por verificar | No integrar hasta aclarar derechos de intervenciones y condiciones |
| [Corpus español de Wikipedia — Zenodo/ELG](https://live.european-language-grid.eu/catalogue/corpus/7694) | 378,5 MB de texto | Distribución declarada CC BY 4.0; origen Wikipedia | En espera: aclarar compatibilidad entre licencia declarada y licencia de las páginas fuente |
| [HPLT español v3](https://hplt-project.org/datasets/v3.0) | 1,20 TB, 725,58 millones de documentos y 658.970 millones de tokens declarados | La ficha declara CC0; origen Common Crawl/Internet Archive | No usar en la iteración CPU; enorme y requiere auditoría de procedencia por documento |
| [DReaM-es-open](https://spraakbanken.gu.se/en/resources/dream-es-open) | 9,1 millones de tokens declarados | CC BY 4.0 | Acceso al corpus vía Korp; la descarga pública enlazada es solo estadísticas. No usar hasta localizar exportación textual directa |

## Fuentes descartadas o en cuarentena

- Mozilla Data Collective: descartada porque exige aceptar condiciones con cuenta y usar API key.
- esCorpius: CC BY-NC-ND 4.0; incompatible con los criterios.
- CEDEL2: CC BY-NC-ND 3.0; incompatible.
- CEREAL/OSCAR: la licencia CC BY cubre anotaciones, pero los autores indican que no poseen los derechos del texto procedente de OSCAR/Common Crawl; no se integra sin resolver los derechos subyacentes.
- Spanish Biomedical Crawled Corpus: solo se publica una muestra pequeña y la ficha consultada no identifica licencia; no se usa.
- Tatoeba: mezcla aportaciones CC BY 2.0 y CC0; la opción CC0 requiere permiso adicional y no cubre traducciones. No descargar el conjunto completo para entrenamiento.
- Corpus con login, registro o acceso restringido (por ejemplo AnCora): descartados, aunque sean gratuitos para investigación.
- Large Spanish Corpus, Spanish Billion Words, corpus clínicos y jurídicos de licencia no verificada: en cuarentena hasta que cada ficha y fichero indique claramente licencia y acceso.

## Protocolo de incorporación

1. Registrar ficha, licencia, jurisdicción, procedencia y método de descarga.
2. Comprobar descarga anónima desde un runner limpio, sin secretos ni cookies.
3. Fijar versión y SHA-256 del archivo original.
4. Ejecutar escaneo de credenciales, datos personales, formato, idioma, duplicados y derechos por documento.
5. Generar manifiesto y particiones por documento; nunca dividir frases del mismo documento entre train y test.
6. Publicar solo métricas y manifiestos. No subir corpus, checkpoints ni textos de terceros al repositorio.

## Referencias

- CLiGS Textbox: https://github.com/cligs/textbox
- CoNSSA: https://github.com/cligs/conssa
- ELTeC-spa: https://github.com/COST-ELTeC/ELTeC-spa
- SomosNLP, catálogo de corpus: https://somosnlp.org/recursos/datasets
- Instituto de Lingüística Aplicada de la UCA: https://ila.uca.es/corpus-en-espanol/
