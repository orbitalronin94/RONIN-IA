# NASA Technical Reports Server (NTRS) — filtro documental

**Estado verificado en `main` a 5 de noviembre de 2026: 824 textos completos descargados como candidatos; 39.262.382 bytes de texto UTF-8 (conteo directo de los blobs `documents/*.txt` y del manifiesto de procedencia). No admitidos para entrenamiento.**

## Valor potencial

NASA NTRS ofrece más de 500.000 citas y más de 200.000 documentos de texto completo en materias aeroespaciales y científico-técnicas. La colección pública se puede consultar sin credenciales; existe una colección registrada separada que no utilizaremos.

Fuentes:
- https://ntrs.nasa.gov/
- https://sti.nasa.gov/disclaimers/
- https://data.nasa.gov/dataset/nasa-technical-reports-server-ntrs

## Filtro de derechos

NASA declara que los trabajos preparados por empleados del Gobierno estadounidense en el ejercicio de sus funciones no están protegidos por copyright en EE. UU. Sin embargo, advierte que documentos públicos pueden contener partes privadas protegidas, que algunos documentos no son obras del Gobierno y que el estado de copyright debe comprobarse en los metadatos de cada documento.

Por tanto, solo pasan a candidato de ingestión los registros públicos cuyo campo de copyright/distribution indique de forma inequívoca **“Work of the US Gov. Public Use Permitted”** o una declaración equivalente documentada. Ejemplo oficial de registro con ese campo: https://ntrs.nasa.gov/search.jsp?R=20150013303

Excluir:
- documentos registrados/restringidos;
- copyright privado, desconocido o ambiguo;
- figuras, fotos, tablas o extractos de terceros sin permiso propio;
- documentos con distribución restringida;
- contenido que incluya datos personales o información sensible.

## Adquisición realizada

El workflow `.github/workflows/ingest-nasa-ntrs-public-use.yml` ha acumulado 824 documentos con texto completo. El manifiesto de procedencia registra 17.015 registros vistos, 1.112 elegibles por metadatos y 824 documentos conservados en el snapshot actual. El último inventario se calcula directamente desde los blobs del repositorio; los descartes y duplicados se mantienen trazados en los manifiestos de cada ejecución. No se presenta este recuento como documentos admitidos ni como total global sin deduplicación entre fuentes. Se conserva un `manifest.jsonl` por documento, `provenance.json`, SHA-256 de cada texto y el fichero en `documents/`.

El filtro aplicado exige `PUBLIC_USE_PERMITTED` o `GOV_PUBLIC_USE_PERMITTED`, `licenseType=NO`, ausencia declarada de material de terceros, distribución pública, `DOCUMENT_AND_METADATA`, estado `CURATED`, `sensitiveInformation=2` (NONE), EAR/ITAR en NO y texto completo disponible. Son candidatos de uso público según el registro NASA; aún requieren revisión humana de derechos, PII y calidad. NASA exige consultar las redistribuciones al menos semanalmente y retirar cualquier documento cuya disponibilidad cambie.

## Ingestión pendiente

Fijar cada NTRS Document ID y versión; conservar metadatos completos y campo copyright; descargar PDF público; calcular SHA-256; extraer texto; revisar referencias, figuras, PII, duplicados y calidad; mantener atribución NASA y datos de publicación.

**Resultado:** candidato de alta prioridad para Astronomía/Ciencias de la Tierra, Física, Química/Materiales e Ingeniería/Robótica. Se está generando un paquete por biblioteca en `data/datasets/libraries/candidate-packs/nasa-ntrs-public-use/`; los paquetes siguen siendo candidatos, no datos admitidos. La declaración general de NASA no basta para admitir un documento concreto; no entrenable hasta completar la revisión humana, la revalidación semanal de redistribución, la deduplicación global y los gates aplicables.


## Revisión manual de archivos concretos (2026-11-05)

Se ha registrado una revisión a nivel de archivo en `data/datasets/reviews/nasa-ntrs-file-review-2026-11-05.json`, enlazada también desde el manifiesto del paquete de bibliotecas.

- **Revisión de contenido superada como candidato (2):** NTRS `19620002819` (*Paraglider Recovery Systems*) y `19630000935` (*Development of Design Strength Levels for the Elastic Stability of Monocoque Cones Under Axial Compression*). Se contrastaron título, autoría, distribución/copyright con sus registros oficiales y se inspeccionó la legibilidad del texto extraído.
- **Retenidos para reparar OCR (2):** `19620000001` y `19620002834`. Sus registros NASA indican uso público, pero la extracción actual contiene suficientes sustituciones y corrupción de columnas como para no incorporarlos al entrenamiento todavía.
- La revisión también detectó tres incidencias de metadatos/ruta en ScienceVerse: fragmentos que parecen dirección postal en autores de `jdm.jdm06002`, autor malformado en `ece3.ece310954` y asignación temática dudosa de `openmind.opmia00001`. Están documentadas en el mismo informe y siguen retenidas.

**Verificación reproducible del paquete:** el artefacto de GitHub Actions `42015186814` se descargó y se inspeccionaron sus 824 filas descomprimidas: 824/824 SHA-256 y tamaños coinciden con cada texto; 824/824 cumplen la allowlist de metadatos de derechos; no hay duplicados exactos dentro del paquete NASA. Los recuentos por biblioteca son 147/119/430/128. La deduplicación global contra las demás fuentes sigue pendiente.\n\n**Importante:** los dos archivos NASA con revisión de contenido positiva siguen siendo candidatos, no documentos admitidos. No se ha ejecutado aún la deduplicación exacta y aproximada global, la revalidación semanal de redistribución NASA ni la separación General/HKD y train/validation/test. Esta revisión añade trazabilidad y decisiones concretas, pero no altera los contadores de admisión ni habilita entrenamiento.


## Ampliación de revisión de archivos NASA (2026-11-05)

La auditoría por archivo cubre ahora **10 textos**:

- **6 pasan revisión individual y se han copiado** al corpus acotado `data/datasets/admitted/nasa-ntrs-file-reviewed-v1/`: `19620002819`, `19630000935`, `19620004488`, `19630000937`, `19640011871` y `19630005290`.
- **3 retenidos por OCR severo:** `19620000001`, `19620002834` y `19620002866`.
- **1 retenido por derechos y OCR no resueltos:** `19630000936`.

Los seis pases suman **701.871 bytes UTF-8**. Sus copias coinciden byte por byte con los originales (Git blob SHA-1 idéntico); el SHA-256, tamaño, título, fuente y destino constan en el manifiesto documental del corpus acotado. Los cuatro retenidos no se copiaron y los **814 textos restantes siguen sin revisión individual**.

La colección completa de 824 sigue siendo candidata. Los seis documentos aceptados permanecen sin habilitación de entrenamiento ni cómputo Level A hasta completar deduplicación exacta/aproximada global, revalidación de restricciones y particionado. La comprobación de integridad se ejecuta en `.github/workflows/validate-nasa-file-reviewed-corpus.yml`.
