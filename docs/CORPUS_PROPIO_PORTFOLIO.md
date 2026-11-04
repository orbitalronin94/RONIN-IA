# Portfolio/Papers como biblioteca experta de recuperación

## Política

Portfolio/Papers **no participa en pretraining ni SFT**. No es una de las 16 bibliotecas masivas y nunca se concatena al corpus de entrenamiento. Se prepara como un índice RAG de experto para consultar únicamente cuando el modelo detecte incertidumbre suficiente. La respuesta debe distinguir conocimiento paramétrico de evidencia recuperada y citar el documento.

La autorización expresa del titular cubre sus aportaciones originales. No concede derechos sobre citas extensas, imágenes, tablas, código, traducciones u otros materiales de terceros. La recuperación mantiene la procedencia y requiere revisión de contenido de terceros antes de publicar respuestas que lo reproduzcan.

## Procedencia

- Origen: https://github.com/orbitalronin94/Portfolio/tree/main/Papers
- Revisión fijada: `fffc234fdf3f82b6a90d56ae9b190d1c0de79690`
- Ruta: `Papers/`
- La revisión se fija por SHA para reproducibilidad.

## Construcción del índice

Ejecutar manualmente **Construir índice RAG experto de Portfolio**. El workflow:

1. Obtiene Portfolio en la revisión inmutable indicada.
2. Extrae Markdown, MDX, TXT, RST, HTML, TeX y PDF; lee ZIP sin extraer rutas al disco y solo admite miembros textuales permitidos.
3. Excluye duplicados exactos, documentos cortos y patrones de credenciales.
4. Escribe `documents.jsonl` con texto, ruta, SHA-256 y revisión de origen; nunca crea `train.txt`.
5. Construye un índice SQLite FTS5 con BM25, fragmentos y citas.
6. Publica un artefacto temporal de siete días, sin subir documentos a Git.

Comandos locales:

```bash
python scripts/prepare_portfolio_corpus.py \
  --source-dir /ruta/Portfolio/Papers \
  --output-dir /tmp/ronin-portfolio-rag/source \
  --source-revision fffc234fdf3f82b6a90d56ae9b190d1c0de79690

python scripts/build_portfolio_rag_index.py \
  --source-dir /tmp/ronin-portfolio-rag/source \
  --output-dir /tmp/ronin-portfolio-rag/index
```

## Recuperación condicionada por incertidumbre

`ronin.retrieval.PortfolioRetriever` consulta SQLite FTS5 en modo solo lectura y devuelve fragmentos con ruta, hash de documento y hash del fragmento. `retrieve_if_uncertain(query, uncertainty, threshold)` no consulta el índice por debajo del umbral.

**Limitación actual:** el modelo RONIN todavía no expone una incertidumbre epistémica calibrada. El helper no se conecta automáticamente al generador; el llamador debe suministrar una puntuación calibrada. No se debe fingir que una probabilidad de token es confianza factual. La integración automática queda pendiente de construir y validar el detector de abstención/incertidumbre.

## Manifiestos y seguridad

- `manifest.json`: lista de documentos y SHA-256 del JSONL.
- `rag-manifest.json`: revisión, hashes del manifiesto y del índice, número de documentos y chunks.
- `portfolio.sqlite3`: índice FTS5, no contiene pesos ni participa en gradientes.
- No imprimir contenido sensible en informes. El escáner de credenciales es básico y no sustituye revisión humana.

El gate oficial requiere este índice RAG, además de las 16 bibliotecas de entrenamiento. Portfolio queda fuera de los 16 y fuera de los pesos.
