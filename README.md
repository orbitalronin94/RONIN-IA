# Ronin IA

> **Asistente experimental para Android y web.** Una interfaz conversacional ligera que combina utilidades web, clasificación heurística local y una ruta opcional para ejecutar un modelo de lenguaje en el navegador.

[![Build Android APK](https://github.com/orbitalronin94/RONIN-IA/actions/workflows/build-android.yml/badge.svg)](https://github.com/orbitalronin94/RONIN-IA/actions/workflows/build-android.yml)
[![Plataforma](https://img.shields.io/badge/plataforma-Android%20%7C%20Web-3b82f6)](#)
[![Estado](https://img.shields.io/badge/estado-experimental-orange)](#)

Ronin IA empaqueta una aplicación web en una app Android mediante **Capacitor**. El objetivo es mantener una base sencilla de inspeccionar y modificar, con compilación reproducible en GitHub Actions y sin exigir un entorno Android local para generar el APK de depuración.

## Índice

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

## Qué incluye

- Interfaz de chat basada en HTML, CSS y JavaScript.
- Capa de respuestas heurísticas para determinadas intenciones y consultas sencillas.
- Integraciones web para consultar información, cuando hay conectividad.
- Ruta opcional para cargar **Transformers.js** y el modelo `HuggingFaceTB/SmolLM2-360M-Instruct` en formato cuantizado `q4`.
- Compatibilidad con las capacidades disponibles en el navegador, como WebGPU, y posibilidad de ejecución mediante WASM cuando la configuración y el dispositivo lo permiten.
- Envoltorio Android con Capacitor.
- Flujo de CI en GitHub Actions que genera un APK de depuración y lo publica como artefacto descargable de la ejecución.

> **Importante:** el modelo no se incluye dentro del repositorio ni del APK como conjunto de pesos integrado. La primera carga del modelo necesita internet y espacio suficiente en el dispositivo. La disponibilidad y el rendimiento dependen del navegador/WebView, la memoria, el procesador y el soporte de aceleración.

## Cómo funciona

A grandes rasgos, el flujo es:

1. La persona escribe un mensaje en la interfaz.
2. La aplicación intenta resolver las consultas sencillas mediante su lógica local.
3. Para las funciones que lo requieren, puede consultar servicios externos.
4. Si la ruta de modelo está habilitada y el dispositivo puede cargarlo, Transformers.js intenta ejecutar el modelo seleccionado.
5. Capacitor presenta la misma aplicación web dentro del contenedor Android.

La ruta heurística **no equivale a un LLM**: sirve para respuestas o clasificación sencillas, pero no tiene la capacidad general de razonamiento de un modelo generativo. La respuesta generada por el modelo puede variar según la disponibilidad de sus archivos y de los recursos del dispositivo.

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
| `www/index.html` | Interfaz, lógica del cliente y conexiones definidas por la aplicación |
| `@capacitor/core` | Puente entre la aplicación web y el contenedor nativo |
| `@capacitor/android` | Proyecto de destino Android |
| `@capacitor/cli` | Preparación y sincronización del proyecto nativo |
| GitHub Actions | Instalación de dependencias, generación del proyecto Android, compilación y publicación del APK |

El proyecto Android se genera durante el workflow con `npx cap add android`; por eso no es necesario mantener el directorio nativo generado en el repositorio para el flujo de compilación actual.

## Modelo de lenguaje y requisitos

Modelo configurado en la aplicación:

- **Modelo:** `HuggingFaceTB/SmolLM2-360M-Instruct`
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

La implementación web incluye o contempla consultas a servicios públicos para distintas funciones, entre ellas:

- **Wikipedia:** contenido enciclopédico.
- **Open-Meteo:** datos meteorológicos.
- **DuckDuckGo:** búsqueda web.
- **MyMemory:** traducción.

La disponibilidad, las políticas de uso, los límites de solicitudes y los resultados dependen de cada proveedor y de la conectividad. Una integración con un servicio público no implica afiliación, patrocinio ni garantía de disponibilidad por parte de ese servicio.

## Limitaciones conocidas

- El proyecto está en fase experimental; no debe asumirse que todas las funciones están disponibles en todos los dispositivos.
- El modelo se descarga cuando se necesita; el primer arranque de esa función puede tardar y consumir datos.
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
