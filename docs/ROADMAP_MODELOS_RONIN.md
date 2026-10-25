# Hoja de ruta: familia de modelos RONIN

## Objetivo de producto

El nombre público de un modelo debe expresar el número real de parámetros, no el tamaño del archivo ni la cantidad de parámetros activos aproximada:

- **Ronin-0.6B**: modelo con aproximadamente 0,6 mil millones de parámetros.
- **Ronin-1.5B**, **Ronin-3B**, etc.: usar solo cuando el conteo real del artefacto coincida aproximadamente.
- Durante la investigación, el artefacto de esta búsqueda se denomina `Ronin-0.6B-Fusion-Exp-001`. No publicar el nombre estable `Ronin-0.6B` como una versión aprobada hasta superar los criterios de evaluación y procedencia de este documento.

La cuantización (Q4, Q8, etc.) cambia el tamaño en disco y el coste de inferencia, no el número nominal de parámetros. Un archivo de 300 MB no demuestra que el modelo tenga 0,3B parámetros.

## Aclaración esencial: fusionar no es preentrenar desde cero

Hay tres trabajos diferentes que no deben confundirse:

1. **Fusión de checkpoints**: combina pesos ya entrenados. Los modelos deben tener correspondencia semántica entre tensores; tener la misma forma o tokenizer no garantiza que el promedio sea útil. El resultado hereda dependencias técnicas y obligaciones de licencia de sus componentes.
2. **Entrenamiento adicional o fine-tuning**: parte de pesos preexistentes y los adapta a datos nuevos. No es entrenamiento desde cero.
3. **Preentrenamiento desde inicialización aleatoria**: define arquitectura y tokenizer, inicializa pesos nuevos y entrena sobre un corpus de gran escala. Una fusión puede servir como profesor para destilación o como referencia experimental, pero el modelo alumno entrenado desde cero es un artefacto distinto.

Por tanto, la ruta práctica recomendada es primero investigar una fusión reproducible de modelos compatibles de la familia Qwen3-0.6B. Si el objetivo final es un modelo genuinamente propio desde inicialización aleatoria, esa será una segunda línea de trabajo, con corpus, tokenizer, presupuesto de entrenamiento y evaluación propios. No se debe llamar “entrenado desde cero” al checkpoint promediado.

## Pipeline de investigación propuesto

### Fase 0 — Reproducibilidad y gobernanza

- Fijar SHA de revisión de cada repositorio de Hugging Face, incluidos el modelo base y cada candidato.
- Guardar en cada informe la huella del experimento, revisiones, licencias declaradas, configuración, método, prompts y parámetros.
- Invalidar resultados cacheados si cambia cualquiera de esos elementos.
- No tratar una licencia ausente como permiso; la lista automática solo sirve para priorizar la revisión manual.
- No descargar ni ejecutar código remoto de modelos durante la auditoría salvo necesidad justificada.

### Fase 1 — Candidatos

Para cada candidato, comprobar de forma separada:

- Linaje declarado y revisión inmutable.
- Arquitectura y configuración completas.
- Tokenizer y asignación exacta de IDs, no solo tamaño del vocabulario.
- Claves, formas, tipos y significado de tensores; pesos atados y buffers no flotantes.
- Licencia del modelo base y de los ajustes, restricciones de uso y atribución.
- Si el repositorio contiene pesos completos o únicamente adaptadores.

Un candidato que falla una comprobación se excluye con una razón registrada; no se arregla la incompatibilidad silenciosamente.

### Fase 2 — Métodos de fusión

El promedio lineal de pesos es el primer baseline, no el método final garantizado. Comparar, cuando los linajes y licencias lo permitan:

- Modelo base sin cambios.
- Fine-tunes individuales.
- Interpolación base/candidato con pesos pequeños y barrido controlado.
- SLERP u otros métodos geométricos solo si los supuestos son aplicables.
- TIES/DARE u otros métodos de combinación de deltas, midiendo sensibilidad y regresiones.
- Combinaciones múltiples únicamente tras demostrar que cada candidato aporta valor. Evitar enumeración exponencial sin hipótesis concreta.

Todas las variantes deben usar las mismas revisiones y condiciones de inferencia. No mezclar cuantización con la evaluación de la fusión: primero comparar pesos equivalentes en precisión comparable; cuantizar después y volver a medir.

### Fase 3 — Evaluación en dos niveles

**Filtro barato de desarrollo:** pruebas exactas de matemáticas/código, calidad del español, seguimiento de instrucciones, incertidumbre, seguridad y latencia. Los chequeos de palabras clave son solo señales de depuración.

**Confirmación independiente:** conjunto de pruebas reservado que no se usa para escoger alfa ni candidato; benchmarks de razonamiento, conocimiento, código, español y seguridad; comparación base/candidato con idéntica configuración; varias semillas cuando aplique; evaluación humana ciega de respuestas emparejadas.

Informar por tarea, intervalos o variabilidad, latencia, memoria pico, tamaño real y fallos. No declarar mejora por una única puntuación agregada. Los resultados de lm-evaluation-harness son útiles, pero no sustituyen una evaluación española ni una revisión humana.

### Fase 4 — Promoción y artefacto

Solo promover cuando el candidato:

1. Supere un umbral predefinido en un conjunto reservado.
2. No presente regresiones críticas en seguridad, español, código o razonamiento.
3. Sea reproducible a partir de revisiones fijas.
4. Tenga procedencia/licencias revisadas.
5. Cumpla límites de memoria, latencia y tamaño del dispositivo destino.
6. Pase tests de empaquetado y smoke tests reales.

El checkpoint experimental no debe reemplazar automáticamente el modelo de la app. Debe convertirse por separado al formato de destino (por ejemplo ONNX), cuantizarse, verificarse numéricamente y probarse en Android. Registrar la diferencia entre el checkpoint fuente, la conversión y el modelo empaquetado.

## Criterios de parada

- Si ninguna interpolación supera al modelo base, no exportar un ganador y no aumentar el presupuesto automáticamente.
- Si un candidato empata en el filtro heurístico, tratarlo como empate; no como mejora.
- Si los candidatos compatibles no mejoran en evaluación independiente, cerrar esa línea y revisar datos, objetivo de entrenamiento o métodos.
- No afirmar que la fusión “crea inteligencia nueva” sin evidencia experimental.

## Estado conocido de esta línea

El barrido previo informó que ninguna interpolación probada superó estrictamente al modelo base en su pantalla heurística de 14 comprobaciones; por tanto, no se exportó un checkpoint validado. El directorio experimental `Ronin-0.6B-Fusion-Exp-001` solo se crea si una interpolación supera ese filtro, y su nombre no equivale a una aprobación de calidad. Es una conclusión negativa útil, no una demostración de que todos los métodos de fusión fallen.

El workflow debe considerar válido un checkpoint solo cuando el informe de la ejecución actual declara finalización, mejora heurística estricta y una ruta de artefacto existente. Después se ejecuta la confirmación independiente. Nunca basta con que exista una carpeta antigua restaurada desde caché.
