# RONIN-IA

**Un modelo propio. Un pipeline reproducible. Un corpus trazable.**

RONIN es un modelo causal Transformer implementado en PyTorch. La rama `main` fija como referencia **RONIN-tiny-main-001**: 9.922.880 parámetros, RoPE, RMSNorm, SwiGLU, GQA y tokenización byte-v1.

## Modelo principal

- Checkpoint: paso 1.000, entrenado desde inicialización aleatoria.
- Corpus de origen: 608 documentos de literatura española de dominio público.
- Evaluación literaria fija: BPB de **7,8684 a 2,8219** sobre 18 documentos de test y 65.536 tokens.
- SHA-256 del checkpoint: `a90a01a3e7f53e2e4aec1f0c1f0c137eedfe219f3fc3cc65f5eea827829d6f25`.
- Ejecución de origen: [GitHub Actions #42014728700](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42014728700).

El manifiesto de pesos se conserva en `weights/main-model.json`. El checkpoint completo se conserva como artefacto inmutable de GitHub Actions y se verifica por SHA-256 antes de cada ciclo. No se presenta el manifiesto como si contuviera los pesos.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `weights/` | Identidad, procedencia y hashes del modelo main y sus checkpoints |
| `data/datasets/` | Corpus, bibliotecas, particiones, manifiestos y registros de derechos |
| `ronin/` | Arquitectura, tokenizador, datos, entrenamiento y evaluación |
| `scripts/` | Entrada mínima para entrenar y evaluar |
| `configs/` | Configuración del modelo tiny |
| `.github/workflows/` | CI y ciclos reproducibles de entrenamiento |

Los corpus candidatos permanecen separados de los documentos habilitados para entrenamiento. Un documento no se considera entrenable por el mero hecho de estar descargado: se exige procedencia, derechos compatibles, integridad del payload y partición explícita. Los conjuntos de validación y test nunca se incorporan a los gradientes.

## Entrenar y evaluar

Requisitos: Python 3.11 y PyTorch 2.2 o posterior.

```bash
python -m pip install -e '.[dev]'
pytest -q
```

El ciclo oficial sin tutor está en [main-native-no-tutor-holdout.yml](.github/workflows/main-native-no-tutor-holdout.yml). Recupera el checkpoint principal, verifica los corpus de entrenamiento admitidos, mide el modelo antes, ejecuta fine-tuning nativo sin tutores y vuelve a medir exactamente los mismos holdouts. El resultado es un candidato: **no sustituye automáticamente los pesos de main**.

Para ejecutar entrenamiento local con un corpus UTF-8 autorizado:

```bash
python scripts/train_text.py --text /ruta/al/corpus.txt --profile tiny --steps 500
```

Para las métricas y el protocolo externo, consulta [MMLU-Pro y su protocolo de evaluación](docs/HOLDOUT_EXTERNO_MMLU_PRO.md).

## Principios

- **Modelo corto, método largo.** No se atribuye al modelo una capacidad que las mediciones no demuestren.
- **Sin tutores por defecto.** El estudiante aprende de corpus admitidos y verificables.
- **Mismo holdout antes y después.** Las comparaciones deben ser reproducibles y con cobertura declarada.
- **Los pesos mandan.** Se conserva la identidad criptográfica del checkpoint y se separan los candidatos del modelo principal.
- **Datos primero.** La adquisición, la admisión y la elegibilidad de entrenamiento son estados distintos.

## Aviso

> Sepan cuantos este repositorio vieren que aquí se hace escarnio de cuanto los doctos predicaron sobre acrecentar modelos. Non hay hueste de tarjetas gráficas, nin caudal de dineros, nin ley del escalado que valga. Hay un ingenio de cuarenta y cuatro millones que apenas distingue el saludo del mandado, y un artificio de trazas que non se rompe.
>
> Al modelo non le tengo ley, ca es ruin y él lo sabe. Al artificio se la tengo entera.
>
> Quien viniere por el modelo, tórnese por do vino, que aquí non hay sino el método. Quien viniere por las trazas, quédese, mas sepa desde luego que el método es largo y el modelo, corto. Non me pidáis que lo aderece, que quien se consuela con el modelo es porque non ha mirado las trazas.
