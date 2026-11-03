# Gobernanza y canalización de datos

Este repositorio no incluye corpus de entrenamiento. Los datos los aporta el operador y deben describirse mediante un manifiesto antes de entrenar.

Cada manifiesto de origen debe registrar:

- identificador estable del conjunto de datos y versión o fecha de obtención;
- URL de origen o método de adquisición;
- licencia y usos permitidos, incluidas las restricciones de entrenamiento y uso comercial;
- idioma y tamaño aproximado;
- pasos de preprocesamiento y filtrado;
- método de deduplicación y recuentos resultantes;
- asignación a entrenamiento, validación y prueba, con semilla aleatoria;
- suma de comprobación criptográfica de cada fragmento inmutable.

## Etapas obligatorias

1. Incorporar solo fuentes aprobadas; rechazar licencias desconocidas o incompatibles.
2. Normalizar el texto de forma determinista conservando la procedencia del original.
3. Eliminar registros mal formados, vacíos o no permitidos por las políticas del proyecto.
4. Aplicar deduplicación exacta y después aproximada, documentando los umbrales.
5. Detectar el idioma y calcular resúmenes estadísticos y de calidad.
6. Separar por documento u origen para evitar filtraciones entre entrenamiento, validación y prueba.
7. Crear fragmentos deterministas y un manifiesto de mezcla con pesos explícitos.
8. Tokenizar con un tokenizador versionado y guardar recuentos y sumas de comprobación.

Los corpus originales y procesados son artefactos locales de ejecución. No se deben subir a Git datos privados ni corpus sujetos a licencias. El tokenizador de bytes y el lector de archivos de texto actuales son provisionales; la canalización completa con trazabilidad sigue pendiente.

## Texto generado por tutores

Los modelos auxiliares se descargan desde repositorios públicos cuya ficha declare licencia MIT. El descargador fija la revisión, guarda la ficha de licencia y calcula SHA-256 de los archivos. Cada ejemplo generado registra el modelo, revisión, licencia y huella del texto.

La licencia MIT del modelo auxiliar no concede automáticamente derechos sobre los datos con los que fue entrenado ni sobre cualquier texto que genere. La procedencia y los permisos del corpus resultante se deben revisar por separado. La revisión humana y la deduplicación siguen siendo obligatorias.
