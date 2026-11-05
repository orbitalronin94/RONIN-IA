# Pesos del modelo principal

El modelo operativo actual es `RONIN-tiny-seed202-500-001`, fijado desde el checkpoint de 500 pasos de la semilla 202. El fichero `ronin-main.pt` contiene el paquete compacto de pesos PyTorch (sin estado del optimizador).

- Checkpoint de origen: SHA-256 `86d7d97360f1eb0ac35e9dc12f69c366101629641115ba1c2a1341b2b7d257ae`.
- Paquete versionado: 39.719.989 bytes; SHA-256 `ee250e1b0e99f2983267ae030dd7d589395e25de028bb052dbff33894c8fe4b7`.
- Procedencia: [GitHub Actions #42071401130](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42071401130).
- Validación de extracción y publicación: [GitHub Actions #42074008702](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42074008702).

El manifiesto `main-model.json` conserva el paso de origen, arquitectura, evaluación pareada, procedencia y hashes. El workflow `.github/workflows/pin-main-weights.yml` recupera el artefacto histórico, verifica el SHA-256 del checkpoint, carga el state_dict con comprobación estricta de arquitectura y actualiza el paquete y el manifiesto en `main`.

Los ciclos posteriores deben cargar `weights/ronin-main.pt`, medir el holdout antes y después con idénticos IDs y no sustituir los pesos de `main` automáticamente.
