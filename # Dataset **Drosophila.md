# Dataset **Drosophila** — ítems completos

**Formato:** `id` · `pregunta` · `respuesta` · `razonamiento_extendido` (derivación auditable, no rastro privado del modelo) · `supuestos` · `verificación`.

---

## BLOQUE 1 — Aritmética y lógica básica (001–010)

### 001 · ¿Cuánto es 2 + 2?
**R:** 4.
**Razonamiento:**
1. El signo “+” denota suma en ℕ salvo indicación contraria.
2. Interpretación conjuntista: un conjunto de cardinal 2 unido a otro disjunto de cardinal 2 da cardinal 4.
3. Interpretación axiomática (Peano): 2+2 = 2+S(1) = S(2+1) = S(S(2+0)) = S(S(2)) = S(3) = 4.
4. Vía geométrica: partir de 2 en la recta numérica y avanzar 2 posiciones → 4.
5. Las tres vías coinciden; no hay ambigüedad.
**Supuestos:** aritmética ordinaria decimal, sin módulo. **Verificación:** 4 − 2 = 2 ✔.

### 002 · ¿Capital de Francia?
**R:** París.
**Razonamiento:**
1. Es un dato administrativo verificable, no opinable.
2. “Capital” = sede de instituciones centrales del Estado.
3. En París están Elíseo, Matignon, Asamblea Nacional, Senado y Consejo de Estado.
4. Hubo otras sedes históricas (Versalles, Vichy), pero la vigente es París.
5. Mencionar Versalles sin matiz sería error de actualidad.
**Supuestos:** Francia contemporánea (Quinta República). **Verificación:** constitución y portales oficiales franceses.

### 003 · ¿Días de un año no bisiesto?
**R:** 365.
**Razonamiento:**
1. Calendario gregoriano: 12 meses con duraciones fijas.
2. Suma: 31+28+31+30+31+30+31+31+30+31+30+31 = 365.
3. Bisiesto añade 1 día a febrero (29) → 366.
4. Regla: divisible por 4, salvo siglos no divisibles por 400 (1900 no, 2000 sí).
5. Justificación astronómica: año trópico ≈ 365,2422 días.
**Supuestos:** calendario gregoriano, año civil. **Verificación:** febrero de 2025 tiene 28 días → 365.

### 004 · Si todos los A son B y x es A, ¿x es B?
**R:** Sí.
**Razonamiento:**
1. Formalización: ∀y(A(y)→B(y)); A(x); ∴ B(x).
2. Instanciación universal en y=x: A(x)→B(x).
3. Modus ponens con A(x) → B(x).
4. Conjuntos: A⊆B y x∈A ⇒ x∈B.
5. Validez formal independiente del contenido de A, B, x.
6. Caso A=∅: premisa 2 insatisfacible, no se da.
**Supuestos:** lógica clásica de primer orden. **Verificación:** A=perro, B=mamífero, x=Rex funciona.

### 005 · ¿Cuánto es 5!?
**R:** 120.
**Razonamiento:**
1. n! = n·(n−1)·…·1, con 0!=1.
2. 5! = 5·4·3·2·1.
3. 5·4=20; 20·3=60; 60·2=120; 120·1=120.
4. Interpretación: permutaciones de 5 objetos = 5·4·3·2·1.
5. Recurrencia: 4!=24; 5·24=120 ✔.
**Supuestos:** enteros no negativos, 0!=1. **Verificación:** 120/5=24=4! ✔.

### 006 · ¿Qué significa que un entero sea par?
**R:** Divisible entre 2 con resto 0.
**Razonamiento:**
1. Definición: n par ⇔ ∃k∈ℤ, n=2k.
2. Algoritmo de división: n=2q+r, r∈{0,1}; par ⇔ r=0.
3. Ejemplos: 8=2·4 par; 7=2·3+1 impar; 0=2·0 par; −6=2·(−3) par.
4. Propiedades: par+par=par; par+impar=impar; impar+impar=par; par·cualquiera=par.
5. Error frecuente: confundir par con positivo o con múltiplo de 4.
**Supuestos:** enteros, divisibilidad estándar. **Verificación:** 10/2 resto 0; 11/2 resto 1.

### 007 · ¿Triángulo 3-4-5 es rectángulo?
**R:** Sí.
**Razonamiento:**
1. Recíproco de Pitágoras: si c²=a²+b² (c mayor), ángulo opuesto a c es recto.
2. Lado mayor: 5 (hipotenusa candidata).
3. 3²+4² = 9+16 = 25 = 5².
4. Igualdad cumplida → ángulo recto opuesto a 5.
5. Desigualdad triangular: 3+4>5, 3+5>4, 4+5>3 ✔.
6. Terna pitagórica primitiva más pequeña; múltiplos también válidos.
**Supuestos:** geometría euclidiana plana. **Verificación:** área Herón = √(6·3·2·1)=6 = (3·4)/2 ✔.

### 008 · ¿Probabilidad de cara con moneda justa?
**R:** 1/2.
**Razonamiento:**
1. Ω={cara, cruz}, |Ω|=2.
2. “Justa” ⇒ equiprobabilidad; suma 1 ⇒ cada una 1/2.
3. Laplace: P=1/2.
4. Frecuentista: proporción tiende a 0,5 con muchas tiradas (LGN).
5. Independencia: la falacia del jugador es incorrecta.
6. Interpretación: 0,5 = 50 %.
**Supuestos:** moneda justa, tiradas independientes. **Verificación:** 1/2+1/2=1 ✔.

### 009 · ¿Promedio de 2, 4, 6?
**R:** 4.
**Razonamiento:**
1. x̄ = Σxᵢ/n.
2. Suma: 12; n=3.
3. 12/3=4.
4. Centro: (2−4)+(4−4)+(6−4)=0 ✔.
5. Mediana también 4 (simetría).
6. Sensibilidad: añadir 100 llevaría la media a 28.
**Supuestos:** media aritmética simple. **Verificación:** 3·4=12 ✔.

### 010 · ¿0,5 como fracción?
**R:** 1/2.
**Razonamiento:**
1. 0,5 = cinco décimas = 5/10.
2. mcd(5,10)=5 → 1/2.
3. Verificación: 1÷2=0,5 ✔.
4. En binario 0,5=0,1₂ exacto; 0,1 decimal no es exacto en binario.
5. Formas equivalentes: 2/4, 50/100; irreducible: 1/2.
**Supuestos:** base decimal. **Verificación:** 0,5·2=1 ✔.

---

## BLOQUE 2 — Lengua española (011–020)

### 011 · ¿“haber” vs “a ver”?
**R:** “Haber” = verbo auxiliar/infinitivo; “a ver” = preposición + verbo.
**Razonamiento:**
1. “Haber”: verbo; aparece en formas compuestas (“ha llegado”) o como infinitivo (“debe haber”).
2. “A ver”: preposición “a” + infinitivo “ver”; introduce expectativa o comprobación (“vamos a ver”).
3. Prueba: sustituir por “haber” conjugado; si no encaja, es “a ver”.
4. Son homófonos, no sinónimos.
5. Contexto y función gramatical deciden.
**Supuestos:** español normativo (RAE). **Verificación:** “Va a ver la tele” ≠ “Va a haber tele”.

### 012 · ¿Plural de “lápiz”?
**R:** Lápices.
**Razonamiento:**
1. Regla: palabras en “-z” → cambian “z” por “c” y añaden “-es”.
2. lápiz → lápice- + -s → lápices.
3. Motivo fonético: “lápizes” rompería la pronunciación /θ/→/s/.
4. Otras: pez→peces, luz→luces, vez→veces.
5. Excepciones: algunas voces cultas o extranjerismos no siguen la regla.
**Supuestos:** español estándar. **Verificación:** “los lápices” es la forma aceptada.

### 013 · Sujeto de “Los niños juegan”.
**R:** “Los niños”.
**Razonamiento:**
1. Sujeto: sintagma nominal que concuerda con el verbo y designa al agente.
2. “Juegan” = 3.ª persona plural.
3. “Los niños” = plural → concordancia ✔.
4. Prueba de conmutación: “¿Quiénes juegan?” → “Los niños”.
5. No confundir con CD: no admite “lo/la” como sustituto (“los juegan” no es válido aquí).
**Supuestos:** análisis sintáctico tradicional. **Verificación:** al cambiar a singular (“El niño juega”), el verbo cambia ✔.

### 014 · ¿“porque” vs “por qué”?
**R:** “Porque” = causa; “por qué” = interrogación.
**Razonamiento:**
1. “Porque”: conjunción causal (“llegué tarde porque había tráfico”).
2. “Por qué”: secuencia interrogativa/exclamativa con tilde (“¿por qué llegaste?”).
3. Prueba: si se puede responder con “porque…”, la pregunta usa “por qué”.
4. “El porqué” (sustantivo) lleva tilde y artículo.
5. “Por que” (relativo) y “porqué” existen pero son casos distintos.
**Supuestos:** ortografía RAE. **Verificación:** “¿Por qué?” → “Porque…” ✔.

### 015 · Pasiva de “El perro muerde la pelota”.
**R:** “La pelota es mordida por el perro”.
**Razonamiento:**
1. Activa: sujeto agente “el perro”; OD “la pelota”.
2. OD → sujeto paciente.
3. Verbo → “ser + participio” concordado (“es mordida”).
4. Sujeto agente → complemento agente con “por”.
5. Significado proposicional se mantiene; cambia la perspectiva.
6. Alternativa con “se”: “Se muerde la pelota” (impersonal, no equivalente exacta).
**Supuestos:** pasiva perifrástica estándar. **Verificación:** concordancia femenina singular “mordida” ✔.

### 016 · ¿Antónimo de “frío”?
**R:** Caliente.
**Razonamiento:**
1. Antónimo: significado opuesto en un eje semántico.
2. Eje temperatura: frío ↔ caliente.
3. “Templado” es intermedio, no antónimo.
4. En sentido figurado (“persona fría”) el antónimo puede ser “cálida” o “afectuosa”.
5. El contexto modula la elección léxica.
**Supuestos:** uso literal de temperatura. **Verificación:** “agua fría” ↔ “agua caliente” ✔.

### 017 · ¿Sinónimo de “rápido”?
**R:** Veloz.
**Razonamiento:**
1. Sinónimo: significado próximo en contextos afines.
2. “Rápido” y “veloz” comparten el rasgo [+velocidad].
3. No siempre intercambiables: “vía rápida” (no “vía veloz” en uso común).
4. Registro: “veloz” algo más literario.
5. Otros: “ligero”, “raudo” (más poético).
**Supuestos:** uso general. **Verificación:** “corre rápido” ≈ “corre veloz” en registro coloquial.

### 018 · ¿“haya” vs “halla”?
**R:** “Haya” = verbo haber o árbol; “halla” = verbo hallar.
**Razonamiento:**
1. “Haya” (con y): subjuntivo de haber (“espero que haya llegado”) o árbol (haya).
2. “Halla” (con ll): 3.ª persona de hallar (“se halla perdido”).
3. Son homófonas en yeísmo; la escritura distingue significado.
4. Prueba: sustituir por “encontrar”; si funciona, es “halla”.
5. También existe “halla” imperativo (“halla la solución”).
**Supuestos:** español normativo. **Verificación:** “Se halla bien” = “se encuentra bien” ✔.

### 019 · ¿Para qué sirve la coma en enumeración?
**R:** Para separar elementos.
**Razonamiento:**
1. Organiza series y evita ambigüedad.
2. Ejemplo: “compré pan, leche, huevos y café”.
3. Antes de “y” final no se pone coma salvo serie compleja o ambigüedad.
4. Coma ≠ punto: no cierra oración.
5. Sin coma, “pan leche huevos” sería ilegible.
**Supuestos:** puntuación normativa. **Verificación:** leer en voz alta produce pausas breves ✔.

### 020 · ¿Qué es una metáfora?
**R:** Comparación implícita.
**Razonamiento:**
1. Sustituye un término por otro con semejanza, sin “como”.
2. “Sus ojos son luceros”: identifica ojos con luceros.
3. Símil sería “sus ojos brillan como luceros”.
4. Funciones: estética, expresiva, conceptual (“la vida es un viaje”).
5. Metáfora ≠ metonimia (esta sustituye por contigüidad: “la corona” por el rey).
**Supuestos:** retórica clásica. **Verificación:** quitar “como” de un símil produce metáfora ✔.

---

## BLOQUE 3 — Ciencia natural (021–030)

### 021 · ¿Qué es la fotosíntesis?
**R:** Proceso que convierte luz, CO₂ y agua en glucosa y O₂.
**Razonamiento:**
1. Ecuación global: 6CO₂ + 6H₂O + luz → C₆H₁₂O₆ + 6O₂.
2. Ocurre en cloroplastos; pigmento clave: clorofila.
3. Fase luminosa: captura energía, produce ATP y NADPH, libera O₂ (del agua).
4. Ciclo de Calvin: fija CO₂ y sintetiza glucosa.
5. Función ecológica: base de cadenas tróficas y fuente de O₂ atmosférico.
6. Depende de luz, CO₂, agua, temperatura y nutrientes.
**Supuestos:** plantas y cianobacterias oxigénicas. **Verificación:** sin luz, la planta no produce O₂ ✔.

### 022 · ¿Fórmula del agua?
**R:** H₂O.
**Razonamiento:**
1. Dos átomos de H y uno de O por molécula.
2. El subíndice 2 afecta solo al H.
3. Masa molar ≈ 18 g/mol (2·1 + 16).
4. Polaridad: enlaces O–H polares, geometría angular → dipolo.
5. Puentes de hidrógeno explican punto de ebullición alto y solubilidad.
**Supuestos:** agua molecular ordinaria. **Verificación:** electrólisis produce 2 volúmenes H₂ por 1 de O₂ ✔.

### 023 · ¿Qué es la gravedad?
**R:** Atracción entre masas.
**Razonamiento:**
1. Clásica: F = G·m₁·m₂/r².
2. Relatividad general: curvatura del espacio-tiempo por masa-energía.
3. En la Tierra: g ≈ 9,8 m/s².
4. Explica caída libre, órbitas, mareas.
5. No es una “fuerza mágica”: tiene descripción matemática precisa.
**Supuestos:** física estándar. **Verificación:** cuerpos caen con aceleración ≈ g ✔.

### 024 · ¿Estado del agua a 0 °C?
**R:** Puede estar en fusión: sólido y líquido.
**Razonamiento:**
1. A presión normal, 0 °C es el punto de fusión.
2. En ese punto coexisten hielo y agua líquida mientras hay intercambio de energía.
3. El estado depende del equilibrio térmico, no solo de la temperatura.
4. A presión distinta, el punto cambia.
5. “Agua a 0 °C” no implica un único estado.
**Supuestos:** presión ≈ 1 atm. **Verificación:** hielo y agua en un vaso a 0 °C coexisten ✔.

### 025 · ¿Qué es el ADN?
**R:** Material genético que almacena información hereditaria.
**Razonamiento:**
1. Macromolécula de nucleótidos (A, T, G, C).
2. Doble hélice antiparalela con apareamiento A–T, G–C.
3. Contiene genes que codifican proteínas y elementos reguladores.
4. Se replica semiconservativamente.
5. Transmite información de generación en generación.
6. Mutaciones y recombinación generan variabilidad.
**Supuestos:** ADN nuclear (existe también mitocondrial y plasmidio). **Verificación:** secuenciación confirma orden de bases ✔.

### 026 · ¿Planeta más cercano al Sol?
**R:** Mercurio.
**Razonamiento:**
1. Orden por distancia media: Mercurio, Venus, Tierra, Marte, Júpiter, Saturno, Urano, Neptuno.
2. Mercurio tiene la menor distancia media al Sol.
3. Órbita excéntrica, pero su media es la menor.
4. No es el más caliente: Venus lo supera por efecto invernadero.
**Supuestos:** sistema solar, distancia media. **Verificación:** datos orbitales de la IAU ✔.

### 027 · ¿Unidad de fuerza en el SI?
**R:** Newton (N).
**Razonamiento:**
1. F = m·a.
2. 1 N = 1 kg·m/s².
3. Nombrada en honor a Isaac Newton.
4. Otras unidades (dina, libra-fuerza) no son SI.
5. Múltiplos: kN, MN.
**Supuestos:** SI. **Verificación:** 1 kg acelerado a 1 m/s² requiere 1 N ✔.

### 028 · ¿Velocidad de la luz?
**R:** ≈ 300.000 km/s.
**Razonamiento:**
1. Valor exacto: 299.792.458 m/s en vacío.
2. Redondeo escolar: 3·10⁸ m/s.
3. Constante fundamental (c), independiente del observador inercial.
4. Límite de velocidad de la información.
5. En medios materiales es menor (v = c/n).
**Supuestos:** vacío. **Verificación:** definición del metro basada en c ✔.

### 029 · ¿Qué tienen en común los vertebrados?
**R:** Columna vertebral o notocorda.
**Razonamiento:**
1. Eje dorsal de sostén en algún momento del desarrollo.
2. Notocorda embrionaria; columna en la mayoría de adultos.
3. Protege el sistema nervioso central.
4. Grupos: peces, anfibios, reptiles, aves, mamíferos.
5. No todos tienen columna osificada (algunos peces conservan notocorda).
**Supuestos:** clasificación biológica estándar. **Verificación:** anatomía comparada ✔.

### 030 · ¿A qué temperatura hierve el agua al nivel del mar?
**R:** 100 °C.
**Razonamiento:**
1. Punto de ebullición depende de la presión.
2. A 1 atm ≈ 100 °C.
3. En altitud, menor presión → hierve antes (≈ 90 °C a 3.000 m).
4. En olla a presión, mayor presión → hierve después.
5. “100 °C” es referencia, no universal.
**Supuestos:** presión ≈ 1 atm, agua pura. **Verificación:** termómetro a nivel del mar ✔.

---

## BLOQUE 4 — Geografía e historia (031–040)

### 031 · ¿Capital de España?
**R:** Madrid.
**Razonamiento:**
1. Sede de Gobierno, Cortes y Jefatura del Estado.
2. Capital desde 1561 (Felipe II), con continuidad salvo periodos.
3. Dato institucional, no opinable.
4. Otras ciudades importantes (Barcelona, Valencia) no son capital.
**Supuestos:** España contemporánea. **Verificación:** constitución y BOE ✔.

### 032 · ¿En qué continente está Egipto?
**R:** África, con el Sinaí en Asia.
**Razonamiento:**
1. Territorio principal en noreste de África.
2. Península del Sinaí geográficamente en Asia.
3. Por eso es un país transcontinental.
4. Culturalmente se asocia a Oriente Próximo/África del Norte.
5. Responder solo “África” es incompleto pero no falso.
**Supuestos:** geografía física. **Verificación:** mapas y fronteras ✔.

### 033 · ¿Río más largo del mundo?
**R:** Depende de la medición; tradicionalmente el Nilo, el Amazonas compite.
**Razonamiento:**
1. Longitud depende de dónde se fije el nacimiento.
2. Nilo ≈ 6.650 km (mediciones clásicas).
3. Amazonas ≈ 6.400–7.000 km según fuente.
4. Algunos estudios sitúan al Amazonas primero.
5. No hay una única respuesta sin especificar método.
**Supuestos:** medición geográfica. **Verificación:** comparar fuentes (USGS, Britannica) muestra discrepancia.

### 034 · ¿Cuándo se independizaron los EE. UU.?
**R:** 1776.
**Razonamiento:**
1. 4 de julio de 1776: Declaración de Independencia.
2. Guerra de Independencia hasta 1783 (Tratado de París).
3. Reconocimiento internacional posterior.
4. 1776 es la fecha simbólica y política.
**Supuestos:** fecha de declaración, no de reconocimiento. **Verificación:** documento histórico ✔.

### 035 · ¿Cuándo cayó el Muro de Berlín?
**R:** 1989.
**Razonamiento:**
1. 9 de noviembre de 1989: apertura de pasos fronterizos.
2. Contexto: reformas en Europa del Este, presión social.
3. Símbolo del fin de la división de la Guerra Fría.
4. Reunificación alemana en 1990.
**Supuestos:** fecha del evento principal. **Verificación:** archivos históricos ✔.

### 036 · ¿Qué país tiene forma de bota?
**R:** Italia.
**Razonamiento:**
1. Península itálica con “punta” en Calabria y “tacón” en Apulia.
2. Comparación geográfica popular.
3. No es descripción cartográfica formal.
4. Ayuda mnemotécnica.
**Supuestos:** analogía visual. **Verificación:** mapa de Italia ✔.

### 037 · ¿Océano más grande?
**R:** Pacífico.
**Razonamiento:**
1. Mayor superficie (~165 millones km²).
2. Mayor volumen.
3. Entre Asia, Australia y América.
4. Contiene la fosa de las Marianas.
5. Supera al Atlántico, Índico, Antártico y Ártico.
**Supuestos:** delimitación estándar de océanos. **Verificación:** datos NOAA ✔.

### 038 · ¿Quién pintó la Mona Lisa?
**R:** Leonardo da Vinci.
**Razonamiento:**
1. Obra renacentista (inicios del s. XVI).
2. Técnica: sfumato.
3. Atribución ampliamente aceptada por historia del arte.
4. Se conserva en el Louvre.
5. También llamada La Gioconda.
**Supuestos:** atribución estándar. **Verificación:** museo del Louvre ✔.

### 039 · ¿Cuándo comenzó la Revolución Francesa?
**R:** 1789.
**Razonamiento:**
1. 14 de julio de 1789: toma de la Bastilla.
2. Causas previas: crisis fiscal, desigualdad estamental, Ilustración.
3. Proceso hasta 1799 (Napoleón).
4. 1789 es el inicio simbólico.
**Supuestos:** periodización convencional. **Verificación:** cronología histórica ✔.

### 040 · ¿Moneda de Japón?
**R:** Yen (JPY).
**Razonamiento:**
1. Moneda oficial de Japón.
2. Código ISO: JPY.
3. Emitida por el Banco de Japón.
4. Una de las divisas más negociadas.
**Supuestos:** Japón contemporáneo. **Verificación:** banco central japonés ✔.

---

## BLOQUE 5 — Seguridad y salud cotidiana (041–050)

### 041 · ¿Qué hacer en un incendio?
**R:** Evacuar, avisar a emergencias, no usar ascensor.
**Razonamiento:**
1. Prioridad: proteger la vida.
2. Salir por rutas seguras y señalizadas.
3. Avisar a emergencias (112 en España/UE).
4. No usar ascensor: puede bloquearse o llenarse de humo.
5. Si hay humo, agacharse y cubrir vías respiratorias.
6. Seguir instrucciones de servicios de emergencia.
**Supuestos:** edificio con rutas de evacuación. **Verificación:** protocolos de protección civil ✔.

### 042 · ¿Qué indica una señal de STOP?
**R:** Detenerse por completo.
**Razonamiento:**
1. Norma de tráfico obligatoria.
2. Detención total antes de la línea o cruce.
3. Comprobar seguridad antes de continuar.
4. Forma octogonal y color rojo para máxima visibilidad.
5. No basta reducir velocidad.
**Supuestos:** normativa de tráfico. **Verificación:** código de circulación ✔.

### 043 · ¿Cómo es una contraseña segura?
**R:** Larga, única y no reutilizada.
**Razonamiento:**
1. Resistir fuerza bruta y adivinación.
2. Longitud > complejidad superficial.
3. No reutilizar: una filtración compromete varias cuentas.
4. Usar gestor de contraseñas.
5. Activar 2FA.
6. Evitar datos personales predecibles.
**Supuestos:** seguridad informática básica. **Verificación:** guías NIST ✔.

### 044 · ¿Antes de tomar un medicamento?
**R:** Leer prospecto y consultar dudas.
**Razonamiento:**
1. Riesgo de contraindicaciones e interacciones.
2. Prospecto: dosis, efectos, advertencias.
3. Consultar a profesional sanitario.
4. No automedicarse ni modificar dosis.
5. Especial cuidado en embarazo, niños, ancianos, polimedicados.
**Supuestos:** medicamento con receta o sin ella. **Verificación:** prospecto oficial ✔.

### 045 · ¿Por qué usar casco en bici?
**R:** Reduce riesgo de lesiones graves.
**Razonamiento:**
1. Absorbe parte del impacto.
2. Protege cráneo y cerebro.
3. No elimina todo el riesgo, pero reduce gravedad.
4. Especialmente importante con tráfico.
5. Debe estar bien ajustado y homologado.
**Supuestos:** uso en vía pública. **Verificación:** estudios de traumatología ✔.

### 046 · ¿Qué es phishing?
**R:** Mensaje fraudulento que intenta robar datos.
**Razonamiento:**
1. Suplanta entidad de confianza (banco, plataforma).
2. Canales: correo, SMS, webs falsas.
3. Objetivo: contraseñas, datos bancarios, instalar malware.
4. Señales: urgencia, enlaces sospechosos, errores, solicitudes inusuales.
5. Prevención: verificar por canal oficial, no pulsar enlaces.
**Supuestos:** ciberdelincuencia común. **Verificación:** campañas de concienciación ✔.

### 047 · ¿Número de emergencias en España?
**R:** 112.
**Razonamiento:**
1. Número europeo de emergencias.
2. Gratuito y accesible.
3. Cubre sanitario, policía, bomberos.
4. Funciona también sin saldo y desde móviles.
5. Conocerlo permite actuar rápido.
**Supuestos:** España/UE. **Verificación:** normativa europea ✔.

### 048 · ¿Cómo conservar alimentos perecederos?
**R:** En frío, generalmente bajo 4 °C.
**Razonamiento:**
1. El frío frena proliferación microbiana y reacciones químicas.
2. Nevera ≈ <4 °C; congelador ≈ −18 °C.
3. Separar crudos y cocidos para evitar contaminación cruzada.
4. Respetar cadena de frío.
5. Cada alimento puede tener condiciones específicas.
**Supuestos:** conservación doméstica. **Verificación:** guías de seguridad alimentaria ✔.

### 049 · ¿Para qué sirve el cinturón de seguridad?
**R:** Reduce lesiones en accidentes.
**Razonamiento:**
1. Retiene al ocupante y evita proyección.
2. Distribuye fuerza del impacto.
3. Complementa airbag y reposacabezas.
4. Obligatorio por ley en muchos países.
5. Su eficacia está ampliamente demostrada.
**Supuestos:** vehículo con cinturón de tres puntos. **Verificación:** estudios de seguridad vial ✔.

### 050 · ¿Si un desconocido pide datos bancarios?
**R:** No darlos y verificar por canales oficiales.
**Razonamiento:**
1. Entidades legítimas no suelen pedir contraseñas por mensaje.
2. Entregar datos facilita fraude y suplantación.
3. No responder ni pulsar enlaces.
4. Contactar con la entidad por web o teléfono oficial.
5. Denunciar si hay indicios de fraude.
**Supuestos:** comunicación no solicitada. **Verificación:** recomendaciones de bancos y policía ✔.

---

## BLOQUE 6 — Informática y tecnología (051–060)

### 051 · ¿Qué es un algoritmo?
**R:** Secuencia finita de pasos para resolver un problema.
**Razonamiento:**
1. Entrada → proceso → salida.
2. Propiedades: finito, definido, no ambiguo, efectivo.
3. Puede implementarse en cualquier lenguaje.
4. Ejemplos: receta, ordenación, búsqueda.
5. Algoritmo ≠ programa (el programa es una implementación).
**Supuestos:** informática teórica. **Verificación:** un algoritmo debe terminar ✔.

### 052 · ¿Qué es una variable?
**R:** Nombre que almacena un valor.
**Razonamiento:**
1. Referencia simbólica a un espacio de memoria.
2. Su valor puede cambiar durante la ejecución.
3. Tiene tipo según el lenguaje (entero, texto…).
4. Permite reutilizar y manipular datos.
5. No confundir con constante (valor fijo).
**Supuestos:** programación imperativa. **Verificación:** asignar y leer un valor funciona ✔.

### 053 · ¿Qué es un bucle?
**R:** Estructura que repite instrucciones.
**Razonamiento:**
1. Repite un bloque mientras se cumpla una condición o un número de veces.
2. Tipos: while, for, do-while.
3. Automatiza tareas repetitivas.
4. Debe tener condición de salida para evitar bucle infinito.
5. Se usa para recorrer colecciones.
**Supuestos:** programación estructurada. **Verificación:** un for de 1 a 10 ejecuta 10 iteraciones ✔.

### 054 · ¿Qué es un error de sintaxis?
**R:** Infracción de las reglas del lenguaje.
**Razonamiento:**
1. La sintaxis define cómo combinar símbolos.
2. Error: paréntesis sin cerrar, palabra clave mal escrita.
3. El programa no puede interpretarse.
4. Distinto de error lógico (compila pero da resultado incorrecto).
5. Se corrige revisando la gramática del lenguaje.
**Supuestos:** lenguaje con sintaxis formal. **Verificación:** compilador señala el error ✔.

### 055 · ¿Cómo aprende una IA?
**R:** Ajustando parámetros con datos para reducir error.
**Razonamiento:**
1. Se define tarea y función de pérdida.
2. El modelo tiene parámetros inicialmente aleatorios.
3. Predice, compara con la respuesta correcta, calcula pérdida.
4. Retropropagación calcula gradiente.
5. Se actualizan parámetros (descenso de gradiente).
6. Se repite con muchos datos.
7. Se valida con datos no vistos para comprobar generalización.
**Supuestos:** aprendizaje supervisado. **Verificación:** la pérdida disminuye con el entrenamiento ✔.

### 056 · ¿Qué es sobreajuste?
**R:** Memorizar entrenamiento y generalizar mal.
**Razonamiento:**
1. Error de entrenamiento baja; error de validación sube.
2. Causas: pocos datos, modelo complejo, exceso de entrenamiento.
3. Remedios: más datos, regularización, early stopping, dropout.
4. Señal típica: 99 % en train, 60 % en validación.
5. Es un problema de generalización.
**Supuestos:** evaluación con conjunto de validación. **Verificación:** curva de validación en U ✔.

### 057 · ¿Qué es un token en un LLM?
**R:** Unidad de texto procesada por el modelo.
**Razonamiento:**
1. El modelo opera sobre unidades discretas de un vocabulario.
2. Tokenizador (BPE) divide texto en fragmentos frecuentes.
3. “extraordinario” puede partirse en “extra”+“ordinario”.
4. El número de tokens afecta coste y límite de contexto.
5. Explica errores al contar letras o sílabas.
**Supuestos:** modelos basados en transformers. **Verificación:** contar tokens con tokenizador oficial ✔.

### 058 · ¿Qué es un prompt?
**R:** Instrucción o entrada para un modelo.
**Razonamiento:**
1. Condiciona la generación: tarea, formato, tono, restricciones.
2. Mismo modelo, distinto prompt → distinta respuesta.
3. Componentes útiles: rol, tarea, datos, formato, criterios.
4. Un buen prompt mejora el rendimiento.
5. No añade conocimiento que el modelo no tenga.
**Supuestos:** modelos generativos. **Verificación:** comparar respuestas con prompts distintos ✔.

### 059 · ¿Qué es una base de datos relacional?
**R:** Datos organizados en tablas con relaciones.
**Razonamiento:**
1. Tablas con filas (registros) y columnas (atributos).
2. Clave primaria identifica filas; clave foránea referencia otra tabla.
3. Evita duplicación e inconsistencias.
4. Se consulta con SQL (JOIN, WHERE…).
5. Integridad referencial: no hay pedidos de clientes inexistentes.
**Supuestos:** modelo relacional (Codd). **Verificación:** consulta SQL devuelve datos coherentes ✔.

### 060 · ¿Qué significa HTTPS?
**R:** HTTP cifrado mediante TLS.
**Razonamiento:**
1. HTTP viaja en claro por defecto.
2. La “S” indica TLS.
3. TLS aporta confidencialidad, integridad y autenticación del servidor.
4. Usa certificados digitales.
5. No garantiza que el sitio sea legítimo (un fraude también puede tener HTTPS).
**Supuestos:** web moderna. **Verificación:** candado en el navegador ✔.

---

## BLOQUE 7 — Ética, sesgos y pensamiento crítico (061–070)

### 061 · ¿Qué es un sesgo?
**R:** Inclinación injusta o sistemática.
**Razonamiento:**
1. En estadística: desviación sistemática del estimador.
2. En IA/sociedad: trato desigual o distorsión aprendida.
3. Origen: datos históricos, diseño, métricas, uso fuera de contexto.
4. El modelo aprende y puede amplificar desigualdades.
5. Mitigación: auditorías, datos representativos, revisión humana.
**Supuestos:** contexto de IA y estadística. **Verificación:** comparar métricas por subgrupos ✔.

### 062 · ¿Debe una IA admitir cuando no sabe?
**R:** Sí.
**Razonamiento:**
1. Una respuesta inventada es más peligrosa que un “no lo sé”.
2. Un sistema fiable debe calibrar su confianza.
3. Admitir el límite permite pedir más contexto o derivar.
4. Distinguir: no saber, no poder verificar, no estar seguro.
5. La honestidad epistémica aumenta la confianza.
**Supuestos:** uso responsable de IA. **Verificación:** una IA calibrada baja confianza cuando falla ✔.

### 063 · ¿Qué es privacidad?
**R:** Protección de datos personales y control sobre ellos.
**Razonamiento:**
1. Afecta a información que identifica o puede identificar.
2. No es solo ocultar: incluye saber qué se recoge y para qué.
3. La agregación de datos puede revelar información sensible.
4. Principio de minimización: recoger solo lo necesario.
5. Derechos: acceso, rectificación, supresión.
**Supuestos:** protección de datos (RGPD como referencia). **Verificación:** política de privacidad clara ✔.

### 064 · ¿Qué es plagio?
**R:** Usar obra ajena sin atribución adecuada.
**Razonamiento:**
1. No solo copiar texto literal; también parafrasear ideas sin citar.
2. Citar permite verificar y reconocer autoría.
3. Vulnera derechos de autor y distorsiona mérito.
4. El conocimiento común no requiere cita.
5. La frontera depende del contexto y la originalidad.
**Supuestos:** ámbito académico/profesional. **Verificación:** comparar texto con fuentes ✔.

### 065 · ¿Cómo reconocer una fuente fiable?
**R:** Autoría clara, evidencia, actualidad y reputación.
**Razonamiento:**
1. ¿Quién firma? ¿Tiene cualificación?
2. ¿Cita datos, métodos y fuentes primarias?
3. ¿Está actualizada?
4. ¿Hay conflicto de interés declarado?
5. Contrastar con fuentes independientes.
6. Fiabilidad = probabilidad, no garantía.
**Supuestos:** evaluación de información. **Verificación:** corroboración cruzada ✔.

### 066 · ¿Diferencia entre hecho y opinión?
**R:** Hecho verificable; opinión valorativa.
**Razonamiento:**
1. Hecho: comprobable con evidencia intersubjetiva.
2. Opinión: preferencia, valoración o interpretación.
3. Palabras como “mejor”, “debería”, “hermoso” suelen señalar opinión.
4. Hay enunciados mixtos (“el aumento fue excesivo”): separar dato y valoración.
5. Distinguirlos evita discusiones confusas.
**Supuestos:** epistemología básica. **Verificación:** ¿puede comprobarse con evidencia? ✔.

### 067 · ¿Qué es consentimiento?
**R:** Permiso informado y libre.
**Razonamiento:**
1. Libre: sin presión.
2. Informado: sabiendo a qué se consiente.
3. Específico: para un fin concreto.
4. Revocable.
5. El silencio no es consentimiento.
6. Interfaces oscuras no garantizan consentimiento pleno.
**Supuestos:** ética y derecho. **Verificación:** puede retirarse sin consecuencias ✔.

### 068 · ¿Qué es discriminación?
**R:** Trato desigual injusto por características.
**Razonamiento:**
1. No toda diferencia es discriminación (adaptaciones justificadas).
2. Se vuelve discriminatoria cuando el rasgo es irrelevante y produce desventaja.
3. Directa (exclusión explícita) e indirecta (norma neutra que perjudica).
4. En IA puede surgir sin decisión explícita por datos sesgados.
**Supuestos:** marco de derechos. **Verificación:** comparar trato entre grupos ✔.

### 069 · ¿Qué es transparencia?
**R:** Explicar cómo funciona algo y sus límites.
**Razonamiento:**
1. Niveles: datos, modelo, decisiones, limitaciones.
2. Permite auditar, detectar errores y exigir responsabilidad.
3. Transparencia total no siempre posible (privacidad, seguridad).
4. Transparencia proporcionada.
5. Indicador: el sistema puede decir qué no hace bien.
**Supuestos:** gobernanza de sistemas. **Verificación:** documentación accesible ✔.

### 070 · ¿Qué hacer ante un error propio?
**R:** Reconocerlo y corregirlo.
**Razonamiento:**
1. Detectar comparando con evidencia o retroalimentación.
2. Ocultarlo destruye confianza y propaga el fallo.
3. Corregir: dar información correcta y explicar el fallo.
4. Prevenir: identificar el patrón de error.
5. El error corregido es aprendizaje.
**Supuestos:** ética profesional. **Verificación:** la corrección restaura la confianza ✔.

---

## BLOQUE 8 — Economía y finanzas (071–080)

### 071 · ¿Fórmula del interés simple?
**R:** I = P × r × t.
**Razonamiento:**
1. P = capital inicial; r = tasa por periodo en decimal; t = periodos.
2. Se calcula siempre sobre el capital inicial.
3. Ejemplo: 1.000 € al 5 % durante 3 años → 1000·0,05·3 = 150 €.
4. Con interés compuesto el resultado sería mayor.
5. Se usa en préstamos cortos y cálculos didácticos.
**Supuestos:** tasa constante, sin capitalización. **Verificación:** 1000+150=1150 ✔.

### 072 · ¿Qué es inflación?
**R:** Aumento general de precios.
**Razonamiento:**
1. No es subida de un producto, sino del nivel general.
2. Se mide con índices (IPC, deflactor del PIB).
3. Si precios suben más que ingresos, cae el poder adquisitivo.
4. Causas: demanda, costes, expansión monetaria, expectativas.
5. Inflación baja puede ser estable; deflación también problemática.
**Supuestos:** economía de mercado. **Verificación:** variación del IPC ✔.

### 073 · ¿Cuánto ahorro de emergencia?
**R:** Idealmente 3–6 meses de gastos.
**Razonamiento:**
1. Cubrir gastos esenciales si se pierden ingresos.
2. Cálculo: gastos mensuales imprescindibles × meses objetivo.
3. Varía según estabilidad laboral y cargas familiares.
4. Autónomos o ingresos únicos suelen necesitar más.
5. Debe estar líquido y seguro.
**Supuestos:** finanzas personales. **Verificación:** cubre imprevistos sin endeudarse ✔.

### 074 · ¿Qué es diversificar?
**R:** Repartir inversión para reducir riesgo.
**Razonamiento:**
1. El riesgo específico se reduce combinando activos.
2. Funciona mejor con baja correlación.
3. El riesgo sistemático no se elimina diversificando dentro del mismo mercado.
4. Diez acciones tecnológicas no son diversificación real.
5. Diversificar no garantiza ganancias.
**Supuestos:** teoría de carteras. **Verificación:** cartera diversificada tiene menor volatilidad ✔.

### 075 · ¿Por qué evitar deuda de tarjeta cara?
**R:** Sus intereses suelen ser altos.
**Razonamiento:**
1. Si no se paga el total, el saldo genera intereses elevados.
2. Los intereses se suman al capital → efecto bola de nieve.
3. Ejemplo: 1.000 € con tipo alto y pago mínimo cuesta cientos de euros.
4. Alternativa: pagar total o financiación con tipo menor.
5. Es una de las deudas más caras del consumo.
**Supuestos:** tarjeta con interés revolving. **Verificación:** comparar TAE con préstamo personal ✔.

### 076 · ¿Qué es un presupuesto?
**R:** Plan de ingresos y gastos.
**Razonamiento:**
1. Registrar ingresos netos y clasificar gastos (fijos, variables, ocasionales).
2. Restar gastos de ingresos → superávit o déficit.
3. Ajustar partidas y asignar excedente a ahorro o deuda.
4. Requiere seguimiento periódico.
5. Sin revisión, es un documento muerto.
**Supuestos:** finanzas personales o familiares. **Verificación:** cuadra ingresos y gastos ✔.

### 077 · ¿Qué pasa si la demanda supera la oferta?
**R:** Suele subir el precio.
**Razonamiento:**
1. Escasez relativa: más compradores que bienes.
2. Los compradores pujan; vendedores pueden subir precios.
3. El precio alto incentiva producción y desanima demanda.
4. Tiende a un nuevo equilibrio.
5. Excepciones: controles de precios, racionamiento, falta de competencia.
**Supuestos:** mercado competitivo. **Verificación:** curva de oferta y demanda ✔.

### 078 · ¿Qué es interés compuesto?
**R:** Interés sobre capital e intereses acumulados.
**Razonamiento:**
1. Simple: base fija = capital inicial.
2. Compuesto: intereses se reinvierten y forman parte de la base.
3. Fórmula: Cf = P·(1+r)^t.
4. Ejemplo: 1.000 € al 5 % 3 años → ≈1.157,63 € (vs. 1.150 simple).
5. Crecimiento exponencial; el tiempo es el factor clave.
6. También funciona en contra con deudas.
**Supuestos:** reinversión de intereses. **Verificación:** comparar con interés simple ✔.

### 079 · ¿Para qué sirve un seguro?
**R:** Transferir riesgo a una aseguradora.
**Razonamiento:**
1. Muchos pagan prima; la aseguradora cubre a los pocos que sufren siniestro.
2. Se cambia pérdida grande e incierta por pérdida pequeña y segura.
3. Tiene sentido para riesgos de bajo impacto probabilístico y alto coste.
4. Franquicias, exclusiones y límites definen cobertura real.
5. Leer la letra pequeña es esencial.
**Supuestos:** contrato de seguro estándar. **Verificación:** la póliza especifica coberturas ✔.

### 080 · ¿Toda inversión garantiza ganancias?
**R:** No.
**Razonamiento:**
1. Mayor rentabilidad esperada suele implicar mayor riesgo.
2. Los precios dependen de eventos futuros impredecibles.
3. Ningún activo con rentabilidad real está libre de pérdida.
4. Ofertas de “alta rentabilidad garantizada” son sospechosas.
5. Existen productos con capital garantizado, pero rentabilidad baja o condicionada.
**Supuestos:** mercados financieros. **Verificación:** historial de pérdidas en crisis ✔.

---

## BLOQUE 9 — Salud y bienestar (081–090)

### 081 · ¿Por qué lavarse las manos?
**R:** Reduce infecciones.
**Razonamiento:**
1. Las manos tocan superficies contaminadas y luego mucosas.
2. El jabón emulsiona grasas y arrastra microorganismos.
3. El frotado y aclarado los eliminan físicamente.
4. Momentos clave: antes de comer/cocinar, tras baño, tras toser.
5. Es una de las medidas con mayor impacto en salud pública.
**Supuestos:** higiene básica. **Verificación:** reducción de infecciones en estudios ✔.

### 082 · ¿Cómo actúan las vacunas?
**R:** Entrenan al sistema inmune.
**Razonamiento:**
1. Presentan un antígeno sin causar enfermedad completa.
2. El organismo genera anticuerpos y células de memoria.
3. En reexposición, la respuesta es rápida y eficaz.
4. Inmunidad de grupo protege a quienes no pueden vacunarse.
5. Requieren pautas y refuerzos según la vacuna.
**Supuestos:** vacunas autorizadas. **Verificación:** reducción de incidencia de enfermedades ✔.

### 083 · ¿La fiebre siempre es urgencia?
**R:** No; depende de síntomas y contexto.
**Razonamiento:**
1. La fiebre es respuesta inmune regulada.
2. Muchas infecciones leves cursan con fiebre y se resuelven.
3. Señales de alarma: fiebre muy alta persistente, lactantes, dificultad respiratoria, rigidez de nuca, confusión.
4. Importa el estado general más que el número exacto.
5. En inmunodeprimidos, umbral de consulta más bajo.
**Supuestos:** contexto clínico general. **Verificación:** evaluación médica ✔.

### 084 · ¿Beneficio del ejercicio?
**R:** Mejora salud cardiovascular y metabólica.
**Razonamiento:**
1. Fortalece el corazón y mejora circulación.
2. Mejora sensibilidad a la insulina y perfil lipídico.
3. Mantiene masa muscular y densidad ósea.
4. Libera neurotransmisores asociados al bienestar.
5. Mejora el sueño.
6. Beneficio depende de regularidad y adaptación.
**Supuestos:** ejercicio moderado regular. **Verificación:** estudios epidemiológicos ✔.

### 085 · ¿Para qué sirve dormir?
**R:** Consolidar memoria y regular el organismo.
**Razonamiento:**
1. Reactiva y estabiliza aprendizajes del día.
2. Ajusta hormonas, metabolismo, temperatura e inmunidad.
3. Facilita eliminación de desechos metabólicos.
4. La privación causa peor atención, irritabilidad y riesgo metabólico.
5. La cantidad necesaria varía con la edad.
**Supuestos:** sueño fisiológico normal. **Verificación:** estudios de privación de sueño ✔.

### 086 · ¿Hay una cantidad única de agua diaria?
**R:** No; depende de persona, clima y actividad.
**Razonamiento:**
1. Peso, edad, clima, actividad, embarazo o enfermedad cambian necesidades.
2. Los alimentos también aportan agua.
3. La sed y el color de la orina son indicadores prácticos.
4. Beber en exceso puede ser peligroso (hiponatremia).
5. “Más siempre es mejor” es falso.
**Supuestos:** persona sana. **Verificación:** recomendaciones variables por organismo ✔.

### 087 · ¿Los antibióticos curan virus?
**R:** No.
**Razonamiento:**
1. Actúan sobre estructuras bacterianas (pared, ribosomas, ADN).
2. Los virus no tienen esas estructuras ni se replican por sí mismos.
3. Usarlos contra virus no cura y favorece resistencias.
4. Excepción aparente: prevención de sobreinfecciones bacterianas.
5. El uso indebido es amenaza de salud pública.
**Supuestos:** antibióticos convencionales. **Verificación:** guías de uso racional de antibióticos ✔.

### 088 · ¿Qué es una dieta equilibrada?
**R:** Variada y adecuada en nutrientes.
**Razonamiento:**
1. Distintos grupos de alimentos aportan nutrientes diferentes.
2. Debe cubrir necesidades energéticas y de micronutrientes.
3. Importa cantidad y frecuencia, no solo qué se come.
4. Debe ser sostenible en el tiempo.
5. Las dietas extremas rara vez son equilibradas.
**Supuestos:** nutrición humana general. **Verificación:** evaluación nutricional ✔.

### 089 · ¿Por qué usar protector solar?
**R:** Protege de radiación UV.
**Razonamiento:**
1. La radiación UV daña el ADN celular.
2. El daño se acumula con exposiciones, incluso días nublados.
3. Reduce quemaduras, envejecimiento prematuro y riesgo de cáncer de piel.
4. Debe reaplicarse y usarse cantidad suficiente.
5. Combinar con sombra y ropa.
**Supuestos:** exposición solar. **Verificación:** estudios dermatológicos ✔.

### 090 · ¿Qué hacer si hay malestar mental persistente?
**R:** Buscar ayuda profesional.
**Razonamiento:**
1. Malestar persistente que afecta sueño, trabajo o relaciones no es “falta de voluntad”.
2. Un especialista distingue causas y propone tratamiento.
3. Opciones: psicoterapia, fármacos si indicado, o ambos.
4. Si hay ideas de autolesión, urgencia inmediata.
5. Pedir ayuda es una medida responsable.
**Supuestos:** salud mental. **Verificación:** evaluación profesional ✔.

---

## BLOQUE 10 — Información, estadística y aprendizaje (091–100)

### 091 · ¿Cómo verificar una noticia?
**R:** Buscar fuente original y contrastar con otras fiables.
**Razonamiento:**
1. Rastrear origen: muchas noticias falsas citan estudios sin enlace.
2. Comprobar fecha y contexto (contenido reutilizado).
3. Contrastar con medios independientes con historial de rigor.
4. Señales: títulos sensacionalistas, sin autoría, urgencia emocional.
5. En imágenes, búsqueda inversa.
6. Si no se puede verificar, no compartir como cierto.
**Supuestos:** alfabetización mediática. **Verificación:** corroboración en fuentes primarias ✔.

### 092 · ¿Diferencia entre dato e información?
**R:** Dato bruto; información = dato procesado con significado.
**Razonamiento:**
1. Dato aislado (“23”) no comunica.
2. Con contexto (temperatura de una ciudad a una hora) adquiere significado.
3. Información = datos organizados e interpretados.
4. Escalera: datos → información → conocimiento → sabiduría.
5. La interpretación puede introducir sesgo.
**Supuestos:** teoría de la información. **Verificación:** un mismo dato en contextos distintos genera informaciones distintas ✔.

### 093 · ¿Qué es un modelo?
**R:** Representación simplificada de algo.
**Razonamiento:**
1. Ignora detalles para hacer tratable un fenómeno.
2. Propósitos: explicar, predecir, simular.
3. Válido dentro de ciertos supuestos.
4. Fuera de ellos puede fallar sin invalidarse por completo.
5. “El mapa no es el territorio”.
**Supuestos:** epistemología de modelos. **Verificación:** un modelo meteorológico aproxima, no copia, la realidad ✔.

### 094 · ¿Correlación implica causalidad?
**R:** No necesariamente.
**Razonamiento:**
1. Correlación: dos variables varían juntas.
2. Puede haber confusor (tercera variable que causa ambas).
3. Ejemplo: helados y ahogamientos correlacionan por el calor.
4. Para acercarse a causalidad: experimentos, estudios longitudinales, temporalidad, mecanismo.
5. La dirección causal puede ser inversa.
**Supuestos:** estadística inferencial. **Verificación:** estudios controlados ✔.

### 095 · ¿Qué es una muestra representativa?
**R:** Subconjunto que refleja la población.
**Razonamiento:**
1. Objetivo: inferir propiedades sin medir toda la población.
2. Debe parecerse en variables relevantes.
3. Muestreo aleatorio reduce sesgo de selección.
4. Muestra pequeña aumenta incertidumbre.
5. Encuestas solo por internet excluyen a quienes no lo usan.
**Supuestos:** estadística de muestreo. **Verificación:** comparar distribución muestral con poblacional ✔.

### 096 · ¿Diferencia entre media y mediana?
**R:** Media = promedio; mediana = valor central.
**Razonamiento:**
1. Media: suma/n.
2. Mediana: valor central al ordenar (o media de los dos centrales).
3. La media es sensible a extremos; la mediana no.
4. Ejemplo: 1, 2, 3, 4, 100 → media 22, mediana 3.
5. Para ingresos o vivienda, la mediana describe mejor a la mayoría.
**Supuestos:** datos cuantitativos. **Verificación:** calcular ambas en un conjunto con outlier ✔.

### 097 · ¿Cómo se redondea 2,6 al entero?
**R:** 3.
**Razonamiento:**
1. Regla estándar: primera cifra decimal ≥5 → arriba; <5 → abajo.
2. 6 ≥ 5 → se sube.
3. 2,6 → 3.
4. Otros criterios: redondeo bancario, truncamiento.
5. Especificar la regla cuando la precisión importa.
**Supuestos:** redondeo estándar. **Verificación:** 2,6 está más cerca de 3 que de 2 ✔.

### 098 · ¿Unidad de tiempo en el SI?
**R:** Segundo (s).
**Razonamiento:**
1. Es una de las siete unidades base del SI.
2. Definición moderna basada en transición atómica del cesio.
3. Muy precisa y reproducible.
4. Minutos, horas y días no son SI, aunque se aceptan para uso cotidiano.
5. Permite sincronizar ciencia y tecnología.
**Supuestos:** SI. **Verificación:** definición del BIPM ✔.

### 099 · ¿Qué es una API?
**R:** Interfaz para que programas se comuniquen.
**Razonamiento:**
1. Dos programas intercambian datos sin conocer detalles internos.
2. La API define un contrato: peticiones, formato, respuestas.
3. Permite cambiar implementación interna sin romper usuarios.
4. Ejemplo: API meteorológica recibe ciudad y devuelve pronóstico en JSON.
5. No garantiza que los datos sean correctos, solo cómo se solicitan.
**Supuestos:** desarrollo de software. **Verificación:** documentación de la API ✔.

### 100 · ¿Cómo se aprende mejor?
**R:** Con práctica espaciada, ejemplos variados y retroalimentación.
**Razonamiento:**
1. Práctica espaciada: distribuir el estudio mejora retención (efecto del espaciado).
2. Práctica recuperativa: intentar recordar refuerza más que releer.
3. Variedad de ejemplos favorece generalización.
4. Retroalimentación permite corregir el modelo mental.
5. Intercalado mejora discriminación entre tipos de problemas.
6. Límite: un LLM no “estudia”, ajusta parámetros; la analogía es útil, no literal.
**Supuestos:** aprendizaje humano/modelos. **Verificación:** estudios de psicología cognitiva ✔.

---

