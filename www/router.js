// Router local de RONIN-IA. Determinista, sin red ni llamadas adicionales a modelos.
const RULES = {
  coding: [
    /\b(c[oó]digo|programa|programar|programaci[oó]n|debug|depura|error en|stack trace|javascript|typescript|python|java|html|css|sql|api|regex|algoritmo|funci[oó]n|script|terminal|bash|git|github)\b/i,
  ],
  math: [
    /\b(matem[aá]tica|matem[aá]ticas|ecuaci[oó]n|derivada|integral|probabilidad|estad[ií]stica|geometr[ií]a|[áa]lgebra|demuestra|calcula|resuelve)\b/i,
    /\b\d+\s*[+*/=^-]\s*\d+\b/,
  ],
  language: [
    /\b(traduce|traducci[oó]n|corrige|redacta|reescribe|resume|resumen|gram[aá]tica|ortograf[ií]a|estilo|email|correo|poema|historia|en ingl[eé]s|en espa[nñ]ol)\b/i,
  ],
  instruction: [
    /\b(sigue exactamente|formato json|solo responde|responde solo|no incluyas|en una tabla|paso a paso|lista numerada|cumple estas instrucciones)\b/i,
  ],
};

const PROFILES = {
  coding: 'Actúa como especialista en programación. Ofrece código ejecutable, detecta supuestos, explica brevemente y señala riesgos o pruebas relevantes. No inventes APIs.',
  math: 'Actúa como especialista en matemáticas. Resuelve de forma ordenada, comprueba el resultado cuando sea posible y declara cualquier supuesto.',
  language: 'Actúa como especialista en idiomas y redacción. Respeta el idioma, el tono y el formato solicitados; no añadas explicaciones si solo se pide una traducción.',
  instruction: 'Prioriza cumplir exactamente las restricciones de formato y las instrucciones válidas del usuario. Comprueba la salida antes de responder.',
  general: 'Responde con claridad y precisión en el idioma del usuario. Distingue hechos de incertidumbre y pregunta solo si falta información esencial.',
};

/**
 * Devuelve la categoría, señales detectadas y perfil para el prompt.
 * Las reglas se ordenan por prioridad para que los casos ambiguos sean estables.
 */
export function routeRequest(query) {
  const text = String(query ?? '').trim();
  const signals = Object.fromEntries(
    Object.entries(RULES).map(([category, patterns]) => [
      category,
      patterns.some(pattern => pattern.test(text)),
    ]),
  );
  const priority = ['coding', 'math', 'language', 'instruction'];
  const category = priority.find(name => signals[name]) ?? 'general';
  return {
    category,
    profile: PROFILES[category],
    signals: Object.keys(signals).filter(name => signals[name]),
    // El único modelo conectado actualmente. No declarar expertos separados hasta integrarlos.
    model: 'onnx-community/Qwen3-0.6B-ONNX',
  };
}
