# Datos de entrenamiento

## Única raíz de datos

`data/datasets/` es la ubicación canónica de todos los corpus, bibliotecas, manifiestos, particiones y registros de derechos. No existe una segunda carpeta de datasets en la raíz del repositorio.

La estructura separa:

- `admitted/`: fuentes y particiones admitidas con procedencia y manifiestos.
- `candidates/`: material adquirido pendiente de revisión o consolidación.
- `libraries/`: bibliotecas temáticas y sus inventarios.
- `quarantine/`: material retenido fuera del entrenamiento.
- `rights_registry/`: política, esquema y registros de derechos.
- `reviews/`: evidencias de revisión de fuentes y documentos.

## Corpus usado por el ciclo principal

La mezcla no-tutor fijada actualmente utiliza solo estas particiones train:

| Fuente | Documentos | Bytes de origen |
|---|---:|---:|
| Literatura española | 608 | 140.295.523 |
| Mathlib4 | 8.498 | 97.629.252 |
| NASA NTRS revisado individualmente | 2 | 32.409 |
| **Total** | **9.108** | **237.957.184** |

Las particiones validation y test permanecen excluidas. El resto de NASA NTRS, ScienceVerse y los documentos propios del propietario no se incorporan a esta mezcla mientras no completen sus revisiones y particiones correspondientes.

## Condiciones de entrenamiento

Un documento solo puede entrar en train si su origen y derechos permiten el uso previsto, el payload está presente e íntegro, su hash está verificado y el manifiesto lo asigna explícitamente a train. La adquisición o la presencia bajo `admitted/` no bastan por sí solas para incluirlo en una ejecución concreta.

Los workflows verifican manifiestos y hashes antes de ensamblar la mezcla. La separación entre train, validation y test debe mantenerse a nivel de documento o fuente para evitar filtraciones. No se versionan credenciales ni se requiere acceso a datasets privados o restringidos.
