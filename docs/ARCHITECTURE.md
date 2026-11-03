# Arquitectura

## Implementación actual

RONIN utiliza un Transformer causal decoder-only implementado en PyTorch. La arquitectura actual incorpora:

- **RoPE** para codificar posiciones sin una tabla de embeddings posicionales aprendida.
- **RMSNorm** en los bloques y en la salida.
- **SwiGLU** como red feed-forward.
- **GQA configurable** mediante `n_kv_heads`; por defecto se mantiene MHA (`n_kv_heads = n_heads`).
- Embeddings de tokens y proyección de salida con pesos compartidos.
- Atención causal mediante `torch.nn.functional.scaled_dot_product_attention`.

Los pesos se inicializan localmente con una distribución normal. El constructor no carga pesos preentrenados ni importa parámetros de los modelos auxiliares.

## Dimensiones y configuración

Los campos `n_kv_heads`, `d_ff`, `rope_theta` y `rms_norm_eps` se definen en `ModelConfig`. La dimensión de cabeza debe ser par para RoPE y `n_heads` debe ser divisible por `n_kv_heads`. El contador analítico de parámetros refleja las proyecciones GQA, las tres matrices SwiGLU, las normalizaciones y el embedding compartido.

El límite de contexto se valida en el modelo. RoPE calcula las frecuencias en función de las posiciones de la secuencia de entrada; no se conserva una tabla de embeddings posicionales aprendida.

## Invariantes

- Máscara causal decoder-only: una posición no puede atender a tokens futuros.
- Límite explícito de longitud de contexto.
- Formas estables: entrada `[lote, secuencia]`, logits `[lote, secuencia, vocabulario]`.
- Entropía cruzada para predecir el siguiente token.
- Pesos compartidos entre embeddings y proyección de salida.
- Inicialización aleatoria local del estudiante.
- Todo cambio de arquitectura requiere pruebas de dimensiones, causalidad, gradientes y recuento de parámetros.

## Decisiones de integración

El diseño de referencia en NumPy se ha utilizado como especificación conceptual, no como backend alternativo. Las operaciones diferenciables se implementan con PyTorch autograd; no se incorpora backpropagation manual.

El tokenizador BPE de referencia no se integra: su decodificador reconstruye los tokens fusionados a partir de claves centinela en lugar de conservar los bytes originales, por lo que no garantiza round-trip UTF-8. Se mantiene el tokenizador de bytes reversible existente hasta disponer de un BPE corregido y probado.

El pipeline de datos de referencia tampoco se copia como paquete paralelo: RONIN ya tiene lectura de corpus, validación de procedencia y lotes PyTorch. Las utilidades duplicadas se incorporarán solo cuando cubran una carencia real y tengan pruebas de integridad de datos.

## Límites actuales

GQA está implementada como proyección y repetición de cabezas KV en la ruta de atención; no equivale a un servidor de inferencia con caché KV incremental. No se declara paged attention, batching continuo, planificación de peticiones ni entrenamiento distribuido hasta que existan implementaciones y pruebas específicas.

Los modelos auxiliares MIT se ejecutan fuera de RONIN. Su única salida admitida para el estudiante son ejemplos de texto con procedencia registrada; sus pesos nunca se reutilizan.
