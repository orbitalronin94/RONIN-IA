# Decisiones técnicas de Ronin IA

Este documento explica el porqué de las decisiones que condicionan el producto. Los comentarios en el código describen los detalles locales; aquí queda el criterio global.

## Objetivo

Mantener una experiencia tipo chat que arranque rápido en Android y web, pueda ejecutar un modelo pequeño en el dispositivo y sea fácil de inspeccionar por colaboradores.

## Marca y recursos

- `www/assets/ronin-logo.svg`: SVG propio, sin fuentes ni imágenes remotas. Se ve nítido a cualquier escala y no añade dependencias.
- La paleta azul noche/cian/violeta da identidad visual y mantiene contraste en la interfaz oscura.

## Frontend

- `www/index.html` es el punto de entrada autocontenido para simplificar el empaquetado con Capacitor. Si crece, el siguiente paso será dividir CSS y JavaScript en módulos probados.
- El diseño responsive usa CSS y media queries para evitar añadir un framework UI pesado a una app pequeña.
- El contenido generado se escapa antes de convertir un subconjunto de Markdown a HTML; no se inserta HTML arbitrario del modelo.
- `localStorage` mantiene el historial local sin cuenta ni servidor. No es una copia de seguridad y el sistema puede borrarlo.

## Inferencia

- `onnx-community/Qwen3-0.6B-ONNX` con Transformers.js permite inferencia en navegador/WebView cuando el dispositivo es compatible.
- Carga bajo demanda: reduce el tiempo de apertura y deja al usuario decidir cuándo descargar el modelo.
- WebGPU primero y CPU como reserva: prioriza aceleración disponible sin bloquear dispositivos sin GPU compatible.
- La cuantización depende del runtime; no se promete la misma variante ni velocidad en todos los teléfonos.
- El contexto y los tokens limitados ayudan a controlar memoria y latencia; deben ajustarse con pruebas reales.

## Herramientas web

- Wikipedia y Open-Meteo requieren conexión; no son funciones offline.
- Las operaciones aritméticas sencillas se resuelven localmente para evitar latencia y consumo de modelo.

## Android y CI

- Capacitor reutiliza la interfaz web y evita duplicarla en código nativo.
- El workflow valida sintaxis antes de Gradle y publica un APK debug temporal.
- `package.json` y `capacitor.config.json` son JSON estricto y no admiten comentarios. Sus decisiones se documentan aquí.
- Un APK debug no es una release firmada para distribución pública.

## Próximos pasos

1. Medir primera carga, tokens por segundo y memoria en teléfonos reales.
2. Añadir pruebas para cálculo, historial, Markdown seguro y detección de herramientas.
3. Separar `www/index.html` en módulos cuando haya pruebas que permitan refactorizar con seguridad.
4. Evaluar un runtime nativo solo si benchmarks justifican mantener un segundo motor.
5. Revisar licencias de modelos, runtimes y datos antes de una publicación comercial.
