# RONIN-IA

**Un modelo propio. Un pipeline reproducible. Un corpus trazable.**

RONIN es un modelo causal Transformer implementado en PyTorch. El modelo operativo fijado en `main` es **RONIN-tiny-seed202-500-001**: 9.922.880 parámetros, RoPE, RMSNorm, SwiGLU, GQA y tokenización byte-v1.

## Modelo principal

- Base: checkpoint anterior de `main`, SHA-256 de pesos `5aa7cd5a8188784b9fbf2e0c0454b6504d32e2188e3ac0291a0a255d88bce49e`.
- Entrenamiento: 500 pasos adicionales de next-token prediction, semilla 202, 128.000 tokens, CPU con 2 hilos.
- Corpus: 9.108 documentos admitidos (literatura española, Mathlib4 y 2 documentos NASA revisados individualmente); sin preguntas, QA sintético ni tutor.
- Checkpoint de origen: SHA-256 `86d7d97360f1eb0ac35e9dc12f69c366101629641115ba1c2a1341b2b7d257ae`.
- Run: [GitHub Actions #42071401130](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42071401130).
- Artefacto de origen: `ronin-corpus-seed-202-500steps-42071401130`. El workflow de fijación extrae y valida el state_dict y lo versiona como `weights/ronin-main.pt`; el manifiesto `weights/main-model.json` conserva hashes y procedencia.

### Evaluación pareada antes/después

| Métrica | Main anterior | Seed 202 | Cambio |
|---|---:|---:|---:|
| Validación interna BPB | 4,4189 | 3,8783 | -12,23 % |
| Validación interna PPL | 21,3904 | 14,7058 | -31,25 % |
| MMLU-Pro validation | 5/50 (10 %) | 5/50 (10 %) | 0 pp |

El screening MMLU-Pro usó los mismos 50 IDs, revisión `b189ec765aa7ed75c8acfea42df31fdae71f97be`, selección estratificada determinista y cobertura del 100 %. La muestra es pequeña (cada acierto equivale a 2 puntos porcentuales), pertenece al split `validation` y **no es el protocolo oficial ni una certificación de razonamiento**. El candidato no mejoró los aciertos MMLU-Pro; la mejora observada corresponde a predicción de texto en la validación interna.

Por decisión del proyecto, este checkpoint queda fijado como **base operativa de los próximos experimentos**, no como una afirmación de superioridad general.

### Puerta obligatoria para cada ciclo de 500 pasos

El workflow `main-native-no-tutor-holdout.yml` impone una evaluación pareada antes de permitir entrenamiento:

1. Carga y verifica el checkpoint de `main`; registra su SHA-256.
2. Evalúa antes del entrenamiento un mínimo de 50 preguntas de MMLU-Pro `validation`, seleccionadas de forma estratificada y determinista.
3. Exige cobertura del 100 %; si el holdout previo está incompleto, el ciclo aborta **antes de calcular gradientes**.
4. Ejecuta exactamente 500 pasos sobre el corpus admitido, sin preguntas, QA sintético ni tutor.
5. Guarda el checkpoint candidato y su SHA-256.
6. Evalúa los mismos IDs, revisión, split y configuración. Si cambia la muestra o falta cobertura, el candidato queda rechazado y el workflow falla.
7. Registra aciertos, accuracy, resultados por dominio, IDs de predicciones cambiadas, nuevos aciertos y regresiones.
8. Registra BPB/PPL en la misma validación interna como métricas secundarias.

Cada artefacto incluye los informes before/after y la configuración del holdout. No se promociona automáticamente ningún candidato. Una mejora de BPB/PPL no se interpreta como mejora de razonamiento si el holdout de preguntas no la respalda.

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

El ciclo oficial sin tutor está en [main-native-no-tutor-holdout.yml](.github/workflows/main-native-no-tutor-holdout.yml). Recupera los pesos fijados en `main`, verifica los corpus admitidos, mide el modelo antes, ejecuta fine-tuning nativo sin tutores y vuelve a medir exactamente los mismos holdouts. Cada ejecución produce un candidato; la promoción requiere revisión explícita.

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
