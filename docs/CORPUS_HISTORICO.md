# Corpus histórico: bibliotecas, autores y obras en dominio público

## Objetivo

Ampliar el corpus de RONIN con castellano de distintas épocas y disciplinas mediante obras históricas recuperadas de bibliotecas y archivos. Esta línea complementa los conjuntos modernos con licencia abierta; no los sustituye.

RONIN se entrena desde pesos aleatorios. Los tutores locales, cuando se usen, solo generan texto y nunca transfieren parámetros al estudiante.

## Fuentes prioritarias para investigar

| Fuente | Uso previsto | Condición para admitir un documento |
|---|---|---|
| Biblioteca Nacional de España (BNE), Autores en dominio público | Identificar autores y obras cuyos derechos han expirado | Verificar autoría, fecha de fallecimiento, coautoría, traducción, edición y registro digital concreto |
| Biblioteca Digital Hispánica (BDH) | Localizar y consultar facsímiles y objetos digitales de la BNE | Comprobar derechos/reutilización del objeto y la edición que se transcribe |
| Biblioteca Virtual del Patrimonio Bibliográfico (BVPH) | Libros y manuscritos históricos de bibliotecas patrimoniales | Registrar la licencia indicada en cada ficha; no asumir que todos los registros comparten condiciones |
| Europeana | Descubrir fondos de bibliotecas y archivos europeos | Admitir preferentemente CC0 o Public Domain Mark; revisar el estado de derechos por objeto |
| Project Gutenberg | Textos clásicos ya transcritos | Revisar la nota legal del título y la jurisdicción; sus condiciones estadounidenses no acreditan por sí solas el dominio público en España |
| Wikisource | Transcripciones colaborativas de obras clásicas | Verificar la obra original, la edición fuente y el estado de derechos de la transcripción |

Enlaces de consulta:

- BNE, autores en dominio público: https://www.bne.es/es/catalogos/autores-dominio-publico
- Biblioteca Digital Hispánica: https://www.bne.es/es/catalogos/biblioteca-digital-hispanica
- BVPH: https://bvpb.mcu.es/
- Europeana: https://www.europeana.eu/
- Project Gutenberg: https://www.gutenberg.org/
- Wikisource: https://es.wikisource.org/

## Primera lista de autores para catalogar

La lista es un punto de partida para localizar obras, no una autorización automática de ingesta:

- Siglos XVI-XVII: Miguel de Cervantes, Lope de Vega, Francisco de Quevedo, Luis de Góngora, Tirso de Molina, Calderón de la Barca y Santa Teresa de Jesús.
- Siglo XVIII: Benito Jerónimo Feijoo, José Cadalso, Gaspar Melchor de Jovellanos y Leandro Fernández de Moratín.
- Historia, ciencia y ensayo: añadir autores de cada disciplina después de comprobar individualmente sus fechas, coautorías y derechos.

Se priorizarán obras originales en castellano. Las traducciones se tratarán como obras separadas: que el autor original haya fallecido hace siglos no extingue los derechos de una traducción moderna.

## Regla jurídica y documental

No se considerará que «sin licencia» equivale a libre uso. Una obra solo entra si se acredita dominio público aplicable o una licencia explícita compatible.

Para obras españolas se tendrá en cuenta el régimen transitorio de derechos de autor: las obras de autores fallecidos antes del 7 de diciembre de 1987 pueden estar sujetas al plazo de 80 años post mortem. Se verificará la fecha y el cómputo en cada caso, además de coautores, traductores, editores, ilustraciones y otros elementos protegidos.

La digitalización o el OCR pueden tener condiciones propias. La ficha del documento debe registrar exactamente qué se reutiliza y bajo qué fundamento. Si la situación es dudosa, el documento queda fuera hasta resolverla.

## Registro obligatorio por obra

Cada registro del catálogo debe contener, como mínimo:

- Identificador estable y título.
- Autor y fechas de nacimiento/fallecimiento, con fuente de verificación.
- Fecha y lugar de publicación de la edición utilizada.
- Biblioteca, identificador del objeto y URL de origen.
- Declaración de derechos/licencia del objeto y URL de esa declaración.
- Traductor, editor, ilustrador y demás colaboradores, cuando existan.
- Formato descargado, fecha de recuperación y SHA-256.
- Estado de revisión: pendiente, aprobado o rechazado; motivo y responsable.
- Método de extracción/OCR, versión del proceso y SHA-256 del texto resultante.

## Fases de incorporación

1. Crear un catálogo de candidatos sin descargar masivamente los fondos.
2. Verificar derechos y metadatos por obra.
3. Descargar únicamente documentos aprobados y conservar el facsímil o fuente original localmente.
4. Extraer texto/OCR y medir su calidad; conservar el texto bruto para auditoría.
5. Limpiar cabeceras, pies, números de página y errores de OCR sin borrar rasgos lingüísticos legítimos.
6. Deduplicar y separar por obra o fuente antes de crear entrenamiento, validación y prueba.
7. Generar manifiestos con procedencia y hashes. Los textos y checkpoints permanecen fuera de Git.

## Primer objetivo técnico

La primera entrega será un catálogo auditable y un pequeño lote piloto de obras con derechos verificados. No se ejecutará una ingesta masiva ni se declarará entrenamiento histórico hasta que existan archivos descargados, hashes, manifiestos y pruebas de calidad.