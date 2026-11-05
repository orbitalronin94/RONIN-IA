# Ciclo socrático Qwen sobre el checkpoint main

Fecha: 2026-11-05

## Alcance autorizado

Este ciclo no modifica G-0 ni convierte bibliotecas pendientes en datos entrenables. Consume únicamente:
- la partición train de ronin-spanish-public-domain-literature-v2 (608 documentos, SHA-256 fijado en el manifiesto);
- ejemplos generados por Qwen/Qwen3-8B GGUF Q4_K_M desde MMLU-Pro validation, admitidos solo si la respuesta coincide con la etiqueta gold y existe una explicación breve verificable.

NASA NTRS (775 documentos scoped) y los nueve Papers propios quedan fuera de este ciclo mientras sus manifiestos sigan indicando training_eligible: false. El G-0 global continúa en FAIL. La autorización es exclusivamente por la partición literaria que ya tiene admisión scoped; no es un PASS global.

## Tutor

- Base: Qwen/Qwen3-8B
- Cuantización: GGUF Q4_K_M
- Repositorio de cuantización: Qwen/Qwen3-8B-GGUF
- Licencia esperada: Apache-2.0
- Verificación: revisiones del modelo base y repositorio GGUF, manifiesto y SHA-256 del archivo.
- Ejecución local con llama.cpp, trust_remote_code=false.
- Los pesos del tutor nunca se importan al estudiante. No se solicita ni conserva cadena privada de pensamiento.
- La licencia de las salidas generadas no se presume. El JSONL de tutor no se publica; el artefacto de experimento conserva solo resumen, manifiesto de mezcla y métricas.

## Entrenamiento y evaluación

1. Recuperar el checkpoint actual de main fijado por SHA-256 y el artefacto train de 608 documentos.
2. Verificar el manifiesto scoped, la elegibilidad de la partición y el hash del payload.
3. Crear una validación interna determinista a partir del train admitido, sin leer los splits legacy validation/test.
4. Generar 48 ejemplos desde MMLU-Pro validation con Qwen; exigir al menos ocho explicaciones aceptadas y 25% de respuestas gold correctas.
5. Mezclar el train documental interno con las explicaciones aceptadas (repetición controlada de 32 veces).
6. Fine-tuning incremental de 500 pasos desde el checkpoint de main, tasa conservadora.
7. Evaluar antes/después sobre la validación interna, la batería multidominio y el test MMLU-Pro completo, sin usar el test para generar datos ni gradientes.
8. Comparar hashes, revisión, IDs y cobertura idénticos. No hay promoción automática.

La muestra de 140 preguntas de MMLU-Pro test ya se utilizó en un experimento anterior. Este ciclo mide el split completo para mayor estabilidad, pero esas 140 preguntas no deben presentarse como un holdout nunca visto. El candidato queda sin promover hasta revisión de resultados y de esa limitación.

## Criterio de decisión

El entrenamiento debe completarse y producir métricas comparables. El candidato solo se considera apto para revisión si no empeora la validación lingüística interna ni la evaluación externa; una mejora de BPB aislada no demuestra razonamiento ni conocimiento factual. No se modifica main con el checkpoint candidato automáticamente.
