# Arquitectura RONIN

## Modelo principal

RONIN-tiny-main-001 es un Transformer causal decoder-only implementado en PyTorch, con 9.922.880 parámetros. Su configuración usa:

- RoPE para codificación posicional.
- RMSNorm en bloques y salida.
- SwiGLU como red feed-forward.
- Grouped Query Attention (GQA).
- Embeddings y proyección de salida con pesos compartidos.
- Atención causal mediante `scaled_dot_product_attention`.
- Tokenizador reversible byte-v1 de 256 símbolos.

El perfil tiny se define en `ronin/config.py` y `configs/tiny.yaml`. El checkpoint principal se identifica por el hash de `weights/main-model.json`.

## Invariantes

- Ninguna posición puede atender a tokens futuros.
- Longitud de contexto validada explícitamente.
- Entrada `[batch, sequence]` y logits `[batch, sequence, vocab]`.
- Predicción autoregresiva del siguiente byte.
- Inicialización aleatoria propia; el checkpoint main se carga solo como punto de partida del entrenamiento.
- Los cambios de arquitectura requieren pruebas de dimensiones, causalidad, gradientes y recuento de parámetros.

## Límites

El perfil tiny es un modelo experimental pequeño. No se atribuye razonamiento general por el mero hecho de que el pipeline entrene y evalúe correctamente. No se incluyen tutores, pesos de terceros ni servicios externos en el ciclo principal.
