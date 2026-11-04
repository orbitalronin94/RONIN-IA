# Topografía RUN 5 — Common Corpus, 4 de noviembre de 2026

Fuente medida: `PleIAs/common_corpus`, revisión `307910e4c5d040d6f318e6edf2a2b97849155771`, 69.907 filas inspeccionadas en el worker del dominio jurídico.

## Rechazos observados

| Motivo | Filas |
|---|---:|
| Licencia fuera de allowlist | 42.920 |
| Idioma fuera de allowlist | 26.478 |
| Dominio sin clasificar | 308 |
| Texto demasiado corto | 158 |
| Admitidos en derecho/economía/ciencias sociales | 43 |

Los 43 registros aceptados produjeron dos candidatos de apenas 9.019 bytes de train cada uno, muy por debajo del mínimo de 2,5 GiB.

## Perfil de colecciones

| Colección | Filas observadas |
|---|---:|
| Open Government | 21.732 |
| Open Source | 20.284 |
| Open Culture | 11.626 |
| Open Web | 11.233 |
| Semantic data | 3.120 |
| Open Science | 1.912 |

## Hallazgo: confusión entre idioma natural y lenguaje de programación

El campo `language` no representa siempre un idioma humano. En `Open Source` incluye etiquetas de lenguaje de programación: Java (3.193), JavaScript (2.672), Python (2.096), C# (1.968), PHP (1.761), TypeScript (1.367), C++ (838), C (791), Go (475), Shell (445), entre otras.

El filtro anterior solo admitía inglés y español, por lo que descartaba código con licencias compatibles antes de que pudiera entrar en la biblioteca de informática. La corrección permite una allowlist explícita de lenguajes de programación únicamente cuando la colección es `Open Source`; no relaja el filtro de idiomas humanos en filosofía, ciencia o derecho.

## Límites

- La allowlist de licencias permanece intacta; no se admite CC BY-SA, NC, ND ni unknown.
- No se amplía el idioma humano permitido más allá de inglés/español.
- Los registros siguen siendo candidatos y requieren revisión humana.
- Este cambio puede recuperar material de informática, pero no resuelve por sí solo el déficit de las otras siete bibliotecas.
