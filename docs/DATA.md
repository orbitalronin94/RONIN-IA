# Gobernanza y canalización de datos

Los corpus completos no se versionan en Git: se preparan localmente o como artefactos temporales de GitHub Actions y deben tener manifiesto, procedencia, licencia, particiones y SHA-256. El inventario actual está en [Inventario de corpus y materiales](INVENTARIO_CORPUS_Y_MATERIALES.md). La PR #39 integra en revisión Portfolio/Papers y las tres fuentes literarias abiertas; no asumir que la integración está fusionada en main hasta que se cierre esa PR.

## Corpus inicial: español financiero CC0 de Mozilla

Se ha seleccionado **Finance Sentences - North American Spanish**, conjunto cmm3gntdp00jymn07zjetwkyy, publicado bajo licencia CC0-1.0. La ficha informa de 79.655 frases limpias (1.325.013 tokens) procedentes de nueve dominios federales estadounidenses, además de una variante sin limpiar. Es un corpus pequeño y especializado: no representa el español general.

La ficha advierte que no se hizo análisis sintáctico y que puede contener títulos o fragmentos. La procedencia se registra mediante file_hash, que el publicador define como MD5 del nombre de archivo; no es un hash del contenido. El script calcula SHA-256 del archivo comprimido y de cada partición.

Antes de descargar, el operador debe entrar en la ficha de Mozilla y aceptar las condiciones aplicables, y crear una clave de API. La API exige credenciales y aceptación previa de términos en la web; no se debe eludir ese paso. Después, define MDC_API_KEY en el entorno e instala el extra opcional:

    python -m pip install -e '.[corpus]'
    export MDC_API_KEY='clave-de-api'
    python scripts/download_mozilla_corpus.py

Si ya tienes el archivo comprimido, puedes omitir la descarga y preparar directamente las particiones:

    python scripts/prepare_mozilla_corpus.py --archive /ruta/finance-sentences-north-american-spanish.tar.gz --output data/processed/mozilla-spanish-finance

El preparador lee corpus.tsv directamente del archivo, conserva frases con puntuación no negativa, elimina duplicados exactos por documento y frase, y separa por file_hash de forma determinista (80/10/10). Genera train.txt, validation.txt, test.txt y manifest.json. Falla si no puede producir las tres particiones o si detecta fuga de documentos. Los datos quedan fuera de Git.

El corpus no debe usarse como benchmark general: su dominio, geografía y calidad limitan las conclusiones posibles.

## Etapas obligatorias

1. Incorporar solo fuentes aprobadas; rechazar licencias desconocidas o incompatibles.
2. Normalizar el texto de forma determinista conservando la procedencia.
3. Eliminar registros mal formados, vacíos o no permitidos.
4. Aplicar deduplicación exacta y aproximada, documentando umbrales.
5. Detectar idioma y calcular estadísticas de calidad.
6. Separar por documento u origen para evitar filtraciones.
7. Crear fragmentos deterministas y un manifiesto de mezcla.
8. Tokenizar con un tokenizador versionado y guardar recuentos y SHA-256.

Los corpus originales y procesados son artefactos locales. No se deben subir a Git datos privados ni corpus sujetos a licencias.

## Texto generado por tutores

Los modelos auxiliares se descargan desde repositorios públicos cuya ficha declare licencia MIT. El descargador fija la revisión y calcula SHA-256 de los archivos. La licencia del modelo no concede derechos sobre sus datos de entrenamiento ni sobre cualquier texto generado. La procedencia y los permisos del corpus resultante se deben revisar por separado. La revisión humana y la deduplicación siguen siendo obligatorias.
