# TAREAS.md — Plan de trabajo (lo que falta + IA incrustada)

Cómo usar este archivo (Claude y Codex):
- Lee SOLO la tarea que Diego te indique (o la primera sin marcar). No leas el resto.
- Una tarea por sesión: plan corto → OK de Diego → programar → `py_compile` → Diego lanza `/codex:review` → marcar `[x]` aquí y actualizar ESTADO.md.
- Las reglas de AGENTS.md mandan (preguntar antes de tocar el esquema de la BD, las dependencias, la seguridad, etc.).

Objetivo: que la demo convenza a un club en 5 minutos. Primero lo que ayuda a vender, luego la IA.

---

## FASE A — Lo que falta para vender (sin IA)

- [x] **A1. Atrasados en Cobros.** Divide el indicador actual en dos recuadros lado a lado: "Pendiente este mes" (el de ahora) y "Atrasado" (pendientes de meses anteriores: importe y número de cobros). Mismo estilo y misma consulta segura por `negocio_id`.
  Hecho cuando: los dos números suman el total de "Pendientes de pago" de la lista.

- [ ] **A2. Recordar a todos los atrasados.** En Cobros, un botón "Recordar a todos" que muestre la lista de atrasados, cada uno con su enlace de WhatsApp (reutiliza `whatsapp()` de comun.py) y un mensaje educado ya escrito. Sin API de WhatsApp: el gerente pulsa cada enlace. Registrar un `evento` por cada recordatorio.
  Hecho cuando: con 3 clics el gerente tiene abiertos los WhatsApp de los que deben.

- [ ] **A3. Datos demo siempre frescos.** Script o botón (solo para el usuario demo) que regenere los datos inventados, para que la demo no se quede vieja ni rota tras enseñarla. Pregunta a Diego antes de tocar Supabase.
  Hecho cuando: tras "trastear" en una demo, un clic la deja como nueva.

---

## FASE B — IA incrustada en la app

Decisiones ya tomadas (no las cambies sin preguntar):
- Proveedor: API de Gemini (modelo Flash-Lite, en el plan gratuito de Google AI Studio). El nombre del modelo va en una constante, fácil de cambiar.
- En el plan gratuito, Google puede usar lo que se le envía para mejorar sus productos. Por eso **solo se usa con datos inventados**. Antes del primer cliente real hay que pasar al plan de pago (céntimos al mes) → avisar a Diego.
- **Nunca se envían nombres, teléfonos ni emails reales al modelo.** Se envían cabeceras y ejemplos seudonimizados (p. ej. "Nombre_1", "6XXXXXXXX").
- La IA propone y el gerente confirma. Nada se escribe en la BD sin su OK.
- Si la IA falla o no hay clave, la app sigue funcionando (hay un plan B sin IA).
- Clave en `st.secrets["GEMINI_API_KEY"]`. Diego la añade él mismo. Nunca en el código ni en el chat.

- [ ] **B1. Pieza base de IA (`ia.py`).** Una función `pedir_json(instrucciones, datos, esquema)` que llame a Gemini con salida JSON estructurada, un tiempo máximo de espera, reintento corto y errores claros en español. Si no hay clave → devuelve `None` y la app sigue sin IA. Incluye una función para seudonimizar un DataFrame (nombres, teléfonos, emails).
  Dependencia nueva (el SDK oficial de Google o `requests`): proponla y espera el OK de Diego.
  Hecho cuando: una prueba con datos inventados devuelve un JSON válido, y sin clave no rompe nada.

- [ ] **B2. Importar el Excel de un club (página "Importar").** Flujo:
  1. El gerente sube un .xlsx o .csv (se lee en local con pandas).
  2. Se envían al modelo SOLO las cabeceras y unas 5 filas seudonimizadas → el modelo devuelve el mapeo columna → campo (nombre, apellidos, teléfono, email, plan, fecha de alta, último pago, importe).
  3. Plan B sin IA: detección por reglas (regex de teléfono/email/fecha/importe).
  4. Validación local (teléfono con `tel_ok`, fechas legibles, importes numéricos) y vista previa editable con los avisos marcados.
  5. El gerente pulsa "Importar" → se inserta con su `negocio_id`.
  Para guardar el mapeo por negocio hace falta una tabla nueva → pregunta a Diego antes.
  Hecho cuando: un Excel inventado con columnas raras ("Tlf.", "Cuota €", "Alta") se importa bien en menos de 2 minutos.

- [ ] **B3. Asistente del gerente (más adelante).** Caja de preguntas ("¿quién debe más de 2 meses?", "¿quién lleva 3 semanas sin venir?"). El modelo SOLO elige una de varias consultas ya programadas y seguras, con sus parámetros. **Nunca escribe SQL.** El resultado se calcula en local.
  Hacerlo solo después de B2 y si algún club lo pide.

- [ ] **B4. Riesgo de baja con ML (portfolio, opcional).** Modelo clásico de scikit-learn con datos inventados (días sin venir, antigüedad, impagos) que marque a los socios con riesgo de baja. Enseñar las métricas en un notebook aparte.

---

## Antes del primer cliente real (checklist para Diego, no para la IA)
- Pasar Gemini al plan de pago (sin uso de datos para entrenar) o cambiar de proveedor.
- Contrato de encargado del tratamiento (RGPD) con el club y DPA de Supabase/Google.
- Revisar que ninguna consulta se salta el filtro por `negocio_id`.
