# RONIN-IA

**Un modelo propio. Un pipeline reproducible. Un corpus trazable.**

RONIN es un modelo causal Transformer implementado en PyTorch. El modelo operativo fijado en main es **RONIN-tiny-seed95-100-001**: 9.922.880 parámetros, RoPE, RMSNorm, SwiGLU, GQA y tokenización byte-v1.

## Modelo principal

- Base: RONIN-tiny de main, pesos SHA-256 ee250e1b0e99f2983267ae030dd7d589395e25de028bb052dbff33894c8fe4b7.
- Entrenamiento: 100 pasos adicionales de next-token prediction, semilla 95, 25.600 tokens, CPU; sin tutor ni preguntas de benchmark en los gradientes.
- Corpus: 286.468 unidades train-scoped y 684.738.932 bytes UTF-8 (literatura española, Mathlib4, NASA revisado, Papers propios, ScienceVerse CC-BY y CoVoST 2 CC0). Las particiones validation/test permanecen excluidas de los gradientes.
- Checkpoint de origen: SHA-256 161c5f414c5aa116b7461d76efd4dfbbffa9d6c72fe4da82cc6bae85f3f60409.
- Run: [GitHub Actions #42121731925](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42121731925).
- Artefacto de origen: ronin-corpus-100-runs-100-steps-42121731925; el workflow valida la arquitectura y extrae únicamente los pesos del modelo, sin estado del optimizador.

### Evaluación pareada antes/después

| Métrica | Main anterior | Seed 95 | Cambio |
|---|---:|---:|---:|
| Validación interna BPB | 4,5654 | 4,3373 | -4,99 % |
| Validación interna PPL | 23,6764 | 20,2137 | -14,63 % |
| MMLU-Pro validation | 5/50 (10 %) | 7/50 (14 %) | +4 pp |

El cribado MMLU-Pro utilizó los mismos 50 IDs del split validation, revisión b189ec765aa7ed75c8acfea42df31fdae71f97be, selección estratificada determinista y cobertura del 100 %. La muestra no es el conjunto completo ni el protocolo oficial. Cada acierto equivale a 2 puntos porcentuales; por tanto, el resultado **no certifica razonamiento general** y requiere evaluación independiente en un holdout no usado para seleccionar la semilla.

Por decisión explícita del propietario del proyecto, seed 95 queda fijada como **base operativa de main** tras el screening de 100 semillas. La promoción no cambia la clasificación de la evidencia: el resultado sigue siendo SCREENING_ONLY, no una afirmación de superioridad general. Se conservan el hash del checkpoint, el hash de los pesos compactos y la procedencia en weights/main-model.json.

El corpus train-scoped ampliado no se atribuye retroactivamente a los entrenamientos anteriores. Los siguientes ciclos medirán el mismo holdout antes y después, conservarán el checkpoint de partida y no promocionarán candidatos automáticamente.

## Estructura del repositorio

| Ruta | Contenido |
|---|---|
| `weights/` | Identidad, procedencia, hashes y pesos del modelo main |
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

El ciclo oficial sin tutor está en [main-native-no-tutor-holdout.yml](.github/workflows/main-native-no-tutor-holdout.yml) (ejecución manual). Recupera los pesos fijados en `main`, verifica los corpus admitidos y añade CoVoST 2 cuando su payload scoped ya está materializado; mide el modelo antes, ejecuta fine-tuning nativo sin tutores y vuelve a medir exactamente los mismos holdouts. El checkpoint actual no incorpora retroactivamente este corpus ampliado. Cada ejecución produce un candidato; la promoción requiere revisión explícita.

El benchmark de desarrollo MMLU-Pro puede ejecutarse con muestras de screening o con el split completo. Una muestra pequeña sirve para cribar, no para declarar capacidad general. El test oficial se mantiene separado de entrenamiento y selección.

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
