# Bibliotecas RONIN — 16 dominios × General/HKD

RONIN mantiene **16 dominios distintos**, cada uno dividido en dos particiones disjuntas:

- **General:** mitad inferior del ranking RONIN-HKD-0.1.
- **HKD:** mitad superior del ranking RONIN-HKD-0.1.

Total: **32 bibliotecas independientes**. El mínimo inicial para admitir cada biblioteca es **1 MiB de texto de entrenamiento**, con objetivo de crecimiento a **10 GiB por biblioteca** (320 GiB en total).

## Regla de tamaño

El mínimo de 1 MiB es un umbral de arranque, no una garantía de calidad ni una excepción legal. Si un dominio no reúne 1 MiB de documentos admisibles, la biblioteca permanece como candidata/incompleta y se informa de su tamaño real. No se rellena con duplicados, texto de otro dominio, documentos sin licencia compatible ni material de evaluación.

## Admisión y G-0

La apertura de G-0 permite trabajar con fuentes que tengan autorización limitada de adquisición de candidatos. No convierte esos candidatos en corpus admitido ni autoriza entrenamiento. Cada documento debe conservar licencia explícita, procedencia, revisión inmutable, hash, deduplicación, análisis de datos sensibles y revisión de calidad. Las licencias desconocidas, NC, ND, ShareAlike no autorizadas y los materiales con derechos inciertos permanecen excluidos.

General y HKD comparten el mismo pool documental elegible, pero sus particiones deben ser disjuntas. Se exige deduplicación entre bibliotecas para impedir que el mismo documento infle ambos tamaños.

## Los 16 dominios

1. Matemáticas
2. Lógica y epistemología
3. Filosofía
4. Física
5. Química y materiales
6. Biología
7. Medicina y ciencias de la salud
8. Informática
9. Ingeniería del software
10. Derecho y jurisprudencia
11. Economía
12. Ciencias sociales
13. Estadística y probabilidad
14. Astronomía y ciencias de la Tierra
15. Ingeniería y robótica
16. Historia, lingüística y literatura

El manifiesto data/manifests/sixteen_libraries.json contiene las 32 entradas y registra el estado real de cada una. Las entradas nuevas son candidatas; su presencia no significa que ya existan 1 MiB descargados ni que hayan superado G-0.

## Escalado

- Fase de arranque: hasta 1 MiB por biblioteca, si existe material admisible.
- Crecimiento: aumentar el tamaño por dominio conforme a la disponibilidad y calidad.
- Objetivo final: 10 GiB por biblioteca, sin relajar las garantías de derechos, calidad o separación de evaluación.

El Portfolio sigue siendo exclusivamente retrieval/RAG y no cuenta como biblioteca de entrenamiento.
