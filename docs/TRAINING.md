# Entrenamiento del modelo RONIN

## Modelo de partida

El ciclo principal parte de **RONIN-tiny-main-001**, checkpoint de 9.922.880 parámetros y paso 1.000. Su SHA-256 está fijado en `weights/main-model.json`. El entrenamiento no reconstruye el modelo desde cero: carga estrictamente sus pesos y conserva una copia de referencia para la evaluación anterior.

## Ciclo nativo sin tutores

El workflow operativo es [main-native-no-tutor-holdout.yml](../.github/workflows/main-native-no-tutor-holdout.yml).

1. Descarga el checkpoint main y verifica su hash.
2. Recupera únicamente particiones train admitidas y verifica manifiestos, identificadores, bytes y SHA-256.
3. Ensambla el corpus sin incluir validation ni test.
4. Evalúa el checkpoint base en los holdouts fijos.
5. Ejecuta fine-tuning nativo con PyTorch, sin modelos tutores ni datos sintéticos generados por terceros.
6. Evalúa el candidato con exactamente los mismos holdouts y publica pesos e informes como artefactos.
7. Deja el candidato pendiente de revisión; nunca sustituye automáticamente los pesos main.

El corte de corpus fijado por el workflow contiene 9.108 documentos: 608 de literatura española, 8.498 de Mathlib4 y 2 NASA NTRS revisados individualmente. Son 237.957.184 bytes de origen. ScienceVerse, Papers del propietario y el resto de NASA no forman parte de esta mezcla de entrenamiento.

## Entrenamiento local

Python 3.11, PyTorch 2.2 o posterior:

```bash
python -m pip install -e '.[dev]'
python scripts/train_text.py \
  --text /ruta/corpus-autorizado.txt \
  --profile tiny \
  --steps 500 \
  --seed 20261106 \
  --init-checkpoint weights/ronin-main.pt \
  --device cpu \
  --num-threads 2 \
  --checkpoints checkpoints/candidate
```

El archivo de entrada debe contener solo texto UTF-8 autorizado para entrenamiento. El script permite inicializar desde un checkpoint y guarda el checkpoint final. Los informes de throughput pueden escribirse con `--metrics-out`.

## Entrenador

- AdamW.
- Warm-up lineal y scheduler coseno.
- Acumulación de gradientes y clipping global.
- FP32 en CPU; BF16/FP16 cuando el dispositivo lo soporta.
- Detección de pérdidas y gradientes no finitos.
- Checkpoints atómicos con pesos, estado del optimizador, escalador, paso y estados aleatorios.
- Reanudación con validación estricta de configuración.

## Reglas de datos

Los datos se leen desde `data/datasets/`. La carpeta distingue corpus admitidos, candidatos, particiones y registros de derechos. Descargado no significa entrenable: solo se usa una partición con derechos compatibles, payload íntegro, hash verificado y asignación train explícita. Validation y test quedan fuera de los gradientes.

## Pesos

La identidad del modelo principal está en `weights/main-model.json`. El workflow [pin-main-weights.yml](../.github/workflows/pin-main-weights.yml) extrae los tensores del artefacto histórico, verifica el hash del checkpoint fuente y versiona `weights/ronin-main.pt` como `state_dict` compacto. También publica `ronin-main-weights-v1` como copia de recuperación. No se confunde el manifiesto con el archivo de tensores.
