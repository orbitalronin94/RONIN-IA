# Corpus propio de Portfolio/Papers

## Autorización y procedencia

El titular del repositorio autorizó expresamente en esta conversación el uso del
contenido de `orbitalronin94/Portfolio/Papers` para el corpus de entrenamiento
de RONIN IA. La autorización queda registrada en el manifiesto generado por el
preparador.

- Origen: https://github.com/orbitalronin94/Portfolio/tree/main/Papers
- Revisión inicial fijada: `fffc234fdf3f82b6a90d56ae9b190d1c0de79690`
- Ruta: `Papers/`
- La revisión está fijada por SHA para que la misma ejecución recupere los mismos
  archivos, aunque la rama `main` avance.
- La carpeta consultada contiene 49 elementos: 42 Markdown, un HTML, un PDF,
  un ZIP y cuatro archivos sin extensión.

La autorización del titular cubre sus aportaciones originales. No concede
derechos sobre citas extensas, imágenes, tablas, código, traducciones u otros
materiales de terceros que puedan aparecer dentro de los documentos. Esos
elementos deben revisarse antes de promover el artefacto a entrenamiento.

## Preparación

Ejecutar manualmente el workflow **Preparar corpus propio de Portfolio**.
El workflow:

1. Obtiene Portfolio en la revisión inmutable indicada.
2. Lee Markdown, MDX, TXT, RST, HTML y TeX.
3. Extrae texto de PDF mediante `pypdf`.
4. Lee ZIP sin extraer rutas al disco y solo admite miembros textuales permitidos.
5. Intenta leer como UTF-8 los archivos sin extensión.
6. Omite formatos binarios no textuales, duplicados exactos, documentos demasiado
   cortos y documentos que coincidan con patrones de credenciales.
7. Genera `train.txt` y `manifest.json`, con SHA-256 por documento y del corpus.

El artefacto de Actions se conserva siete días y no se incorpora al repositorio.
No se suben corpus ni checkpoints a Git.

## Uso en entrenamiento y evaluación

Esta colección es **solo material de entrenamiento**. No se divide aleatoriamente
entre entrenamiento, validación y prueba: los documentos están relacionados,
pueden compartir pasajes y el PDF puede compendiar otros textos. Separarlos al
azar podría provocar fuga de información.

La evaluación held-out de RONIN debe usar fuentes independientes que no formen
parte de esta colección. El artefacto generado es una etapa de preparación y
revisión; no inicia entrenamiento automáticamente.

## Revisión epistemológica y de seguridad

Los textos del autor contienen teorías, hipótesis, propuestas, experimentos,
manuales y afirmaciones de distinta naturaleza. La ingesta conserva el texto
original, pero no certifica la verdad de sus afirmaciones. Los informes de
entrenamiento y evaluación deben distinguir hipótesis, demostraciones formales,
resultados reproducibles, resultados exploratorios y opiniones.

Los manuales de ciberseguridad se conservan como material textual autorizado,
pero deben someterse a la política de seguridad del corpus y a una clasificación
temática antes de usarse para ajustar objetivos de comportamiento.

El escáner de credenciales es una defensa básica, no una auditoría completa.
El manifiesto enumera los documentos omitidos y los motivos. Debe revisarse antes
de considerar el corpus listo para entrenamiento.
