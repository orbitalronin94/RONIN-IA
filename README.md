# Ronin IA

> Asistente experimental ligero para web y Android. Esta versión prioriza arrancar rápido, una APK pequeña y una ruta de IA remota intercambiable.

## Estado actual

- Interfaz web empaquetada con Capacitor para Android.
- Respuestas generativas mediante un endpoint público experimental compatible con OpenAI.
- Herramientas deterministas locales para cálculos sencillos y utilidades web.
- Historial local, enrutamiento de prompts y pruebas automatizadas.
- GitHub Actions construye una APK de depuración; el artefacto no es una release firmada.

**Importante:** el modelo generativo actual se ejecuta en un servicio remoto, no dentro de la APK. La respuesta depende de conexión, cuota y disponibilidad del proveedor. No envíes secretos ni información sensible al endpoint público. El router de expertos es lógica de aplicación, no una red neuronal MoE.

## Decisión de peso y velocidad

La APK no debe incluir pesos de modelos ni descargar varios modelos durante cada build. Los pesos ONNX de los experimentos anteriores podían añadir aproximadamente 1,8 GB a la compilación y al artefacto.

- No se empaquetan modelos ONNX en la APK.
- No se descargan pesos durante el build Android.
- El workflow de Android ejecuta pruebas, validaciones y genera el APK.
- Los barridos de fusión son investigación opcional y se lanzan manualmente; no bloquean el camino principal.
- Los pesos, checkpoints, cachés y resultados grandes permanecen fuera del historial Git.

## Ejecutar y probar

Requisitos: Node.js 20 y npm.

```bash
npm install
npm test
```

Para compilar el APK desde GitHub, abre **Actions → Build Ronin IA APK → Run workflow**. El workflow prepara el proyecto Android en el runner y publica una APK de depuración como artefacto durante 7 días.

Para compilar localmente en un entorno con Java/Android SDK:

```bash
npm install
npx cap add android
npx cap sync android
cd android
./gradlew --no-daemon assembleDebug
```

## Ruta del modelo Ronin

El objetivo inmediato es tener una aplicación ligera que funcione y después sustituir el proveedor experimental por un modelo base seleccionado y evaluado.

1. Comparar modelos abiertos pequeños con licencia, arquitectura y benchmarks verificados.
2. Seleccionar un único modelo inicial; no fusionar modelos por defecto.
3. Añadir una ruta de inferencia local opcional con descarga bajo demanda, sin incluir los pesos en el APK.
4. Adaptar el modelo solo después de medir una línea base y contar con datos permitidos.
5. Publicar resultados reproducibles antes de afirmar que Ronin mejora al modelo base.

Una adaptación de pesos existentes no es preentrenamiento desde cero. El proyecto no afirma que ya exista un modelo fundacional propio ni que las heurísticas actuales demuestren una mejora general.

## Estructura principal

- `www/`: interfaz, router de prompts y cliente de IA remota.
- `tests/`: contratos y pruebas automatizadas.
- `scripts/`: herramientas de investigación que no se ejecutan en cada build.
- `.github/workflows/`: CI de la aplicación y experimentos manuales.

## Privacidad y seguridad

El historial de chat se conserva localmente en el dispositivo. Las consultas generativas se envían al proveedor remoto actual; revisa el código y las condiciones del proveedor antes de usarlo. No se incluyen claves personales ni secretos en la aplicación.

## Limitaciones

- El endpoint público puede cambiar, limitar peticiones o dejar de estar disponible.
- El build de APK no valida el rendimiento en un dispositivo Android físico.
- La selección de modelos y las puntuaciones preliminares no demuestran superioridad; hacen falta benchmarks comparables.
