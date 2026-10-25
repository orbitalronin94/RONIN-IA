# Ronin IA

> **Asistente experimental para Android y web.** Una interfaz conversacional ligera que combina utilidades web, clasificación heurística local y una ruta opcional para ejecutar un modelo de lenguaje en el navegador.

[![Build Android APK](https://github.com/orbitalronin94/RONIN-IA/actions/workflows/build-android.yml/badge.svg)](https://github.com/orbitalronin94/RONIN-IA/actions/workflows/build-android.yml)
[![Plataforma](https://img.shields.io/badge/plataforma-Android%20%7C%20Web-3b82f6)](#)
[![Estado](https://img.shields.io/badge/estado-experimental-orange)](#)

Ronin IA empaqueta una aplicación web en una app Android mediante **Capacitor**. El objetivo es mantener una base sencilla de inspeccionar y modificar, con compilación reproducible en GitHub Actions y sin exigir un entorno Android local para generar el APK de depuración.

## Objetivo del experimento

RONIN-IA investiga si una persona sin un laboratorio de IA ni un entorno de desarrollo local potente puede mejorar modelos existentes mediante selección informada, fusión de pesos compatible y evaluación reproducible, utilizando GitHub Actions y recursos gratuitos o de bajo coste cuando sea viable. El proyecto **no pretende entrenar un modelo fundacional desde cero**.

La hipótesis es que una combinación cuidadosamente elegida de modelos preentrenados puede mejorar determinadas capacidades frente al modelo base sin asumir el coste de un entrenamiento completo. Es una hipótesis por comprobar, no un resultado garantizado.

### Criterios de éxito

- Identificar candidatos con arquitectura, formas de tensores y tokenizadores compatibles.
- Ejecutar una fusión real y conservar la configuración exacta para reproducirla.
- Comparar el modelo base, los candidatos y el modelo fusionado con las mismas pruebas; incluir tareas en español, razonamiento, código y seguridad.
- Informar puntuaciones, latencia, memoria, costes y regresiones, sin presentar señales heurísticas como una evaluación humana.
- Publicar el procedimiento y los resultados, incluidos los experimentos fallidos, para que otras personas puedan repetirlos sin un entorno local potente.

**Definición de mejora:** el modelo fusionado solo se considerará mejor si supera al modelo base en criterios previamente definidos y comparables, sin ocultar las tareas en las que empeora. La compilación de una APK, la compatibilidad estructural o la creación de un archivo fusionado no bastan para demostrarlo.

## Índice

- [Decisiones de diseño](#decisiones-de-diseño)

- [Qué incluye](#qué-incluye)
- [Cómo funciona](#cómo-funciona)
- [Arquitectura](#arquitectura)
- [Modelo de lenguaje y requisitos](#modelo-de-lenguaje-y-requisitos)
- [Compilar el APK en la nube](#compilar-el-apk-en-la-nube)
- [Ejecutar en local](#ejecutar-en-local)
- [Servicios externos](#servicios-externos)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Seguridad y privacidad](#seguridad-y-privacidad)
- [Solución de problemas](#solución-de-problemas)
- [Hoja de ruta](#hoja-de-ruta)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

## Decisiones de diseño

Los formatos JSON (`package.json` y `capacitor.config.json`) no admiten comentarios válidos; sus motivos se documentan aquí y en `docs/DECISIONES.md`.

- **Marca propia:** `www/assets/ronin-logo.svg` es un SVG ligero, escalable y sin dependencias externas.
- **Interfaz:** paleta azul noche con acentos cian/violeta, diseño responsive y respeto por `prefers-reduced-motion`.
- **Arranque:** Android intenta preparar el modelo al abrir; la web mantiene la carga bajo demanda.
- **Inferencia:** WebGPU primero cuando es compatible, con CPU de reserva; la cuantización depende del dispositivo/runtime.
- **Seguridad de salida:** el texto del modelo se escapa antes de renderizar Markdown y los enlaces externos usan `noopener noreferrer`.
- **Datos:** el historial permanece en almacenamiento local; Wikipedia y el tiempo necesitan conexión.
- **Build:** GitHub Actions valida sintaxis JavaScript antes de construir el APK de depuración.

## Qué incluye

- Interfaz conversacional inspirada en ChatGPT, adaptable a móvil, tablet y escritorio.
- Historial local de conversaciones, creación de chats y copia de respuestas.
- Arranque ligero: la interfaz aparece sin descargar el modelo de lenguaje.
- Carga bajo demanda de **Transformers.js** y `onnx-community/Qwen3-0.6B-ONNX` en formato cuantizado `q4`, con selección automática de cuantización (`q4f16` en WebGPU y `q8`/`int8` como alternativas de CPU) y backend de reserva cuando la GPU no está disponible.
- Respuestas rápidas para operaciones aritméticas sencillas.
- Consultas a Wikipedia y Open-Meteo cuando se detectan esas peticiones y hay conexión.
- Empaquetado Android con Capacitor y compilación de APK mediante GitHub Actions.

> **Importante:** el modelo no está incluido en el APK como pesos locales. La primera carga requiere internet y puede tardar. La capacidad de razonamiento de Qwen3-0.6B es limitada comparada con modelos grandes alojados en la nube.

## Cómo funciona

1. La interfaz se muestra primero. En Android nativo se inicia después la preparación del modelo; en web no se descarga hasta que el usuario activa la IA o envía una pregunta.
2. Las operaciones aritméticas sencillas se resuelven localmente; algunas consultas de Wikipedia y tiempo usan servicios públicos.
3. Al activar la IA o enviar un mensaje normal, Ronin carga Transformers.js y el modelo seleccionado.
4. La conversación reciente se usa como contexto del modelo y el historial se guarda en el almacenamiento local del navegador/WebView.
5. Capacitor empaqueta la web en una aplicación Android.

La carga bajo demanda mejora el tiempo hasta la primera pantalla, pero no garantiza que la primera respuesta generativa sea rápida: depende de la descarga inicial, memoria, CPU/GPU y WebView del dispositivo. El contexto se limita a los últimos ocho mensajes (con límite por mensaje) y la generación a 192 tokens para equilibrar calidad, latencia y memoria.

## Arquitectura

```text
RONIN-IA/
├── .github/
│   └── workflows/
│       └── build-android.yml   # Compilación automática del APK
├── www/
│   └── index.html              # Interfaz y lógica web de Ronin IA
├── capacitor.config.json       # Identidad y configuración de Capacitor
├── package.json                # Dependencias y herramientas Node.js
└── README.md
```

### Componentes principales

| Componente | Responsabilidad |
|---|---|
| `www/index.html` | Interfaz, estilos responsive, historial, lógica del chat y consultas públicas |
| `localStorage` | Persistencia local del historial de chats |
| Transformers.js | Runtime de inferencia del modelo en navegador |
| `@capacitor/core` y `@capacitor/android` | Contenedor y plataforma Android |
| GitHub Actions | Comprobación de sintaxis, generación Android, compilación y publicación del APK |

## Modelo de lenguaje y requisitos

Modelo configurado en la aplicación:

- **Modelo:** `onnx-community/Qwen3-0.6B-ONNX`
- **Formato solicitado:** cuantización `q4`
- **Runtime web:** Transformers.js
- **Aceleración:** WebGPU si el entorno la admite; WASM puede actuar como alternativa según la configuración efectiva.

### Consejos de uso

- Conéctate a una red estable la primera vez que cargues el modelo.
- Deja que termine la descarga y la inicialización antes de enviar otra consulta.
- Si WebGPU no está disponible en el WebView del dispositivo, el rendimiento puede ser menor o la ruta de inferencia puede no funcionar.
- El tamaño real descargado, el uso de memoria y la compatibilidad dependen de las versiones de las bibliotecas y de los artefactos publicados por el modelo.
- No se debe interpretar una respuesta heurística como prueba de que el modelo se ha cargado correctamente.

## Compilar el APK en la nube

La compilación automatizada está definida en:

`.github/workflows/build-android.yml`

### Opción A: ejecutar manualmente

1. Abre la pestaña [Actions del repositorio](https://github.com/orbitalronin94/RONIN-IA/actions).
2. Selecciona **Build Ronin IA APK**.
3. Pulsa **Run workflow** y elige la rama deseada, normalmente `main`.
4. Abre la ejecución nueva y espera a que el trabajo termine.
5. Si el trabajo termina correctamente, baja hasta **Artifacts** y descarga `ronin-ia-debug-apk`.
6. Descomprime el artefacto: el archivo esperado es `app-debug.apk`.

### Opción B: compilar al subir cambios

El workflow también se ejecuta automáticamente cuando se hace `push` a las ramas `main` o `master`.

### Qué hace el workflow

1. Prepara Node.js 20 y Java 21.
2. Instala las dependencias de npm.
3. Genera la plataforma Android con Capacitor.
4. Sincroniza los recursos web con Android.
5. Ejecuta Gradle para generar el APK de depuración.
6. Publica el APK como artefacto de GitHub Actions durante 7 días.

El APK de depuración está destinado a pruebas. No es una publicación de producción firmada para distribución general. Para publicar en Google Play o distribuir una versión de producción, hay que configurar firma, gestión segura de claves, versionado y un proceso de release específico.

**Descarga:** [ver ejecuciones y artefactos de GitHub Actions](https://github.com/orbitalronin94/RONIN-IA/actions).

## Ejecutar en local

Necesitas Node.js 20 o compatible con las dependencias del proyecto, npm y un entorno Android/Java apropiado si quieres compilar en tu ordenador.

```bash
git clone https://github.com/orbitalronin94/RONIN-IA.git
cd RONIN-IA
npm install
npx cap add android
npx cap sync android
cd android
./gradlew assembleDebug
```

El APK de depuración suele generarse en:

`android/app/build/outputs/apk/debug/app-debug.apk`

En Windows, ejecuta el wrapper como `gradlew.bat assembleDebug` desde el directorio `android`. Si ya existe el directorio `android`, no repitas `npx cap add android`; ejecuta `npx cap sync android`.

Para inspeccionar la versión web sin empaquetar, puedes servir el contenido de `www/` con un servidor HTTP local. Algunas funciones, especialmente la descarga del modelo, pueden comportarse de forma distinta en `file://`, en un servidor local y dentro del WebView de Android.

## Servicios externos

La aplicación puede consultar estos servicios públicos cuando el usuario hace una petición compatible:

- **Wikipedia:** búsqueda de artículos y extractos.
- **Open-Meteo:** geocodificación y condiciones meteorológicas actuales.

Los servicios requieren conectividad y pueden cambiar disponibilidad, límites o políticas. La integración no implica afiliación ni garantía por parte de esos proveedores.

## Limitaciones conocidas

- El proyecto está en fase experimental; no debe asumirse que todas las funciones están disponibles en todos los dispositivos.
- Qwen3-0.6B es un modelo pequeño: el diseño optimiza el arranque, pero no puede convertir ese modelo en un sistema de razonamiento de gran escala.
- En Android la preparación automática puede descargar el modelo en el primer arranque y consumir datos; en web se inicia bajo demanda.
- WebGPU y WASM varían en rendimiento y compatibilidad según el navegador/WebView y el hardware.
- Los servicios externos pueden fallar, cambiar sus API o limitar las solicitudes.
- La compilación de CI verifica que el proyecto pueda empaquetarse; por sí sola no garantiza la corrección funcional de todas las funciones ni pruebas en dispositivos físicos.
- El artefacto `app-debug.apk` es una compilación de depuración, no una versión firmada de producción.

## Seguridad y privacidad

- No introduzcas contraseñas, claves privadas ni información sensible en conversaciones de prueba.
- Las consultas enviadas a servicios externos pueden salir del dispositivo; revisa el código y las políticas de esos proveedores antes de usar datos personales.
- La ejecución local de un modelo no significa que **toda** la aplicación funcione sin red: las consultas externas y la descarga inicial del modelo requieren conectividad.
- No guardes keystores, contraseñas de firma, tokens ni credenciales en el repositorio. Para futuras versiones de producción, usa GitHub Actions Secrets y permisos mínimos.
- Revisa las licencias y condiciones de uso de las bibliotecas, el modelo y los servicios externos antes de distribuir la aplicación.

## Solución de problemas

### El workflow falla durante npm

Comprueba que `package.json` esté presente en la rama compilada y que las dependencias sean resolubles. Abre el paso que ha fallado en la ejecución de Actions para ver el mensaje exacto.

### Gradle falla

Revisa la versión de Java, el log completo de Gradle y los pasos de preparación de Capacitor. El workflow actual ejecuta Gradle desde el directorio `android`.

### La compilación termina, pero no aparece el APK

Confirma que el paso **Upload artifact** haya terminado correctamente y que el archivo exista en `android/app/build/outputs/apk/debug/app-debug.apk`. Los artefactos de este workflow se conservan durante 7 días.

### La IA no responde o tarda demasiado

Comprueba la conexión, espera a que el modelo termine de inicializarse y vuelve a probar. En dispositivos con poca memoria o sin aceleración compatible, reduce las expectativas de rendimiento y revisa la consola/logs para identificar fallos de carga.

### Las funciones web no devuelven resultados

Comprueba la conexión y si el proveedor externo está disponible. Los servicios públicos pueden cambiar sus políticas o límites sin que eso implique un fallo de la interfaz.

## Hoja de ruta

- [ ] Añadir pruebas automatizadas para la lógica de interfaz y las funciones principales.
- [ ] Validar el flujo en dispositivos Android reales y distintas versiones de WebView.
- [ ] Mejorar la presentación del estado de carga y de los errores del modelo.
- [ ] Documentar con precisión las licencias y versiones de dependencias.
- [ ] Preparar un flujo de release independiente con firma segura para producción.
- [ ] Añadir comprobaciones de accesibilidad y manejo de errores de red.

## Contribuir

1. Crea una rama para tu cambio.
2. Mantén los cambios acotados y explica cualquier dependencia nueva.
3. Prueba la interfaz y, cuando sea posible, ejecuta el workflow de Android.
4. Abre un pull request con el propósito, los cambios y las pruebas realizadas.

Las propuestas, correcciones y reportes de errores son bienvenidos. Incluye pasos reproducibles, el dispositivo/versión de Android si procede y los logs relevantes, eliminando antes cualquier dato sensible.

## Licencia

No se especifica aquí una licencia del proyecto. Hasta que se añada un archivo `LICENSE`, no debe asumirse que el código puede reutilizarse, modificarse o redistribuirse sin restricciones. Las licencias del modelo, las dependencias y los servicios de terceros son independientes.


## Preparación del modelo en Android

En la APK Android, Ronin intenta preparar Qwen3 al abrir la app. La primera apertura necesita conexión y espacio para descargar el modelo; la caché del navegador se reutiliza cuando está disponible. En la web normal el modelo sigue cargándose bajo demanda para no consumir datos automáticamente. Esta modalidad **no incorpora aún los pesos dentro del APK**; para ello se necesita una variante de distribución específica y comprobar el tamaño final.

## Comprobaciones locales

`npm test` ejecuta pruebas de contrato estáticas sobre las protecciones críticas del frontend. La compilación de GitHub Actions valida además la sintaxis del módulo y genera un APK de depuración. Las pruebas estáticas no sustituyen una prueba de inferencia en móviles físicos.

## Validación independiente tras el barrido

Cuando el cribado heurístico exporta `fusion-sweep-results/ronin-fused-checkpoint`, el workflow ejecuta una segunda etapa con `lm-evaluation-harness`: compara base y candidato con ARC-Easy, HellaSwag, TruthfulQA MC2 y GSM8K (100 ejemplos por tarea, semilla 42), y publica `comparison.json`. Si no se exporta checkpoint, no hay nada que validar y el workflow debe dejar constancia de que el cribado no encontró candidato. Un resultado positivo en estas cuatro tareas es evidencia direccional, no prueba universal: revisar deltas por tarea, muestras y regresiones antes de adoptar el modelo.

## Estado de validación del proyecto

**Última revisión:** 2026-10-23 (UTC). Esta sección refleja ejecuciones concretas de GitHub Actions; consulta los enlaces para ver el estado más reciente.

| Comprobación | Resultado conocido | Evidencia |
|---|---|---|
| Auditoría de candidatos (24 repositorios) | Correcta | [Ejecución 39995711599](https://github.com/orbitalronin94/RONIN-IA/actions/runs/39995711599) |
| APK Android en el commit `bac497f` | Compilación correcta; artefacto publicado | [Ejecución 39997314107](https://github.com/orbitalronin94/RONIN-IA/actions/runs/39997314107) |
| Evaluación profunda en el commit `71d2f79` | Workflow correcto; informe publicado | [Ejecución 39994459932](https://github.com/orbitalronin94/RONIN-IA/actions/runs/39994459932) |
| Evaluación profunda en el commit `8e92cc5` | En curso en la última consulta; aún sin informe final | [Ejecución 39995671249](https://github.com/orbitalronin94/RONIN-IA/actions/runs/39995671249) |

El informe de la ejecución anterior `39994459932` (`71d2f79`) se inspeccionó y contiene una prueba exploratoria de cuatro modelos. El modelo base Qwen3-0.6B obtuvo 10/14 comprobaciones heurísticas; `instruction`, 7/14; `coding`, 7/14; y `luth`, 8/14. Los tres candidatos muestran compatibilidad estructural preliminar (311 tensores, sin diferencias de forma reportadas y vocabulario/token IDs coincidentes). Estas puntuaciones son señales de cribado pequeñas, no una evaluación humana ni una prueba de mejora; en esa prueba el base quedó por encima de los tres candidatos. No se ha demostrado aún una fusión superior.

La ejecución más reciente de evaluación, `39995671249` (`8e92cc5`), seguía en curso en la última consulta. Los números del informe anterior no deben atribuirse a ese commit.

### Última iteración de fusión y validación independiente (2026-10-25)

- El workflow de barrido encadena una comparación independiente con `lm-evaluation-harness` si el cribado exporta un checkpoint: ARC-Easy, HellaSwag, TruthfulQA MC2 y GSM8K, hasta 100 ejemplos por tarea, semilla 42 y batch 1.
- Si no se exporta checkpoint, la comparación se marca como omitida y no se afirma mejora alguna. La puntuación de nueve prompts sigue siendo solo un filtro preliminar.
- [Workflow de barrido de fusiones](https://github.com/orbitalronin94/RONIN-IA/actions/workflows/fusion-sweep.yml) · [Build APK, ejecución 40173795125](https://github.com/orbitalronin94/RONIN-IA/actions/runs/40173795125).
- El build de depuración terminó correctamente: descarga de pesos ONNX, sincronización de Capacitor, Gradle y publicación del artefacto. Esto no demuestra calidad del modelo fusionado ni funcionamiento en dispositivo físico.
- En la última consulta, el barrido antiguo 40173401635 seguía activo y 40173666529 esperaba por concurrencia; aún no había artefactos del primero.

### Memoria técnica de iteraciones

El historial de cambios, resultados, fallos conocidos y próximos pasos se mantiene en [`docs/MEMORIA_ITERACIONES.md`](docs/MEMORIA_ITERACIONES.md). Actualiza ese documento junto con este README cuando haya resultados nuevos y verificables.

### Estado y límites de la validación

- Una auditoría correcta no demuestra que todos los candidatos sean compatibles entre sí.
- Una compilación APK correcta no sustituye las pruebas funcionales en un dispositivo Android real.
- No se declara una fusión validada ni una mejora del modelo hasta disponer de resultados reproducibles y comparables con el modelo base.


## APK Android con modelos precargados

La preparación de Android descarga los pesos ONNX q4 de los dos modelos del catálogo y los coloca bajo `www/models/`; Capacitor los copia a los recursos de la app para que la inferencia no dependa de descargar los pesos al abrirla.

```bash
npm install
npx cap add android   # solo la primera vez, si aún no existe android/
npm run sync:android
```

La descarga de preparación requiere conexión y aproximadamente **1,8 GB** de espacio para los pesos, además del espacio temporal de compilación. El APK resultante será muy grande y debe instalarse mediante distribución directa; las tiendas pueden imponer límites distintos. Los pesos generados se excluyen de Git mediante `.gitignore` para no convertir el repositorio en un almacén de binarios gigantes. El paquete incluye los modelos, pero la app carga un único experto cada vez para limitar el uso de RAM.

Para listar qué archivos se empaquetarán sin descargarlos:

```bash
npm run prepare:models -- --list
```
