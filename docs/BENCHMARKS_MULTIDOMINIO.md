# Benchmarks multidominio y ciclos de entrenamiento

## Protocolo

El workflow manual «Ciclos de entrenamiento y evaluación multidominio» ejecuta hasta cinco entrenamientos independientes desde cero, con semillas configurables. Por defecto usa 1.000 pasos y las semillas 1337, 2027 y 42.

Cada ciclo evalúa el checkpoint final en dos planos que no deben confundirse:

1. **Modelado de lenguaje:** cross-entropy, perplejidad y bits por byte (BPB) en la partición de validación del corpus público preparado por el proyecto.
2. **Piloto de dominios:** exactitud por dominio y por capacidad en `benchmarks/domains_v1.jsonl`, con matemáticas, física, química, biología, programación, historia, estadística, derecho, economía, lingüística, criptografía, clima, filosofía, ingeniería y arte.

El benchmark piloto usa la probabilidad del siguiente byte para elegir A/B/C/D. Su azar uniforme es 25 %. No es una prueba de razonamiento abierto ni de generación conversacional. Tiene solo 23 preguntas: sirve para comprobar el circuito y detectar señales muy preliminares, no para declarar competencia. Debe crecer antes de tomar decisiones de arquitectura o de producto.

## Reproducibilidad

Cada informe registra SHA-256 del checkpoint, del dataset y del corpus, paso de entrenamiento, semilla y desglose por dominio/capacidad. Los ciclos no comparten pesos: cada uno parte de inicialización aleatoria. Los checkpoints se conservan solo durante el trabajo de Actions y nunca se publican como artefactos; el artefacto final contiene métricas JSON.

## Cómo lanzar ciclos

En GitHub: Actions → «Ciclos de entrenamiento y evaluación multidominio» → Run workflow. Elegir pasos y semillas. No activar ni consultar el holdout: permanece reservado.

## Próximas ampliaciones

- Aumentar cada dominio a cientos de ítems revisados y equilibrados.
- Añadir pruebas de respuesta abierta con rúbricas adjudicadas por humanos.
- Medir calibración (Brier, ECE y curvas de fiabilidad), abstención, contradicción, trazabilidad de evidencia y robustez ante premisas falsas.
- Separar desarrollo, validación y test sellado; no seleccionar tutores ni ajustar prompts sobre el test.
- Repetir cada experimento con varias semillas y comparar medias, dispersión e intervalos de confianza.
