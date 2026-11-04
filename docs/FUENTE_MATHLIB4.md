# Fuente candidata: Lean mathlib4

- Repositorio: https://github.com/leanprover-community/mathlib4
- Revisión fijada: `a84939a26903163e1b98ee002bc94e9563e75c12`
- Licencia declarada en el repositorio: Apache-2.0
- Ámbito de extracción: solo archivos `.lean` bajo `Mathlib/`
- Dominios de destino: matemáticas y lógica/epistemología
- Acceso: checkout Git público, sin token ni credenciales
- Estado: candidato con autorización limitada de adquisición; no admitido a entrenamiento

El inventario del árbol Git en esa revisión contiene 9.307 archivos `.lean` y 103.212.560 bytes de fuente. Esta cantidad aporta una base formal valiosa, pero no satisface por sí sola los 2,5 GiB exigidos a cada biblioteca. El workflow vuelve a calcular los conteos reales y produce JSONL con identificador, revisión, licencia, URL inmutable, SHA-256 por fichero y dominio.

El adaptador verifica el archivo raíz `LICENSE`, rechaza encabezados SPDX explícitos incompatibles y no incluye `.lake`, dependencias, artefactos de compilación ni contenido externo. La extracción conserva los ficheros Lean completos como candidatos de código y demostraciones; no los presenta como prosa general.

La autorización de alcance limitado permite preparar candidatos Apache-2.0 para revisión. No cambia G-0, no convierte los artefactos en training-eligible y no elimina la revisión humana de calidad, procedencia, seguridad y obligaciones de licencia.
