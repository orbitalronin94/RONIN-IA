# Libro de ejecuciones (runs) de RONIN-IA

Este es el registro cronológico de ejecuciones relevantes de GitHub Actions. Cada entrada enlaza a la ejecución original, identifica el commit y resume qué se ejecutó y qué se incorporó. Los detalles numéricos, logs y artefactos permanecen en la página de cada run.

**Regla operativa:** toda ejecución de workflows registrados debe añadir automáticamente una entrada al terminar, tanto si acaba en éxito como en fallo o cancelación. El resumen de cada workflow debe enlazar directamente a este libro. Las correcciones y ampliaciones de una iteración se registran como nuevas entradas; no se reescribe el historial para ocultar resultados anteriores.

## Historial

| Fecha UTC | Workflow / ejecución | Estado | Qué ocurrió / qué se incorporó | Commit |
|---|---|---|---|---|
| 2026-11-04 | [Experimento oficial #1](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41827976377) | success | Entrenamiento tiny desde cero, 1.000 pasos, semilla 1337. MMLU-Pro custom next-byte: 11,115% inicial y 10,978% final; cobertura 97,13%. Resultado sin evidencia de mejora; 345 ítems omitidos. | ba22ed03 |
| 2026-11-04 | [Experimento oficial #3](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41842575826) | in_progress al último chequeo | Ejecución automática tras integrar PR #44: entrenamiento oficial completo con 1.000 pasos y una semilla. En el último chequeo seguía entrenando; no se consignan métricas finales hasta consultar el artefacto. | 3a47956f |
| 2026-11-04 | [Validación del manifiesto externo #1](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41848179047) | success | Validador de inventario externo ejecutado correctamente. PR #47 incorporó 21 fuentes, 53 etiquetas de dominio, reglas G-0, validador y CI dedicado. | 4aefd7ca |
| 2026-11-04 | [Integración continua #428](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41848178762) | success | CI general completada correctamente para la iteración de inventario de datasets externos. | 4aefd7ca |

## Formato obligatorio para nuevas entradas

El registrador automático añade fecha UTC, nombre del workflow, número y URL del run, resultado, rama, commit, evento disparador y resumen de la finalidad del workflow. Para los runs que producen artefactos, la URL del run permite acceder a los informes y archivos publicados.

Si una ejecución cambia datos, código o documentación, la descripción debe identificar el artefacto o commit correspondiente. Un run fallido también se registra: el fallo forma parte de la trazabilidad experimental.

## Enlaces de referencia

- [Workflows de GitHub Actions](https://github.com/orbitalronin94/RONIN-IA/actions)
- [Manifiesto de datasets externos](../data/manifests/external_datasets.json)
- [Política de ingesta y derechos G-0](INGESTA_AMPLIA_DATASETS_EXTERNOS.md)
- [README del proyecto](../README.md)
