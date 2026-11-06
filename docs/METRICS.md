# Métricas, tokens y comparabilidad

## Principio

No se comparan números si cambian simultáneamente arquitectura, datos, exposición, split o protocolo. Un tokenizador común no hace comparables dos entrenamientos con presupuestos distintos.

## Tabla de regímenes

| Régimen | Parámetros | Pasos | Evaluación publicada | Qué significa |
|---|---:|---:|---|---|
| Main tiny seed95 | 9.922.880 | 100 | BPB 4,5654→4,3373; PPL 23,6764→20,2137; MMLU-Pro validation 5/50→7/50 | Línea base operativa; screening |
| Ganador 10k | 9.922.880 | 10.000 | BPB 3,8152→2,9798; MMLU-Pro test 1.295/12.032→1.314/12.032 | Régimen histórico anterior a la expansión |
| Drosophila | 100.900.160 | 500 tras expansión | MMLU-Pro validation 5/64→5/64 | Candidato; no hay BPB/PPL equivalente publicado |

Los BPB/PPL de main pertenecen a validación interna del régimen de 100 pasos. Los BPB del ganador 10k pertenecen a otra etapa y evaluación. Drosophila no tiene en su manifiesto BPB/PPL pareados comparables. No se debe fabricar un delta entre esas filas.

## Tokens procesados en Drosophila

El script scripts/expand_and_train_10x.py obtiene el perfil tiny, con longitud de contexto 128. La configuración de continuación fija:

- batch size = 1;
- gradient accumulation = 1;
- pasos = 500;
- tokenizer byte-v1;
- muestreo de ventanas aleatorias con reemplazo.

Exposición nominal:

**500 × 1 × 1 × 128 = 64.000 posiciones de entrada.**

El entrenador predice el siguiente token de cada posición. La cifra no representa 64.000 tokens únicos: las ventanas pueden solaparse y repetirse. Tampoco es una época completa sobre los 685.023.414 bytes declarados.

## Tokens por parámetro: dos ratios distintos

Para Drosophila:

- Pool de corpus / parámetros: **685.023.414 / 100.900.160 ≈ 6,79 bytes por parámetro**.
- Posiciones nominales de la continuación / parámetros: **64.000 / 100.900.160 ≈ 0,000634 posiciones por parámetro**.

El primer ratio describe el tamaño del pool de bytes frente al tamaño del modelo. No es tokens vistos. El segundo aproxima las posiciones muestreadas durante los 500 pasos publicados; no cuenta tokens únicos ni el entrenamiento previo de 10.000 pasos.

La heurística Chinchilla (~20 tokens de entrenamiento por parámetro) se refiere al presupuesto de entrenamiento, no al tamaño total del corpus disponible. No se usa aquí para declarar un óptimo ni para evaluar un fine-tuning aislado. La etapa base de 10.000 pasos necesita su propio recuento verificable de tokens procesados antes de calcular una exposición acumulada.

## Evidencia MMLU-Pro

- Main tiny: 50 preguntas del split validation; 5/50→7/50. SCREENING_ONLY.
- Drosophila: 64 preguntas del split validation, mismos IDs; 5/64→5/64. MODEL_ORGANISM_ONLY + SCREENING_ONLY. No certifica razonamiento general.
- Ganador 10k: 12.032 preguntas del split test; 1.295→1.314 correctas. Es evidencia del checkpoint de 9,9M anterior a la expansión, no de Drosophila.

El protocolo de RONIN puntúa la probabilidad del siguiente byte de las opciones A–J. No es el protocolo oficial CoT de MMLU-Pro ni es comparable directamente con su leaderboard. El uso repetido del mismo test para seleccionar candidatos introduce riesgo de contaminación por selección, aunque no haya gradientes sobre test.

## Variabilidad

La continuación Drosophila publicada tiene n=1. No se calcula media ni desviación estándar. Para hablar de señal entre seeds, ejecutar al menos cuatro réplicas comparables desde el mismo checkpoint base, mismo corpus/hash, mismos pasos, mismo protocolo y seeds predefinidas. Publicar cada resultado individual, media, desviación estándar y todas las curvas; no mostrar solo el ganador.
