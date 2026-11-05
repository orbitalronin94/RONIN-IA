# Pesos del modelo principal

El checkpoint completo se conserva como artefacto GitHub Actions `ronin-main-weights-v1`, extraído del artefacto original y verificado por SHA-256. El manifiesto `main-model.json` fija identidad, arquitectura, ejecución de origen y hash. No se versiona una copia duplicada de varios gigabytes ni se confunde el manifiesto con los tensores.

El workflow `.github/workflows/pin-main-weights.yml` reconstruye el artefacto limpio desde la ejecución histórica y verifica el hash antes de publicarlo.
