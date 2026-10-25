# RONIN-IA — informe de pruebas de APK offline con Qwen2.5-0.5B

Estado: **implementación propuesta; pruebas de APK y dispositivo pendientes**.  
Modelo: `onnx-community/Qwen2.5-0.5B-Instruct`, ONNX `q4`.  
Workflow: `.github/workflows/build-offline-apk.yml`.

## Objetivo

Construir una APK de debug que incluya el runtime de inferencia, los recursos WASM, el tokenizer/configuración y los pesos del modelo para permitir una primera conversación sin conexión. La APK estándar sigue siendo ligera; el empaquetado grande se ejecuta solo mediante el workflow manual.

## Configuración que debe quedar registrada

- Commit de RONIN-IA:
- SHA de revisión resuelta en Hugging Face:
- Archivos incluidos y hashes: `www/models/onnx-community/Qwen2.5-0.5B-Instruct/ronin-bundle-manifest.json`
- Versión de Transformers.js: 3.7.2
- Variante ONNX: q4
- Dispositivo / modelo:
- Versión Android:
- Versión System WebView:
- Fecha de prueba:
- SHA-256 y tamaño de APK:

## Resultados

| Prueba | Resultado | Evidencia |
|---|---|---|
| Workflow de compilación | Pendiente | Enlace a ejecución de GitHub Actions |
| APK contiene modelo y runtime | Pendiente | Manifest de paquete y hashes |
| Instalación limpia sin red | Pendiente | Dispositivo, pasos y registro |
| Primera respuesta en modo avión | Pendiente | Prompt y respuesta guardados sin datos sensibles |
| Reinicio y segunda conversación offline | Pendiente | Pasos y resultado |
| Mediana / rango de latencia (mínimo 3 ejecuciones) | Pendiente | Exportación con timestamps |
| Pico de memoria / cierre por falta de memoria | Pendiente | Herramienta y registro usados |
| Tamaño final de APK | Pendiente | Tamaño y SHA-256 del artefacto |
| Ausencia de solicitudes de runtime/modelo a red | Pendiente | Inspección de tráfico o logs del dispositivo |

## Procedimiento de validación en dispositivo

1. Descargar la APK del artefacto de GitHub Actions e instalarla en un dispositivo de prueba.
2. Activar modo avión **antes de abrir la app por primera vez** y verificar que Wi-Fi/datos siguen desactivados.
3. Abrir RONIN-IA y enviar un prompt breve en español, por ejemplo: `Responde solo con la palabra OK.`
4. Registrar si el modelo inicializa y responde; guardar duración y errores sin datos personales.
5. Forzar cierre, volver a abrir en modo avión y repetir.
6. Ejecutar el conjunto de evaluación existente en el mismo dispositivo, si se puede adaptar al paquete local, y revisar manualmente respuestas ambiguas.
7. Repetir latencias al menos tres veces y anotar dispositivo, Android, WebView y commit.

## Límites y riesgos conocidos

- Un workflow que compile no demuestra que el modelo se ejecute en Android ni que responda correctamente sin red.
- El tamaño final de APK, pico de RAM, latencia y calidad todavía no se han medido para esta variante empaquetada.
- El script de preparación registra la revisión resuelta y los hashes de archivos descargados en CI limpio; el valor predeterminado `main` no es un pin inmutable. Para una release reproducible, ejecutar con el SHA de 40 caracteres revisado y conservarlo.
- El runtime y los pesos están configurados para no usar modelos remotos en Android; se debe confirmar mediante prueba de tráfico que no existan solicitudes inesperadas durante la inferencia.
- La APK generada es de debug; no es un artefacto de lanzamiento firmado.
- Las funciones opcionales que consultan servicios web (por ejemplo, búsqueda o clima) seguirán necesitando conexión. La garantía objetivo es la inferencia del modelo local, no convertir servicios externos en offline.

## Conclusión

**No hay todavía un resultado de éxito offline que declarar.** La conclusión se actualizará únicamente después de ejecutar el workflow y completar la prueba en dispositivo con modo avión desde antes del primer arranque.
