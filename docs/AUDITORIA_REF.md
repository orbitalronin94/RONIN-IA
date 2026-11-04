# Auditoría estructural de respuestas REF

El módulo `ronin.data.ref` valida que una respuesta de tutor contenga los nueve apartados del currículo, use las etiquetas permitidas y declare una confianza numérica entre 0 y 1. También rechaza apartados duplicados y exige una descripción de evidencia cuando se etiqueta un caso como `decoded`.

## Uso

```bash
python scripts/audit_ref_dataset.py \
  --input artifacts/teacher/gpt2.jsonl \
  --report artifacts/teacher/gpt2-ref-audit.json \
  --accepted-output artifacts/teacher/gpt2-ref-valid.jsonl
```

El informe cuenta registros válidos e inválidos, incidencias por tipo y tasa de validez estructural. El fichero opcional de salida conserva solo registros que superan las reglas de formato.

## Límite epistemológico

**Validar el esquema no valida el contenido.** El auditor no comprueba si las fuentes existen, si una inferencia es correcta, si la clase epistemológica está bien asignada ni si una confianza está calibrada. Tampoco convierte las respuestas de GPT-2 o GPT-Neo en anotaciones expertas. La adjudicación humana y las métricas de calibración requieren datos etiquetados independientes.
