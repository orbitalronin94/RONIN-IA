# Contrato de anotación REF: correspondencia y migración

## Estado

La propuesta de ingesta REF del 4 de noviembre de 2026 no es compatible,
campo por campo, con el validador actual de `ronin/epistemic/schema.py`.
No se debe producir `annotations.jsonl` hasta aprobar una versión de contrato
y probar su conversión.

## Diferencias detectadas

| Propuesta de ingesta | Esquema actual | Decisión |
|---|---|---|
| `fragment_id` | `record_id` | Mapear el ID del fragmento a `record_id`; conservar `fragment_id` como alias opcional solo si se versiona. |
| `fragment_sha256` | `source_sha256` | No son equivalentes. El esquema actual valida el hash de la fuente. Añadir un campo explícito `text_sha256` o migrar el contrato para conservar ambos. |
| `fuente` | `source_id` | Mapear a identificador estable de la fuente, no a nombre libre. |
| `licencia` | `license` | Conservar etiqueta exacta y evidencia de licencia en el manifiesto; no usar `PD` sin jurisdicción. |
| `encoding_state` | `encoding_status` | Renombrado directo. |
| `annotator_id` | `annotator` | Renombrado directo. |
| `refutation_criterion` | `potential_falsifier` | Renombrado semántico; debe contener un criterio comprobable si la clase es `falsifiable`. |
| `required_evidence` | Sin campo obligatorio equivalente | Puede añadirse como campo opcional en una futura versión. |
| `decoding_evidence` | `decoding_evidence` | Compatible; obligatorio si `encoding_status=decoded`. |
| `epistemic_class` | `epistemic_class` | Compatible. |
| `claim_type` | `claim_type` | El esquema actual admite además `descriptive` y `unknown`. |
| `genre` | `genre` | El esquema actual admite además `unknown`. |
| `offset_inicio/fin` | `span_start/span_end` | Los offsets actuales son relativos a `text`; no equivalen a offsets en el texto padre. |

## Invariantes antes de anotar

1. Cada registro conserva el SHA-256 del texto original de origen y el SHA-256
   del fragmento por separado.
2. Los offsets se definen explícitamente como relativos al texto normalizado
   o al archivo original. No mezclar ambos sistemas.
3. `decoded` requiere evidencia documental identificable y recuperable.
4. `falsifiable` requiere `potential_falsifier`; una frase vaga como
   «se puede comprobar» no basta.
5. Una confianza inferior a 0,6 se mantiene en la cola de revisión y no se
   introduce como etiqueta supervisada de alta confianza.
6. El esquema estructural no valida la verdad de la anotación ni la calidad
   jurídica de la licencia.

## Decisión de compatibilidad

Para no romper registros REF existentes, mantener el esquema actual como
`REF-v1` y diseñar una migración aditiva `REF-v1.1` antes de generar datos
a escala. La migración debe incluir pruebas de ida y vuelta y fixtures con
casos `decoded`, `falsifiable`, `mixed` y `undetermined`.

## Validación del gate G-0

Ejecutar:

```bash
python scripts/validate_license_audit.py
pytest tests/test_license_audit.py
```

El validador comprueba la integridad estructural del informe y bloquea
contradicciones como autorizar descargas cuando `passed=false`. No constituye
un dictamen jurídico.
