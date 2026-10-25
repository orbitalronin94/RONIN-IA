# Evaluación del modelo local desde navegador

## Ejecutar en el dispositivo objetivo

1. Clona el repositorio y sitúate en su raíz.
2. Inicia un servidor estático: `python -m http.server 8000`.
3. En el dispositivo que se desea medir, abre `http://<IP-del-ordenador>:8000/www/model-eval.html` (si ejecutas en el mismo equipo, usa `http://localhost:8000/www/model-eval.html`).
4. Pulsa **Cargar modelo y ejecutar 12 casos**. La primera ejecución descarga runtime/pesos; concede tiempo y memoria suficientes.
5. Exporta el JSONL y puntúalo desde la raíz:
   ```bash
   python scripts/score_model_eval.py --predictions ronin-qwen-model-eval-predictions.jsonl --output report.json
   ```

## Qué mide y qué no

- `startup_ms`: tiempo para inicializar runtime y cargar pesos; puede incluir la descarga fría.
- `latency_ms`: tiempo por respuesta después de inicializar el modelo.
- `backend`: backend solicitado y fallback notificado por el runtime; comprueba el dispositivo y el registro de la ejecución antes de interpretar resultados.
- Las respuestas de `human_review` se exportan pero se excluyen de la exactitud automática.
- Esta herramienta ejecuta únicamente el baseline Qwen integrado. No representa todavía una comparación Qwen vs. SmolLM2.
- Repite la prueba al menos tres veces en el mismo dispositivo y guarda cada exportación por separado. Anota modelo de dispositivo, SO, navegador/WebView y commit de dataset.
- No se suben automáticamente predicciones ni conversaciones. El archivo se genera localmente en el navegador.
