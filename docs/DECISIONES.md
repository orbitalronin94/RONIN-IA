# Decisiones técnicas de Ronin IA

Este documento explica el porqué de las decisiones que condicionan el producto. Los comentarios en el código describen los detalles locales; aquí queda el criterio global.

## Objetivo

Mantener una experiencia tipo chat que arranque rápido en Android y web, pueda ejecutar un modelo pequeño en el dispositivo y sea fácil de inspeccionar por colaboradores.

## Marca y recursos

- El SVG incluye título y descripción accesibles; no usa rasterizados, fuentes externas ni dependencias. Los comentarios del SVG explican el propósito de cada capa visual.

- `www/assets/ronin-logo.svg`: SVG propio, sin fuentes ni imágenes remotas. Se ve nítido a cualquier escala y no añade dependencias.
- La paleta azul noche/cian/violeta da identidad visual y mantiene contraste en la interfaz oscura.

## Frontend

- Los comentarios junto a funciones críticas explican el motivo de la decisión, no solo repiten lo que hace la línea. Esto ayuda a cambiar la arquitectura con menos riesgo.
- El contenido del modelo se trata como entrada no confiable. El Markdown permitido es deliberadamente limitado; no debe añadirse soporte para HTML arbitrario.

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

## Criterio de investigación open source

- Transformers.js es la ruta actual porque evita un servidor y funciona con ONNX en navegador; no se asume que WebGPU esté disponible en todos los WebView.
- Ollama y Open WebUI son referencias para API y experiencia de producto, no dependencias requeridas para una aplicación móvil autónoma.
- llama.cpp se evaluará como alternativa nativa solo con mediciones comparables de tiempo hasta primera respuesta, tokens/s, RAM y tamaño de descarga.
- Los proyectos de referencia y sus límites se registran en `docs/REFERENCIAS_OPEN_SOURCE.md`.

## Próximos pasos

1. Medir primera carga, tokens por segundo y memoria en teléfonos reales.
2. Añadir pruebas para cálculo, historial, Markdown seguro y detección de herramientas.
3. Separar `www/index.html` en módulos cuando haya pruebas que permitan refactorizar con seguridad.
4. Evaluar un runtime nativo solo si benchmarks justifican mantener un segundo motor.
5. Revisar licencias de modelos, runtimes y datos antes de una publicación comercial.
