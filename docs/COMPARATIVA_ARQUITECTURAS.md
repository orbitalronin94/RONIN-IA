# Comparativa A/B de arquitecturas

Este experimento compara la implementación histórica del commit
`4c3f497f3a9be8ce518aab2433729e2cae7c2c2d` con la arquitectura actual.

## Condiciones controladas

- Mismo perfil `tiny` actual: vocabulario byte, contexto, capas, cabezas y ancho.
- Mismo corpus de entrenamiento y validación preparado por el mismo script y commits de fuentes.
- Mismo tokenizador `byte-v1`, batch, longitud de secuencia, optimizador, planificador y pasos.
- Mismas semillas para inicialización y muestreo; cada semilla entrena ambos modelos.
- Evaluación únicamente en validation. El test reservado no se lee ni se evalúa.
- Se registran BPB, entropía, perplejidad, parámetros y tiempo por ejecución.

## Qué significa el resultado

La comparación enfrenta dos paquetes arquitectónicos completos:

- Histórico: embeddings posicionales absolutos, atención MHA con proyección QKV fusionada, LayerNorm y MLP GELU 4x.
- Actual: RoPE, atención con proyecciones separadas y GQA configurable, RMSNorm y SwiGLU.

El número de parámetros no es necesariamente igual. Por tanto, el resultado no aísla cada componente ni es iso-parámetro o iso-FLOPs. Es una comparación práctica de las dos arquitecturas tal como están definidas, con idéntico perfil exterior y presupuesto de optimización.

La métrica primaria es BPB de validación; menor es mejor. El resultado de una ejecución corta es una señal exploratoria, no evidencia estadística concluyente. Para una conclusión robusta deben ampliarse pasos y semillas y añadirse una comparación iso-parámetro.

## Ejecución

El workflow se dispara al abrir o actualizar un PR que cambie los componentes relevantes. En PR usa 100 pasos y tres semillas. También admite lanzamiento manual de 1 a 1000 pasos y semillas configurables.

El artefacto `ronin-arquitectura-ab` contiene el informe JSON. No publica corpus ni checkpoints.
