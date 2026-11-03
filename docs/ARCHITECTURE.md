# Arquitectura

## Implementación actual

RONIN comienza con un modelo de lenguaje Transformer causal de tipo decoder-only, implementado en PyTorch. Los embeddings de tokens y la proyección de salida comparten pesos. La atención es causal y utiliza la implementación escalada de atención de PyTorch. Los parámetros se inicializan localmente con una distribución normal; al construir el modelo no se carga ningún checkpoint externo.

El tokenizador inicial representa el texto como bytes UTF-8 reversibles (identificadores 0–255). Es una base provisional para probar la canalización, no el tokenizador definitivo. La dimensión del vocabulario del tokenizador y la del modelo deben coincidir en todo experimento ejecutable.

## Perfiles de escala

Los perfiles se centralizan en `ronin/config.py`. Todos utilizan la misma implementación `RoninLM`. Los recuentos de parámetros se deben calcular a partir de módulos instanciados. Los tamaños objetivo del README son aspiraciones y no deben presentarse como recuentos medidos.

## Invariantes

- Máscara causal decoder-only; no puede filtrarse información de tokens futuros.
- Límite explícito de longitud de contexto.
- Formas estables: entrada `[lote, secuencia]`, logits `[lote, secuencia, vocabulario]`.
- Objetivo de entropía cruzada para predecir el siguiente token.
- El uso compartido de pesos entre embeddings y proyección de salida está probado.
- Todo cambio de arquitectura requiere pruebas de parámetros, dimensiones, causalidad y gradientes.

## Ampliaciones previstas

Las codificaciones posicionales rotatorias, atención agrupada por consultas, variantes configurables de redes feed-forward, checkpointing de activaciones y entrenamiento distribuido todavía no forman parte de la implementación inicial. Deben añadirse mediante opciones de configuración probadas, sin bifurcar la canalización de entrenamiento por perfil.

Los modelos auxiliares MIT se ejecutan fuera de RONIN. Su única salida admitida para el estudiante son ejemplos de texto con procedencia registrada; nunca se reutilizan sus tensores de pesos.
