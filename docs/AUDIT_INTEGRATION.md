# Auditoría e integración del código de referencia

## Alcance y decisión

Se revisó el código de referencia compartido en la conversación: núcleo Transformer NumPy con backpropagation manual, tokenizador byte-level BPE, pipeline de corpus, métricas, entrenamiento, checkpoints y fragmentos de evaluación/Hub. La arquitectura útil se ha trasladado a PyTorch en lugar de mantener un segundo backend.

La integración se realiza en la rama `integration/audited-transformer-components`. No se importan pesos preentrenados al estudiante. Los modelos auxiliares MIT permanecen como generadores externos de texto, con procedencia, y nunca comparten parámetros con RONIN.

## Componentes integrados

| Idea del código de referencia | Decisión |
|---|---|
| RoPE | Integrada en PyTorch y diferenciable con autograd |
| RMSNorm | Integrada en PyTorch |
| SwiGLU | Integrada en PyTorch |
| GQA | Integrada con número configurable de cabezas KV |
| Pesos de embeddings compartidos | Se conserva la implementación existente |
| Backpropagation manual NumPy | No integrada; PyTorch autograd es el único motor de gradientes |
| BPE artesanal | No integrado: el decodificador de referencia no reconstruye los bytes de tokens fusionados |
| Pipeline de datos duplicado | No integrado como paquete paralelo; se conserva el pipeline RONIN |
| Métricas BLEU/F1 de referencia | No se incorporan como métricas oficiales sin corregir sus definiciones |
| Servidor, scheduler y caché KV de referencia | No se declaran capacidades operativas sin integración real ni pruebas |

## Hallazgos de auditoría

### Críticos

1. **Decodificación BPE incorrecta.** Los tokens fusionados se guardan como claves centinela `\x00m<ID>`; `_rebuild_reverse()` convierte esas claves a bytes Latin-1. Por tanto, `decode(encode(text))` no reconstruye los bytes originales de los tokens fusionados. El test de round-trip incluido no detectaría necesariamente todos los merges y casos.
2. **Backpropagation manual sin validación numérica.** La atención GQA, RoPE, embeddings atados y SwiGLU requieren pruebas de gradiente por diferencias finitas. Un test que solo comprueba gradientes no nulos no demuestra que sean correctos.
3. **Comprobación de pérdida tardía en el Trainer NumPy.** El paso del optimizador ocurre antes de comprobar si la pérdida es NaN o infinita. Un paso inválido puede contaminar los pesos antes de abortar.
4. **Checkpoint pickle inseguro.** Cargar checkpoints pickle de fuentes no confiables puede ejecutar código. Los checkpoints solo deben cargarse desde fuentes de confianza; no se debe tratar un archivo `.pt` como formato seguro por su extensión.
5. **Afirmaciones de serving no respaldadas.** La presencia de clases para KV cache o scheduler no demuestra que la inferencia incremental las utilice. En el código compartido, el estado de caché y los límites del scheduler no están conectados a la ruta real de generación.

### Importantes

- El codificador BPE vuelve a recorrer toda la secuencia para cada merge y busca cada par mediante `list.index`; su coste crece rápidamente.
- La división del corpus se hace por posición de token y no por documento/fuente; puede cortar documentos y no garantiza ausencia de fuga entre particiones.
- La carga JSONL del ejemplo no asigna necesariamente los campos de licencia, URL e idioma a sus campos tipados de `Document`; parte de esa información queda como metadatos.
- El registro de procedencia de ejemplo crea fuentes con recuento cero en vez de agregar documentos por fuente.
- El método denominado deduplicación aproximada solo calcula un hash de texto en minúsculas; no es una técnica real de near-deduplication.
- La métrica F1 usa conjuntos de palabras y pierde multiplicidad. El BLEU-4 simplificado omite la penalización de brevedad; no debe presentarse como BLEU estándar.
- La validación y el entrenamiento deben separar estrictamente corpus, fuentes y documentos. La pérdida sobre muestras aleatorias de una única secuencia no reemplaza una evaluación fija y reproducible.
- La función de reanudación del Trainer de referencia restaura un checkpoint, pero no toda la historia del entrenamiento ni el mejor resultado de validación.
- El código de referencia incluye interfaces opcionales y fragmentos de Hub que no constituyen por sí mismos un backend ONNX funcional o una ruta real de predicción por lotes.
- Los snippets MoE/servidor adicionales revisados en la conversación no deben pasar a producción sin pruebas: el backward del router top-k debe contrastarse con gradientes numéricos; la caché paginada y el scheduler deben estar conectados a la generación real; la etiqueta mixed precision requiere autocast y escalado reales.

## Cambios realizados en esta rama

- Ampliación de `ModelConfig` con `n_kv_heads`, `d_ff`, `rope_theta` y `rms_norm_eps`, con validaciones.
- Sustitución de embeddings posicionales aprendidos por RoPE.
- Sustitución de LayerNorm por RMSNorm.
- Sustitución de MLP GELU por SwiGLU.
- Atención multi-head generalizada a GQA.
- Actualización del recuento analítico de parámetros para coincidir con los módulos reales.
- Pruebas para forma y gradiente de RoPE, GQA, SwiGLU/RMSNorm y pesos atados.
- Actualización de README y documentación de arquitectura/manifiesto.

## Validación pendiente

La integración no se considera terminada hasta que CI ejecute y supere:

```bash
pip install -e '.[dev]'
pytest
ruff check ronin tests scripts
python scripts/train_text.py --text /tmp/ronin-smoke.txt --profile tiny --steps 1 --device cpu
```

También debe comprobarse que `count_parameters(config)` coincide con `RoninLM(config).parameter_count` para todos los perfiles sin instanciar los perfiles grandes. Los tamaños de planificación no son garantías de memoria ni rendimiento.
