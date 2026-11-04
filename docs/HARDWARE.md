# Hardware y runners gratuitos

## Entorno operativo de referencia

RONIN usa como referencia los runners estándar de GitHub Actions para repositorios públicos, con `runs-on: ubuntu-latest`.

| Recurso | Especificación publicada |
|---|---:|
| CPU | 4 vCPU |
| RAM | 16 GB |
| Almacenamiento | 14 GB SSD nominales |
| Arquitectura | x86_64 |
| GPU CUDA | No incluida |
| Coste del runner estándar público | Gratis |

Consulta la [documentación oficial de GitHub sobre runners alojados](https://docs.github.com/en/actions/reference/runners/github-hosted-runners). Los runners estándar son gratuitos para repositorios públicos; no extrapolar esta condición a repositorios privados ni a runners de mayor tamaño.

## Límites prácticos

- Cada trabajo recibe una máquina virtual nueva. Los trabajos paralelos no comparten CPU, RAM, disco ni aceleradores.
- El disco es efímero y los 14 GB son nominales; el sistema, Python y las dependencias consumen parte.
- La RAM disponible para PyTorch es menor que la cifra nominal: pesos, gradientes, estados de AdamW, activaciones y temporales compiten por ella.
- No hay GPU CUDA en el runner estándar. El entrenamiento debe usar CPU y FP32.
- Los checkpoints y datos locales desaparecen al terminar el trabajo. No utilizar Actions como almacenamiento persistente.
- Las imágenes `ubuntu-latest` pueden cambiar. El workflow registra recursos observados para que cada medición tenga contexto.

## Uso adecuado

1. Lint, comprobaciones del paquete y pruebas unitarias.
2. Pruebas de integración de arquitectura, tokenizador, optimizador y checkpoints.
3. Entrenamientos diminutos de humo en CPU con datos sintéticos temporales.
4. Verificación de inicialización aleatoria y aislamiento de los tutores.
5. Microexperimentos reproducibles y evaluación de pruebas pequeñas.

Actions no es una plataforma para preentrenamiento prolongado, generación masiva de corpus, entrenamiento distribuido ni experimentos de miles de millones de parámetros.

## Escala de perfiles

| Perfil | Parámetros objetivo | Decisión actual |
|---|---:|---|
| tiny | 9.922.880 | Perfil operativo para pruebas y experimentos CPU pequeños |
| seed-0 | 147.092.736 | No validado en el runner gratuito; medir memoria y duración antes |
| seed-1 | 955.221.504 | Fuera del entorno operativo actual |
| seed-2 | 6.976.598.016 | Fuera del entorno operativo actual |

Los perfiles seed-* siguen siendo objetivos de investigación, no promesas de que el runner pueda ejecutarlos. No afirmar que un perfil cabe sin medir el proceso completo.

## Telemetría obligatoria

El workflow registra CPU, RAM, disco, sistema operativo, Python, PyTorch y disponibilidad CUDA. Para cada entrenamiento no trivial se deben añadir parámetros, precisión, micro-lote, longitud de secuencia, acumulación, pico de RAM, tiempo por paso, tokens por segundo y tamaño del checkpoint.

Los valores publicados son especificaciones de referencia; las cifras observadas en el workflow son la evidencia del experimento. No inferir rendimiento ni generalización a partir del número de parámetros.
