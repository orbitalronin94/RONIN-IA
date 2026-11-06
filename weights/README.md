# Pesos del modelo de referencia

El checkpoint versionado en `main` es **RONIN-tiny-seed95-100-001**, con 9.922.880 parámetros. Este directorio contiene el paquete compacto PyTorch `ronin-main.pt` (sin estado del optimizador) y el manifiesto de identidad/procedencia.

- **Pesos:** [ronin-main.pt](ronin-main.pt)
- **Manifiesto:** [main-model.json](main-model.json)
- **SHA-256 del paquete:** `4fb699cf3633ce610f66f2066ce182ceb957b2b0bead2b97c42cccf7f7021d11`
- **Tamaño:** 39.719.989 bytes.
- **Checkpoint de origen:** 100 pasos, seed 95.
- **Procedencia:** [GitHub Actions #42121731925](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42121731925).

El manifiesto es la fuente de verdad para arquitectura, número de parámetros, checkpoint de origen, hashes, evaluación y política de promoción.

Los experimentos posteriores —incluido el candidato de 10.000 pasos— no sustituyen automáticamente estos pesos. Sus checkpoints se publican como artefactos de Actions hasta que exista una decisión explícita de promoción y se actualicen juntos el paquete y el manifiesto.

No confundas el inventario actual de datasets con el corpus histórico usado para crear este checkpoint. Cada manifiesto de experimento registra el corte real de datos utilizado.
