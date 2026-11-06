# Pesos y modelos publicados

## Modelo experimental principal: Ronin - Drosophila

**Nombre:** Ronin - Drosophila (**100.900.160 parámetros**).  
**Identificador:** `Ronin-Drosophila-100900160`.  
**Manifiesto principal:** [ronin-drosophila-main.json](ronin-drosophila-main.json).  
**Run de expansión ×10:** [#42203609278](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42203609278).  
**Artefacto del checkpoint:** [expanded-final.pt + informes](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42203609278/artifacts/13495833454).  
**SHA-256:** `f3f8e2e75e418f8630372c242378a28010db83148d169d85ad3e4f73114cda9a`.  
**Tamaño:** 403.629.045 bytes.

Drosophila es el modelo experimental principal por decisión expresa. El checkpoint se almacena como artefacto de GitHub Actions porque supera el límite práctico de un archivo Git ordinario. Los artefactos tienen política de retención: para distribución duradera habrá que publicar una release o migrar a almacenamiento de pesos adecuado.

## Fallback compacto empaquetado en Git

El archivo [ronin-main.pt](ronin-main.pt) sigue conteniendo **RONIN-tiny-seed95-100-001**, con 9.922.880 parámetros.

- **Manifiesto:** [main-model.json](main-model.json)
- **SHA-256:** `4fb699cf3633ce610f66f2066ce182ceb957b2b0bead2b97c42cccf7f7021d11`
- **Tamaño:** 39.719.989 bytes.
- **Procedencia:** [GitHub Actions #42121731925](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42121731925).

Este paquete se conserva como fallback reproducible y compacto. No se debe interpretar como si contuviera los pesos de Drosophila.

## Evaluación y límites

La expansión preservó los logits antes del entrenamiento (diferencia absoluta máxima 1,4305×10⁻⁶). Tras 500 pasos, el screening MMLU-Pro pareado quedó en 5/64 antes y 5/64 después. Esto significa que no se detectó regresión en esa muestra; no demuestra mejora general ni sustituye una evaluación independiente completa.

El manifiesto principal experimental registra asimismo G-0 como FAIL y las comprobaciones globales de near-duplicates y contaminación de holdout como PENDING. La promoción del modelo experimental no borra esas limitaciones.

## Histórico

El manifiesto [ronin-drosophila-100900160-candidate.json](ronin-drosophila-100900160-candidate.json) conserva la procedencia del candidato anterior, run #42198068241. El checkpoint actual promovido procede del run #42203609278 y está descrito en el manifiesto principal experimental.
