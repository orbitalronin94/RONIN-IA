# Biblioteca Digital Hispánica — catálogo BNE y OCR

**Estado: catálogo y licencia de metadatos verificados; textos OCR solo candidatos por obra/edición. No se admite el OCR en bloque.**

La BNE publica un conjunto descargable de metadatos de la Biblioteca Digital Hispánica. El registro oficial de datos.gob.es indica que el catálogo incluye enlaces a los objetos digitales y, para obras textuales procesadas, enlaces a texto OCR. La distribución del catálogo declara CC BY 4.0.

Fuente oficial: https://datos.gob.es/es/catalogo/ea0019768-biblioteca-digital-set-completo1

## Límite de la licencia

La licencia CC BY 4.0 verificada corresponde al conjunto de datos de catálogo y sus metadatos. **No se interpreta como una licencia general de todos los libros, manuscritos o textos OCR enlazados.**

Solo se podrá extraer texto de una obra si su registro individual acredita dominio público o una licencia compatible aplicable a la obra, traducción, edición, introducción, notas y aparato editorial concretos.

## Ingestión

- Descargar el archivo de metadatos y fijar versión/fecha/hash.
- Mantener identificador BNE, signatura, autor, título, fecha, edición y declaración de derechos.
- Seleccionar solo obras cuyo texto completo esté individualmente liberado.
- Excluir traducciones y ediciones modernas protegidas, anotaciones editoriales y OCR de estado jurídico incierto.
- Calcular hashes del original y del OCR normalizado; revisar calidad, duplicados y solapamiento con los 608 documentos ya admitidos.
- Mantener atribución BNE y la licencia CC BY 4.0 del catálogo separada de los derechos del texto.

**Destino provisional:** Humanidades, pool de obras históricas candidatas. No entrenable hasta la revisión por obra.
