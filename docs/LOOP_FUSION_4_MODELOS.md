# Bucle experimental de fusión de cuatro modelos

Este flujo define un experimento repetible, no una promesa de mejora. La mejora «exponencial» no puede garantizarse: las fusiones pueden empeorar el resultado y cada candidato debe superar una evaluación fija.

## Candidatos de investigación (no aprobados aún)

La búsqueda inicial debe partir de modelos completos derivados de `Qwen/Qwen3-0.6B`, no cuantizaciones ni adaptadores LoRA sin fusionar. Posibles pistas para auditar:

1. `Qwen/Qwen3-0.6B` — referencia oficial, Apache-2.0.
2. `andresnowak/Qwen3-0.6B-instruction-finetuned_v2` — ajuste de instrucciones derivado de `unsloth/Qwen3-0.6B-Base`; revisar pesos completos, tokenizer y licencia.
3. `rohitnagareddy/Qwen3-0.6B-Coding-Finetuned-v1` — ajuste orientado a código; verificar si el repositorio contiene pesos completos o solo adaptadores antes de incluirlo.
4. `kurakurai/Luth-0.6B-Instruct` — ajuste francés/inglés; validar compatibilidad exacta y si aporta algo a las tareas objetivo en español.

Estas pistas no constituyen una selección validada. El flujo debe rechazarlas si faltan archivos, hay tensores incompatibles, tokenizer distinto, licencias no claras o si el modelo requiere una conversión no soportada.

## Bucle propuesto

1. Fijar revisión inmutable de los cuatro repositorios.
2. Verificar licencias, procedencia, arquitectura, nombres/formas de tensores y tokenizer.
3. Descartar los modelos que sean adaptadores, modelos de clasificación o cuantizaciones incompatibles con la fusión causal de pesos.
4. Generar candidatos con pesos conservadores y deterministas, manteniendo un registro de cada configuración.
5. Evaluar base y candidatos con el mismo conjunto de prompts de español, razonamiento, código, seguridad y formato; guardar respuestas, puntuaciones, latencia y memoria.
6. Repetir solo dentro de un presupuesto de experimentos fijado, modificando un parámetro cada vez. No detenerse por una métrica de juez aislada.
7. Elegir candidato únicamente si supera al modelo base en el objetivo predefinido y no presenta regresiones graves. Guardar hashes, configuración y resultados.
8. Convertir a ONNX y cuantizar solo después de aceptar el checkpoint de investigación; verificar el resultado en Android.

## Recursos y límites

La fusión de cuatro checkpoints de 0.6B requiere descargar varios gigabytes y memoria RAM/VRAM sustancial. No es razonable ejecutarla en el dispositivo Android ni afirmar que se ha completado desde una edición de archivos del repositorio. Hace falta un runner de entrenamiento con recursos suficientes. GitHub Actions estándar no garantiza GPU ni memoria suficiente.

## Criterio de éxito

No usar «exponencial» como criterio de aceptación: la calidad no escala de esa forma por sumar modelos. Registrar métricas antes y después, aceptar solo mejoras reproducibles y mantener Qwen3-0.6B como fallback. Si no hay mejora demostrada, conservar la referencia.

## Referencias consultadas

- Modelo base y licencia declarada: https://huggingface.co/Qwen/Qwen3-0.6B
- Ejemplo de ajuste de instrucciones: https://huggingface.co/andresnowak/Qwen3-0.6B-instruction-finetuned_v2
- Candidato de código: https://huggingface.co/rohitnagareddy/Qwen3-0.6B-Coding-Finetuned-v1
- Candidato multilingüe: https://huggingface.co/kurakurai/Luth-0.6B-Instruct
- Compatibilidad y cautela al fusionar: https://www.sbert.net/docs/package_reference/base/model.html
