# Pesos del modelo principal

Los pesos del modelo principal se versionan en `ronin-main.pt` como `state_dict` PyTorch (sin el estado del optimizador). El fichero conserva el paso de origen y se verifica por SHA-256 desde `main-model.json`. El checkpoint completo histórico queda como fuente inmutable de procedencia; los ciclos de fine-tuning reinician el optimizador deliberadamente.

El workflow `.github/workflows/pin-main-weights.yml` extrae los tensores del checkpoint original, comprueba su hash, genera el paquete compacto y lo incorpora a `main`.
