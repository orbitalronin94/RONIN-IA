# RONIN-IA

**Un modelo propio. Un pipeline reproducible. Un corpus trazable.**

RONIN es un modelo causal Transformer implementado en PyTorch. El modelo operativo fijado en `main` es **RONIN-tiny-seed202-500-001**: 9.922.880 parámetros, RoPE, RMSNorm, SwiGLU, GQA y tokenización byte-v1.

## Modelo principal

- Base: checkpoint anterior de `main`, SHA-256 de pesos `5aa7cd5a8188784b9fbf2e0c0454b6504d32e2188e3ac0291a0a255d88bce49e`.
- Entrenamiento: 500 pasos adicionales de next-token prediction, semilla 202, 128.000 tokens, CPU con 2 hilos.
- Corpus usado para crear este checkpoint: 9.108 documentos admitidos (literatura española, Mathlib4 y NASA revisado); no se le atribuye el corpus ampliado posterior.
- Inventario train-scoped disponible para los siguientes ciclos: **286.468 unidades y 684.738.932 bytes UTF-8**; incluye 270.244 segmentos de traducción CoVoST 2 en inglés/catalán. Sus particiones validation/test permanecen excluidas.
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

Por decisión del proyecto, este checkpoint queda fijado como **base operativa de los próximos experimentos**, no como una afirmación de superioridad general. Los ciclos siguientes medirán el mismo holdout antes y después, conservarán el checkpoint de partida y no promocionarán automáticamente candidatos.

## Tutor local MoE

El workflow está preparado para descargar **Qwen3-30B-A3B Q4_K_M** en el almacenamiento persistente `tool_cache` de un runner propio y ejecutar inferencia local con `llama.cpp` CPU, sin Ollama. El GGUF **todavía no está verificado como descargado**: hace falta un runner Linux x64 con etiqueta `ronin-32gb-cpu`, 28 GiB de RAM disponible y 55 GiB libres. El pipeline permite hasta 100 trazas; son generaciones del tutor, no pasos de optimizador del estudiante. Las trazas quedan sin admitir y nunca se ingieren automáticamente. Consulta [docs/TUTOR_MOE_LOCAL.md](docs/TUTOR_MOE_LOCAL.md).

## Experimento de 100 corridas sobre el corpus actual

La PR ejecuta **100 candidatos independientes**, semillas 1–100, con **100 pasos de optimizador cada uno** (10.000 actualizaciones agregadas). Todos parten del checkpoint operativo de `main` (**9.922.880 parámetros**, no el experimento de 95,5 M) y se comparan con los mismos 50 IDs de MMLU-Pro `validation`, además de la validación interna de texto. Se usan particiones train admitidas de literatura, Mathlib4, NASA revisado, Papers propios, ScienceVerse CC-BY y CoVoST 2 CC0. No se usa tutor. Se conservan los informes completos y los tres mejores checkpoints; no hay promoción automática.

**Referencia previa, no equivalente al experimento 100×100:** la run [#42120055946](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42120055946) ejecutó la semilla 202 durante 500 pasos. En su muestra fija de 50 preguntas validation pasó de 5/50 a 7/50 (+4 puntos porcentuales); BPB interno pasó de 4,5654 a 4,0541 y la loss final fue 2,77316. Es un screening pequeño, no el benchmark oficial ni una prueba de mejora general. La nueva run [#42121731925](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42121731925) es la ejecución 100×100 y sus resultados solo se publicarán cuando termine.

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
