# Modelos auxiliares locales y generación de corpus

RONIN aprende siempre desde una inicialización aleatoria. Los tutores solo aportan texto; sus pesos nunca se copian al estudiante.

## Modelos admitidos

| Alias | Repositorio | Licencia declarada |
|---|---|---|
| gpt2 | https://huggingface.co/openai-community/gpt2 | MIT |
| gpt-neo-125m | https://huggingface.co/EleutherAI/gpt-neo-125m | MIT |
| phi-4-mini-instruct | https://huggingface.co/microsoft/Phi-4-mini-instruct | MIT |

El descargador vuelve a consultar los metadatos y cancela si la licencia del modelo no es exactamente MIT. Fija una revisión inmutable y calcula SHA-256 de los archivos. Al cargar el tutor, RONIN vuelve a verificar el inventario completo y cada hash; rechaza archivos ausentes, inesperados, alterados o rutas inseguras. **La licencia MIT del modelo no se atribuye automáticamente al texto que genere.**

Phi-4-mini-instruct es el tutor principal para las nuevas pruebas: 3,8B parámetros, ajuste instruct, soporte declarado para español y otros 23 idiomas. Su licencia publicada es MIT. Se carga con la implementación Phi-3 integrada en Transformers 4.53.3, sin ejecutar código Python remoto del repositorio. El workflow fija la combinación recomendada por la ficha del modelo: PyTorch 2.5.1, Transformers 4.53.3, Hugging Face Hub 0.36.0 y Accelerate 1.3.0. El descargador fija el commit, omite los archivos de código del modelo y el cargador verifica los pesos y el resto del inventario antes de usarlos. Sigue siendo principalmente entrenado en inglés y puede equivocarse; no se debe tratar como experto ni como fuente de verdad. GPT-2 y GPT-Neo 125M se conservan como líneas base pequeñas. Sus salidas son propuestas de tutor, no etiquetas certificadas ni hechos verificados. Requieren revisión, filtrado, deduplicación y comprobación de derechos antes de incorporarse a un entrenamiento.

## Descargar una vez en el equipo local

    python -m pip install -e '.[teachers]'
    python scripts/download_teacher_models.py --model gpt2
    python scripts/download_teacher_models.py --model gpt-neo-125m
    python scripts/download_teacher_models.py --model phi-4-mini-instruct

Los pesos y manifiestos quedan en models/teachers/, excluido de Git. Las generaciones posteriores pueden cargarlos desde disco sin repetir la descarga.

## Currículo multidominio y REF

El currículo determinista cubre matemáticas, física, química, biología y salud pública, informática, IA, historia, filosofía y lógica, economía, derecho, lingüística y literatura, criptografía, estadística, clima, arte e ingeniería. Recorre todos los dominios antes de repetir un tema.

Cada instrucción pide separar evidencia, inferencia e hipótesis y propone una respuesta estructurada con los ejes de REF: clase epistemológica, tipo de afirmación, género y estado de codificación. También exige límites, incertidumbre, posible refutación y qué evidencia cambiaría la conclusión.

Esto no convierte la salida en una anotación REF válida automáticamente. La generación del tutor no sustituye validación estructural, revisión humana ni adjudicación entre anotadores. En particular, «decoded» exige evidencia documentada y una cifra de confianza generada no equivale a calibración medida.

## Caché de GitHub Actions

El workflow manual «Preparar caché de tutores locales» descarga y verifica GPT-2, GPT-Neo 125M y Phi-4 mini instruct en un runner público y guarda models/teachers/ en la caché de Actions. Se ejecuta desde la pestaña Actions o automáticamente al integrar cambios en el descargador, el cargador, sus dependencias o el propio workflow. Las siguientes ejecuciones pueden restaurarla; GitHub puede desalojar cachés antiguas por sus políticas de retención, así que el descargador siempre debe poder reconstruirlas.

La caché acelera trabajos de Actions; no copia los modelos al ordenador local del operador. Los pesos no se versionan ni se publican como artefactos.

## Generación local

Genera lotes amplios y reproducibles con cada tutor, por separado:

    python scripts/generate_teacher_data.py --model-dir models/teachers/gpt2 --count 500 --device auto --max-new-tokens 256 --seed 1337 --output artifacts/teacher/gpt2.jsonl
    python scripts/generate_teacher_data.py --model-dir models/teachers/gpt-neo-125m --count 500 --device auto --max-new-tokens 256 --seed 2027 --output artifacts/teacher/gpt-neo-125m.jsonl
    python scripts/generate_teacher_data.py --model-dir models/teachers/phi-4-mini-instruct --count 500 --device auto --max-new-tokens 256 --seed 404 --output artifacts/teacher/phi-4-mini-instruct.jsonl

El dispositivo auto utiliza CUDA si está disponible y CPU en caso contrario. Los registros generados deben revisarse antes de entrenar. No se deben mezclar sin más respuestas contradictorias: conservar identidad del tutor, comparar desacuerdos y priorizar ejemplos verificables.

Preparación de cada lote:

    python scripts/prepare_teacher_corpus.py --input artifacts/teacher/gpt2.jsonl --output artifacts/teacher/gpt2.txt
    python scripts/prepare_teacher_corpus.py --input artifacts/teacher/gpt-neo-125m.jsonl --output artifacts/teacher/gpt-neo-125m.txt

El corpus generado por Phi-4 puede incorporarse como augmentación experimental después de la auditoría estructural REF. Esa auditoría solo valida formato y etiquetas; no comprueba verdad, citas ni calibración. Los registros identifican la licencia del modelo por separado y dejan la licencia de la salida como no atribuida; los textos generados no se publican como artefactos. Antes de redistribuirlos hay que revisar por separado sus derechos y condiciones. Las salidas conservan siempre la identidad y revisión del tutor, y no sustituyen la adjudicación humana. Para una destilación seria, añadir tutores especializados por dominio con licencias verificadas, evaluación cruzada y un conjunto REF anotado por personas.

## Separación tutor-estudiante

- Los pesos del tutor solo se cargan en el proceso generador.
- RONIN se construye con inicialización aleatoria.
- El entrenador solo recibe texto tokenizado.
- No se realiza fine-tuning, fusión ni destilación de parámetros.


La revisión de Phi-4 queda fijada en `cfbefacb99257ffa30c83adab238a50856ac3083`; no se descarga la rama móvil `main`. La carga usa el soporte Phi-3/Phi-4 integrado en Transformers 4.53.3 y mantiene `trust_remote_code=False`.
