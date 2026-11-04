# Filtro epistemico de RONIN (REF)

## Proposito

REF separa la naturaleza de una afirmacion, su genero textual y el estado de
interpretacion del fragmento. No es un detector automatico de verdad ni una
clasificacion de libros completos. La unidad preferente es una afirmacion o un
fragmento con contexto suficiente.

Principio rector: **RONIN no debe confundir lo que puede comprobarse, lo que
puede imaginarse, lo que puede estar codificado y lo que aun no puede
determinarse.**

## Ejes independientes

### Clase epistemica

- `falsifiable`: existe al menos un resultado observable que entraria en
  conflicto con la afirmacion, una vez especificadas sus condiciones.
- `non_falsifiable`: la formulacion no ofrece un criterio empirico posible
  para refutarla. Esto no significa que sea falsa, absurda o inutil.
- `mixed`: combina afirmaciones de distinto tipo que conviene separar.
- `undetermined`: falta contexto, precision o evidencia para decidir.

La falsabilidad es un criterio de demarcacion metodologica, no una etiqueta de
verdad. Las afirmaciones normativas, matematicas, metaforicas o metafisicas
requieren tratamiento propio; no deben declararse carentes de significado.

### Tipo de afirmacion

El campo `claim_type` distingue, entre otros, contenido empirico, causal,
metafisico, normativo, metaforico, ficticio, matematico y procedimental.

### Genero

El campo `genre` describe el contexto (cientifico, historico, religioso,
literario, juridico, tecnico, filosofico, etc.). El genero no determina la
falsabilidad: un texto religioso puede conservar una observacion historica o
una receta contrastable, y un texto cientifico puede contener metaforas.

### Estado de codificacion e interpretacion

- `clear`: lectura suficientemente directa para el anotador.
- `possibly_encoded`: hay indicios para investigar una posible clave,
  nomenclatura especializada, cifrado, alegoria tecnica o convencion perdida.
- `decoded`: existe una interpretacion documentada y evidencia de descifrado.
- `unknown`: no se ha podido determinar.

**No equiparar baja frecuencia, rareza, lenguaje arcaico o aparente absurdo con
baja semantica.** Un grimorio puede usar nombres en clave, simbolos, recetas,
metales, minerales, operaciones o referencias culturales. Tambien puede ser
alegorico, ritual, especulativo o estar corrupto por la transmision. No se
presupone que toda receta funcione ni que todo pasaje oculte quimica.

Para marcar `decoded` se exige documentar `decoding_evidence`. Una hipotesis
de lectura permanece en `possibly_encoded` o `undetermined` hasta que se
justifique.

## Esquema de anotacion

Cada registro JSONL representa un fragmento/afirmacion y conserva:

- Identificador del registro y de la fuente.
- SHA-256 de la fuente y licencia/procedencia declaradas.
- Texto, y opcionalmente offsets de caracteres.
- Clase epistemica, tipo de afirmacion, genero y estado de codificacion.
- Criterio potencial de refutacion, evidencia requerida y evidencia de
  descifrado cuando corresponda.
- Confianza, anotador y version de politica.

El esquema estructural vive en `ronin/epistemic/schema.py`. Su validador no
decide si la anotacion es intelectualmente correcta: solo comprueba que el
registro cumple el contrato.

## Ejemplos de politica

| Fragmento | Tratamiento inicial |
|---|---|
| «El agua hierve a 100 °C a presion atmosferica estandar» | Falsable; exige condiciones y medicion |
| «El tiempo es un rio» | Metaforico; no evaluarlo como una ley fisica |
| «Existe un proposito invisible que gobierna todo» | No falsable en esa formulacion |
| «La oracion reduce el estres» | Falsable si se operacionaliza y controla |
| «El preparado cambia de color al calentar el mercurio verde» | Indeterminado; aclarar terminos, seguridad, contexto y procedimiento |
| «El leon verde devora al sol» | Posible simbolismo o nomenclatura alquimica; no concluir que sea literal ni que este descifrado |
| «El manuscrito describe una operacion que produce un precipitado» | Afirmacion procedimental potencialmente contrastable, tras identificar sustancias y condiciones |

Los ejemplos son ilustrativos, no evidencia historica ni instrucciones
experimentales. No se deben ejecutar recetas antiguas: algunas sustancias y
procedimientos son toxicos o peligrosos.

## Uso en entrenamiento y evaluacion

1. No introducir textos como «negativos» por su religion, genero o estilo.
2. Mantener el preentrenamiento general separado de las anotaciones REF.
3. Usar REF primero como tarea auxiliar de clasificacion/calibracion, no como
   penalizacion del contenido simbolico.
4. Crear un conjunto de evaluacion con anotacion humana independiente, doble
   revision y adjudicacion de desacuerdos.
5. Mantener separado el holdout REF del holdout de modelado de lenguaje.
6. No permitir que las etiquetas del holdout guien gradientes ni decisiones
   de hiperparametros.
7. Registrar procedencia y licencias verificadas para cada fuente. No descargar
   corpus que requieran cuenta, token, credenciales o aceptacion condicionada.

## Estado

Version inicial del contrato de datos y validacion estructural. No incluye aun
un clasificador automatico, descifrado de textos, corpus historico incorporado
ni resultados de evaluacion.
