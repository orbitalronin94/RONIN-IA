# Recursos de hardware y ejecución gratuita

## Entorno operativo de referencia

RONIN toma como referencia el entorno gratuito de GitHub Actions para repositorios públicos. El workflow actual usa `runs-on: ubuntu-latest` en sus tres trabajos.

Según la documentación oficial de GitHub, el runner estándar `ubuntu-latest` para repositorios públicos dispone de:

| Recurso | Especificación publicada |
|---|---:|
| CPU | 4 vCPU |
| RAM | 16 GB |
| Almacenamiento | 14 GB SSD |
| Arquitectura | x86_64 |
| GPU CUDA | No incluida |
| Precio del runner estándar público | Gratis |

Los runners estándar son gratuitos y sin límite de minutos para repositorios públicos. Esta condición no debe extrapolarse a repositorios privados ni a runners de mayor tamaño. Referencia: [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

## Límites prácticos

- Cada trabajo de Actions se ejecuta en una máquina virtual nueva. Los trabajos paralelos no comparten memoria, disco, procesos ni GPU.
- El disco es efímero. Los 14 GB son capacidad nominal, no espacio libre para datasets o checkpoints; sistema operativo, herramientas y dependencias consumen parte.
- La RAM anunciada no está íntegramente disponible para PyTorch. El sistema, los procesos auxiliares, el cargador de datos, los pesos, gradientes, estados del optimizador y activaciones compiten por ella.
- El runner estándar no ofrece una GPU NVIDIA/CUDA. La selección automática de precisión debe acabar en FP32 sobre CPU.
- Las máquinas se destruyen al terminar el trabajo. Los resultados que deban conservarse se publicarán como artefactos pequeños y no sensibles, con retención explícita. No usar Actions como almacenamiento de corpus, modelos tutores ni checkpoints persistentes.
- Las imágenes `-latest` pueden cambiar. Registrar las especificaciones observadas en cada ejecución y no tratar la tabla publicada como benchmark del rendimiento de PyTorch.

## Uso admitido en esta fase

El runner gratuito sirve para:

1. Ruff, comprobaciones de paquete y pruebas unitarias.
2. Pruebas de integración de arquitectura, tokenizador, optimizador y checkpoints.
3. Entrenamientos diminutos de humo en CPU, con corpus sintético temporal y número de pasos acotado.
4. Verificación de que la inicialización del estudiante es aleatoria y no importa pesos de tutores.
5. Pruebas de reproducibilidad y evaluación de métricas sobre muestras pequeñas.

No es el entorno para preentrenamiento prolongado, generación masiva de corpus, entrenamiento distribuido, ni para validar escalas de cientos de millones o miles de millones de parámetros.

## Perfiles y decisión de escala

| Perfil | Parámetros objetivo | Decisión actual |
|---|---:|---|
| tiny | 9.964.160 | Perfil operativo para CI y experimentos CPU pequeños |
| seed-0 | 147.909.120 | No habilitar como objetivo de Actions hasta medir RAM máxima, tiempo por paso y estabilidad |
| seed-1 | 958.467.072 | Fuera del entorno gratuito actual |
| seed-2 | 6.993.518.592 | Fuera del entorno gratuito actual |

Los perfiles seed-0, seed-1 y seed-2 permanecen como configuraciones de investigación, no como promesas de que el runner puede ejecutarlos. No reducir el tamaño de RONIN a partir de una estimación de parámetros aislada ni afirmar que un perfil cabe sin medir el proceso completo.

## Diagnóstico obligatorio por ejecución

Antes de cualquier experimento no trivial, registrar:

- etiqueta y sistema operativo del runner;
- CPU detectada y memoria total/disponible;
- espacio libre antes y después de instalar dependencias;
- versión de Python y PyTorch;
- disponibilidad CUDA y número/nombre de dispositivos;
- parámetros, precisión, micro-lote, longitud de secuencia y acumulación;
- pico de RAM, tiempo por paso, tokens por segundo y estado final;
- tamaño del checkpoint y espacio libre restante.

Los valores publicados por GitHub son especificaciones de referencia; los valores observados por el propio workflow son la evidencia del experimento.

## Regla de promoción

Un perfil solo puede pasar de «objetivo» a «validado en hardware» si existe un workflow reproducible que termina correctamente y conserva un informe con las mediciones anteriores. No se deben inferir tokens por segundo, duración de entrenamiento, capacidad de generalización ni coste a partir del número de parámetros.

Los recursos de Actions son adecuados para construir y auditar RONIN desde cero, no para fingir que ya disponemos de un clúster de entrenamiento.
