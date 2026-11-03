# Manifiesto v3: contrato de capacidades

El registro de `ronin/manifest/registry.py` contiene la lista ejecutable de 50 capacidades. Cada entrada especifica categoría, perfil mínimo, estado de implementación y ruta de evidencia. Una capacidad marcada como implementada sin una ruta de evidencia real no debe contribuir al indicador de preparación.

## Distribución por categorías

| Área | Cantidad |
|---|---:|
| Entrenamiento | 16 |
| Datos | 8 |
| Evaluación | 8 |
| Monitorización | 6 |
| Despliegue | 5 |
| Pruebas | 7 |
| **Total** | **50** |

## Escalera de modelos

| Perfil | Escala objetivo | Hardware previsto en el proyecto |
|---|---:|---|
| tiny | ~10 M | CPU |
| seed-0 | ~150 M | 1× RTX 4090 |
| seed-1 | ~1.000 M | 2× A100 40 GB |
| seed-2 | ~7.000 M | 4× A100 80 GB |

Las configuraciones actuales del Transformer son puntos de partida, no correspondencias verificadas con esos objetivos de parámetros. Ejecutar siempre `ronin count-params --profile NOMBRE` y registrar el resultado. Ajustar las dimensiones antes de afirmar que se ha alcanzado un tamaño objetivo. La compatibilidad con el hardware exige medir memoria máxima y rendimiento en la máquina real.

## Matriz histórica de objetivos

El documento inicial del proyecto incluía objetivos de capacidades activadas de 30/50 (tiny), 37/50 (seed-0), 45/50 (seed-1) y 47/50 (seed-2). Se conservan como metas de planificación, no como valores exigidos por el código, porque los valores predeterminados originales, la lista de activación por ciclo y las ampliaciones de seed-0 no eran coherentes. El registro ejecutable utiliza ahora `min_profile` y estados basados en evidencias. Cualquier matriz futura debe reconciliarse con las 50 definiciones individuales; no se deben forzar los totales marcando capacidades como activas sin justificación.

## Reglas críticas de corrección

- Se evalúa `min_profile`; no es metadato decorativo.
- Un estado predeterminado (ACTIVO/DESACTIVADO/PLANIFICADO) no equivale a la activación por perfil.
- `readiness_percent` solo cuenta capacidades implementadas con una ruta de evidencia no vacía.
- Las pruebas y CI también son capacidades: no se marcan como implementadas hasta que existan y pasen las pruebas y el flujo correspondiente.
- El número de parámetros se obtiene de los parámetros instanciados, no de un objetivo codificado a mano.
- La compatibilidad de BF16 en CPU varía; seleccionar precisión en tiempo de ejecución y fallar explícitamente si un modo solicitado no está disponible.
- Los estimadores de memoria deben incluir activaciones, gradientes, estados del optimizador, búferes temporales, fragmentación y sobrecarga distribuida. Los cálculos basados solo en parámetros no garantizan que el modelo quepa.
- Un umbral de pérdida en un único lote repetido solo demuestra memorización, no generalización.
- La comparación de perplejidad entre tokenizadores exige cautela; utilizar BPB para una comparación normalizada.
- El rendimiento, tiempo y coste solo son resultados medidos cuando se capturan con hardware, configuración y metadatos de datos identificados.
- La salida YAML debe conservar los tipos escalares y listas correctos; usar un serializador YAML, no concatenación de cadenas.

## CLI

- `ronin info --profile tiny`
- `ronin count-params --profile tiny`
- `ronin features [--category training|data|evaluation|monitoring|deployment|tests]`
- `ronin readiness --profile tiny`
- `ronin matrix`
- `ronin roadmap`

La lista de capacidades no sustituye a una implementación funcional. Consultar [ROADMAP.md](ROADMAP.md) para conocer los criterios de aceptación.
