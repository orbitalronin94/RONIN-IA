# Protocolo de benchmark de Ronin IA

## Objetivo

Medir la experiencia real del modelo local sin confundir tiempos de descarga, inicialización, inferencia y respuesta de servicios web. Este protocolo es manual por ahora: la CI actual no dispone de GPU/WebGPU ni de un dispositivo Android físico y no debe presentar sus resultados como benchmark móvil.

## Entorno que debe registrarse

Para cada ejecución, anotar:

- fecha y versión/commit de Ronin IA;
- dispositivo, versión de Android, versión de System WebView y navegador;
- RAM disponible aproximada, chipset y compatibilidad WebGPU;
- conexión utilizada (Wi-Fi/datos/desconectado);
- primera ejecución o modelo ya almacenado en caché;
- backend efectivo (WebGPU/CPU/WASM si se puede confirmar) y cuantización indicada por la app.

No publicar identificadores del dispositivo ni datos personales.

## Guion reproducible

Ejecutar cada escenario tres veces y guardar mediana y rango, sin mezclar dispositivos:

1. **Arranque en frío:** borrar datos/caché de la app, abrirla y medir tiempo hasta que la interfaz sea interactiva. Registrar aparte el volumen descargado si puede medirse.
2. **Primera preparación del modelo:** desde la misma instalación, medir desde la activación/inicio de carga hasta que la app indique modelo listo. No confundirlo con el arranque visual.
3. **Primera inferencia:** enviar el prompt "Explica en tres frases qué es una variable en programación." y medir desde envío hasta el primer texto visible y hasta la respuesta completa.
4. **Inferencia caliente:** repetir exactamente el mismo prompt sin recargar la app.
5. **Contexto:** enviar cinco mensajes cortos y luego preguntar "Resume los puntos principales en tres viñetas.".
6. **Resistencia:** ejecutar diez preguntas cortas seguidas, registrar fallos, bloqueos, reinicios, errores y si el modelo deja de responder.
7. **Red desconectada:** después de una carga exitosa, activar modo avión y repetir una pregunta local. Registrar por separado qué funciones locales funcionan y cuáles dependen de servicios externos.

## Plantilla de resultados

| Métrica | Resultado |
|---|---|
| Dispositivo / SO / WebView | |
| Commit | |
| Backend y cuantización observados | |
| Arranque visual (s) | |
| Preparación en frío (s) | |
| Primera respuesta visible (s) | |
| Respuesta completa en frío (s) | |
| Respuesta completa caliente (s) | |
| Fallos en 10 turnos | |
| Funciona sin red tras cachear (sí/no/parcial) | |

## Reglas de interpretación

- Comparar únicamente resultados tomados con el mismo guion y condiciones descritas.
- Informar mediana y rango de las tres repeticiones; no elegir solo la mejor ejecución.
- No afirmar que una inferencia es completamente offline si no se ha comprobado la ruta de red y los servicios externos.
- No comparar tokens/segundo si no se registra la longitud real de salida y no se mide con el mismo método.
- Un test estático aprobado o un APK compilado no prueba que la inferencia funcione en todos los móviles.
- No publicar una cifra de rendimiento hasta completar el protocolo en un dispositivo real.

## Próximo paso automatizable

Añadir instrumentación estructurada de carga e inferencia con marcas separadas para inicio de carga, modelo listo, primer token y fin de generación; después, exportar resultados sin incluir prompts privados. La instrumentación debe ser opt-in o limitarse a métricas locales, sin telemetría remota por defecto.
