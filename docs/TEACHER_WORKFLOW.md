# Modelos auxiliares locales y generación de corpus

RONIN aprende siempre desde una inicialización aleatoria. Los tutores solo aportan texto; sus pesos nunca se copian al estudiante.

## Modelos admitidos

| Alias | Repositorio | Licencia declarada |
|---|---|---|
| gpt2 | https://huggingface.co/openai-community/gpt2 | MIT |
| gpt-neo-125m | https://huggingface.co/EleutherAI/gpt-neo-125m | MIT |

El descargador vuelve a consultar los metadatos y cancela si la licencia no es exactamente mit. Fija una revisión inmutable y calcula SHA-256 de los archivos. Al cargar el tutor, RONIN vuelve a verificar el inventario completo y cada hash; rechaza archivos ausentes, inesperados, alterados o rutas inseguras.

Ambos modelos son pequeños y principalmente anglófonos. No se debe presuponer que generarán buen castellano, conocimiento experto ni juicios epistemológicos correctos. Sus salidas son propuestas de tutor, no etiquetas certificadas ni hechos verificados. Requieren revisión, filtrado, deduplicación y comprobación de derechos antes de incorporarse a un entrenamiento.

## Descargar una vez en el equipo local

    python -m pip install -e '.[teachers]'
    python scripts/download_teacher_models.py --model gpt2
    python scripts/download_teacher_models.py --model gpt-neo-125m

Los pesos y manifiestos quedan en models/teachers/, excluido de Git. Las generaciones posteriores pueden cargarlos desde disco sin repetir la descarga.

## Currículo multidominio y REF

El currículo determinista cubre matemáticas, física, química, biología y salud pública, informática, IA, historia, filosofía y lógica, economía, derecho, lingüística y literatura, criptografía, estadística, clima, arte e ingeniería. Recorre todos los dominios antes de repetir un tema.

Cada instrucción pide separar evidencia, inferencia e hipótesis y propone una respuesta estructurada con los ejes de REF: clase epistemológica, tipo de afirmación, género y estado de codificación. También exige límites, incertidumbre, posible refutación y qué evidencia cambiaría la conclusión.

Esto no convierte la salida en una anotación REF válida automáticamente. La generación del tutor no sustituye validación estructural, revisión humana ni adjudicación entre anotadores. En particular, «decoded» exige evidencia documentada y una cifra de confianza generada no equivale a calibración medida.

## Caché de GitHub Actions

El workflow manual «Preparar caché de tutores locales» descarga y verifica ambos modelos en un runner público y guarda models/teachers/ en la caché de Actions. Se ejecuta desde la pestaña Actions o automáticamente al integrar cambios en el descargador, el cargador, sus dependencias o el propio workflow. Las siguientes ejecuciones pueden restaurarla; GitHub puede desalojar cachés antiguas por sus políticas de retención, así que el descargador siempre debe poder reconstruirlas.

La caché acelera trabajos de Actions; no copia los modelos al ordenador local del operador. Los pesos no se versionan ni se publican como artefactos.

## Generación local

Genera lotes amplios y reproducibles con cada tutor, por separado:

    python scripts/generate_teacher_data.py --model-dir models/teachers/gpt2 --count 500 --device auto --max-new-tokens 256 --seed 1337 --output artifacts/teacher/gpt2.jsonl
    python scripts/generate_teacher_data.py --model-dir models/teachers/gpt-neo-125m --count 500 --device auto --max-new-tokens 256 --seed 2027 --output artifacts/teacher/gpt-neo-125m.jsonl

El dispositivo auto utiliza CUDA si está disponible y CPU en caso contrario. Los registros generados deben revisarse antes de entrenar. No se deben mezclar sin más respuestas contradictorias: conservar identidad del tutor, comparar desacuerdos y priorizar ejemplos verificables.

Preparación de cada lote:

    python scripts/prepare_teacher_corpus.py --input artifacts/teacher/gpt2.jsonl --output artifacts/teacher/gpt2.txt
    python scripts/prepare_teacher_corpus.py --input artifacts/teacher/gpt-neo-125m.jsonl --output artifacts/teacher/gpt-neo-125m.txt

Los tutores actuales sirven para probar el circuito y generar material preliminar; no son profesores expertos de todos los dominios. Para una destilación seria, añadir tutores especializados por dominio con licencias verificadas, evaluación cruzada y un conjunto REF anotado por personas.

## Separación tutor-estudiante

- Los pesos del tutor solo se cargan en el proceso generador.
- RONIN se construye con inicialización aleatoria.
- El entrenador solo recibe texto tokenizado.
- No se realiza fine-tuning, fusión ni destilación de parámetros.
