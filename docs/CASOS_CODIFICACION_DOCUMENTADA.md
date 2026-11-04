# Biblioteca de casos de codificación documentada

## Propósito

Esta biblioteca reúne obras históricas y literarias útiles para enseñar a RONIN
a reconocer mensajes ocultos, criptogramas, acrósticos y otros mecanismos de
codificación sin confundir una lectura sugerente con un descifrado demostrado.

**No es todavía un corpus de entrenamiento.** Es un catálogo de investigación
y anotación. Antes de incorporar el texto íntegro a los datos de entrenamiento
se deben fijar una edición digital concreta, su procedencia, su licencia,
un hash verificable y la política de partición. Las referencias académicas no
sustituyen la descarga y verificación del ejemplar fuente.

## Estados que no deben mezclarse

- `decoded_documented`: existe una solución reproducible y una fuente
  identificable que documenta el mecanismo.
- `acrostic_documented_interpretation`: el patrón formal puede comprobarse,
  pero su interpretación (por ejemplo, la identidad del autor) no es por ello
  concluyente.
- `fictional_cipher_solved_in_narrative`: el criptograma pertenece a una obra
  de ficción y su solución se da dentro del propio relato. No es evidencia de
  un mensaje histórico oculto en el libro.
- `historical_explanation_available`: una fuente histórica posterior explica
  un sistema anterior; registrar qué parte explica y qué no.
- `claim_needs_verification`: afirmación interesante sin respaldo suficiente
  todavía. No usar como ejemplo positivo confirmado.

## Casos con evidencia identificable

### 1. Johannes Trithemius — *Steganographia* (c. 1500)

**Estado:** `decoded_documented`.

El Libro III contiene criptogramas que Jim Reeds identificó y resolvió en un
artículo de *Cryptologia* (1998). La presencia de cifrados en los Libros I y II
ya era conocida desde 1606; no atribuir a Reeds el descubrimiento de esos dos
libros. El caso muestra cómo un texto que aparenta ser mágico puede contener
un procedimiento criptográfico real.

Referencia principal:
- Jim Reeds, “Solved: The Ciphers in Book III of Trithemius's
  *Steganographia*”, *Cryptologia* 22 (1998), 291–317.
  DOI: https://doi.org/10.1080/0161-119891886948

### 2. *Hypnerotomachia Poliphili* (Venecia, 1499)

**Estado:** `acrostic_documented_interpretation`.

Las letras iniciales ornamentales de los capítulos forman el acróstico
“POLIAM FRATER FRANCISCVS COLVMNA PERAMAVIT”. La existencia del patrón es
comprobable en la estructura del libro. Se ha interpretado como “el hermano
Francesco Colonna amó intensamente a Polia” y como indicio de autoría; no
presentarlo como prueba definitiva de quién escribió la obra. Las fuentes
académicas consultadas no son uniformes al describir el recuento de capítulos
o la secuencia de iniciales, por lo que cualquier reproducción computacional
debe fijar edición y transcripción antes de validar el patrón.

Referencias:
- Morgan Library & Museum, ficha de la obra y explicación del acróstico:
  https://www.themorgan.org/morganmobile/in-disguise/colonna
- University of Otago, “Authorial Acrostics”:
  https://www.otago.ac.nz/library/exhibitions/authorship/cabinet8-1.html
- Estudio académico sobre la obra y sus problemas de autoría:
  https://libraetd.lib.virginia.edu/downloads/jh343s79w?filename=X004457851.pdf

### 3. Gustavus Selenus — *Cryptomenytices et Cryptographiae libri IX* (1624)

**Estado:** `historical_explanation_available`.

La obra de 1624 incluye una explicación del sistema de esteganografía de
Trithemius. El título correcto es *Cryptomenytices et Cryptographiae libri IX*;
no “Cryptomenytics”. Selenus es el seudónimo tradicionalmente asociado con
Augustus, duque de Brunswick-Lüneburg. Registrar este libro como testimonio
histórico y explicación temprana del sistema, no como el descifrado moderno
del Libro III que publicó Reeds en 1998.

Referencias de orientación:
- Transcripción y bibliografía de Trithemius:
  https://philipneal.net/voynichsources/lingua_ignota_steganographia/
- Referencia bibliográfica al título de 1624:
  https://trithemius.com/bibliography/

### 4. Edgar Allan Poe — “The Gold-Bug” / “El escarabajo de oro” (1843)

**Estado:** `fictional_cipher_solved_in_narrative`.

El relato contiene un criptograma de sustitución y explica su resolución
mediante análisis de frecuencias y contexto lingüístico. Es un ejemplo
didáctico excelente, pero el mensaje es parte de la ficción y no un documento
histórico cifrado.

Referencias:
- Texto y notas de la Edgar Allan Poe Society of Baltimore:
  https://eapoe.org/WORKS/cmprs/pt042c03.htm
- New York State Library, “The Gold-Bug: Cracking the Code”:
  https://nyslibrary.libguides.com/blogs/system/edgar-allan-poe-in-nys-library-collections-detective-fiction-cryptography-and-alexander

### 5. Arthur Conan Doyle — “The Adventure of the Dancing Men” (1903)

**Estado:** `fictional_cipher_solved_in_narrative`.

El relato de Sherlock Holmes presenta un cifrado de sustitución mediante
figuras humanas y su solución aparece en la propia narración. No confundirlo
con “The Adventure of the Speckled Band” / “La banda de lunares”, que es otro
relato y no el caso del criptograma de los bailarines.

La clave es una invención literaria de Doyle, no un criptograma histórico
descubierto en un manuscrito anterior.

Edición digital de acceso abierto:
- Project Gutenberg Australia, texto de *The Return of Sherlock Holmes*,
  con “The Adventure of the Dancing Men” y su publicación original en 1903:
  https://gutenberg.net.au/ebooks/c00016.html

### 6. Julio Verne — *La Jangada* (1881)

**Estado:** `fictional_cipher_solved_in_narrative` para la presencia y solución
narrativa del criptograma; afirmación histórica sobre el método: refutada en
la formulación inicial.

La novela incluye un criptograma cuya solución se desarrolla dentro de la
narración. Sin embargo, no debe atribuirse a Verne la invención ni la primera
exposición del método de solución. Un estudio histórico de la NSA sobre los
criptogramas de Verne señala que el procedimiento de análisis era anterior y
que Verne no lo inventó; también cuestiona su pretensión de haber resuelto el
cifrado por un método nuevo. La obra sigue siendo útil como ejemplo de
criptografía ficcional, no como prioridad histórica del método.

Referencia especializada:
- William F. Friedman, estudio histórico sobre criptogramas en la obra de
  Verne, documento desclasificado de la NSA:
  https://www.nsa.gov/portals/75/documents/news-features/declassified-documents/friedman-documents/publications/FOLDER_205/41762559080174.pdf

## Descargas primarias incorporadas a la adquisición automatizada

El flujo de auditoría descarga, sin autenticación y fuera de Git, cuatro fuentes
concretas. Verifica formato o marcadores de contenido, calcula SHA-256 y publica
los originales junto con un manifiesto de procedencia como artefacto temporal:

- Poe, *The Works of Edgar Allan Poe*, vol. 1 (incluye “The Gold-Bug”):
  https://www.gutenberg.org/cache/epub/2147/pg2147.txt
- Verne, *The Giant Raft* / *La Jangada*:
  https://www.gutenberg.org/cache/epub/3091/pg3091.txt
- Doyle, *The Return of Sherlock Holmes* (incluye “The Adventure of the Dancing
  Men”):
  https://gutenberg.net.au/ebooks/c00016.html
- Selenus, ejemplar de 1624 de Wellcome Collection, 550 imágenes, descarga PDF
  con Public Domain Mark:
  https://iiif.wellcomecollection.org/pdf/b12946308

La descarga no significa que estos materiales ya formen parte del entrenamiento:
el manifiesto los marca como `excluded_pending_manual_review`. El PDF latino
de Selenus requiere OCR/transcripción revisada antes de usarlo como texto.
La *Hypnerotomachia Poliphili* permanece en el catálogo bibliográfico, pero no
se incorpora hasta fijar un ejemplar digital y derechos verificables.

El código de adquisición está en `scripts/acquire_cryptography_library.py`;
las pruebas automatizadas verifican el manifiesto, los hashes y la exclusión
del entrenamiento general.

## Reglas de adquisición y anotación

1. Descargar solo ediciones con acceso anónimo directo y derechos claros.
   No usar repositorios que exijan cuenta, token, API key, cookies, DM o
   aceptación condicionada a registro.
2. Fijar edición, URL de descarga, revisión o fecha de consulta, licencia,
   tamaño y SHA-256 del fichero original.
3. Conservar la transcripción original y una versión normalizada por separado;
   no reemplazar grafías históricas ni signos que puedan formar parte de una
   clave.
4. Registrar por separado el texto cifrado, el texto claro propuesto, el
   algoritmo o patrón, los pasos reproducibles, la fuente de la solución y
   las incertidumbres editoriales.
5. Un acróstico reproducible no prueba automáticamente una autoría. Una
   solución incluida en una ficción no convierte el texto en evidencia
   histórica. Una explicación posterior no debe confundirse con el
   descubrimiento inicial.
6. Los casos `claim_needs_verification` no se usan como ejemplos positivos
   para entrenar detección de códigos confirmados.
7. Mantener estos materiales fuera del holdout general hasta que se defina un
   protocolo específico de evaluación de codificación. No usar el mismo
   ejemplo para diseñar reglas y luego presentarlo como evaluación independiente.

## Uso en REF

Estos casos sirven para desarrollar la dimensión de codificación de REF.
La clase epistémica de las afirmaciones que aparecen en ellos se anota por
separado: un libro puede contener narración ficticia, datos históricos,
afirmaciones empíricas y texto cifrado en diferentes fragmentos.

No penalizar el lenguaje mágico, religioso, alegórico o arcaico como si fuera
ruido. Tampoco inferir que todo pasaje oscuro oculta un cifrado. La etiqueta
debe describir la evidencia disponible, no la fascinación del lector.
