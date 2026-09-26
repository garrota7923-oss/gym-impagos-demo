# TAREAS.md — Plan de trabajo (lo que falta + IA incrustada)

Cómo usar este archivo (Claude y Codex):
- Lee SOLO la tarea que Diego te indique (o la primera sin marcar). No leas el resto.
- Una tarea por sesión: plan corto → OK de Diego → programar → `py_compile` → Diego lanza `/codex:review` → marcar `[x]` aquí y actualizar ESTADO.md.
- Las reglas de AGENTS.md mandan (preguntar antes de tocar el esquema de la BD, las dependencias, la seguridad, etc.).

Objetivo: que la demo convenza a un club en 5 minutos. Primero lo que ayuda a vender, luego la IA.

---

## FASE A — Lo que falta para vender (sin IA)

(A1-A5 terminadas: ver HECHO.md)

---

## FASE B — IA incrustada en la app

Decisiones ya tomadas (no las cambies sin preguntar):
- Proveedor: API de Gemini (modelo Flash-Lite, en el plan gratuito de Google AI Studio). El nombre del modelo va en una constante, fácil de cambiar.
- En el plan gratuito, Google puede usar lo que se le envía para mejorar sus productos. Por eso **solo se usa con datos inventados**. Antes del primer cliente real hay que pasar al plan de pago (céntimos al mes) → avisar a Diego.
- **Nunca se envían nombres, teléfonos ni emails reales al modelo.** Se envían cabeceras y ejemplos seudonimizados (p. ej. "Nombre_1", "6XXXXXXXX").
- La IA propone y el gerente confirma. Nada se escribe en la BD sin su OK.
- Si la IA falla o no hay clave, la app sigue funcionando (hay un plan B sin IA).
- Clave en `st.secrets["GEMINI_API_KEY"]`. Diego la añade él mismo. Nunca en el código ni en el chat.

Dependencias nuevas de esta fase (scikit-learn, joblib, jupyter): pedir OK a Diego una sola vez para todas.

Plan completo y principios: `examen/PLAN_IMPORTADOR.md`. Reglas y metricas del examen: `examen/LEEME.md`.
`examen/` es solo para medir: prohibido entrenar con ella o ajustar el codigo a esos archivos concretos.

- [ ] **B3b. Normalizadores** (la lectura, B3a, esta hecha: `lector_archivos.py`). Fechas (dd/mm/aaaa, dd/mm/aa, ISO, "1 de octubre", numero de serie de Excel; siempre dia/mes), importes, Si/No, telefonos (9 digitos), nombres ("Apellidos, Nombre", apellidos en 2 columnas). Tests unitarios de cada uno en `tests/`.
  Hecho cuando: `python -m unittest discover tests` pasa, con casos inventados de cada formato del plan.

- [ ] **B4. Mapeo de listas.** Socios y pagos, incluido el formato ancho (un mes por columna).
  Incluye duplicados casi exactos dentro del mismo archivo (mismo telefono normalizado y nombre sin tildes, p. ej. "0034 600..." y "600..."): el lector solo quita los exactos.
  Hecho cuando: >=98% de filas correctas y 0 filas de mas en `examen/listas/`.

- [ ] **B5. Lector de cuadriculas.** Modelo de celdas y separacion de varios nombres por celda.
  Hecho cuando: >=98% de reservas correctas en `examen/cuadriculas/`.

- [ ] **B6. Pagina "Importar".** Vista previa editable, errores y avisos, deteccion de duplicados, transaccion, `lote_id` y "Deshacer". Preguntar antes de cambiar el esquema de la BD.

- [ ] **B7. Perfil por club y respaldo con Gemini.** Solo si la confianza es baja; sin clave, la app sigue funcionando.

- [ ] **B8. Informe del examen.** Script `examen/evaluar.py` que saca las 4 metricas del LEEME por familia. Se ejecuta en cada PR del importador.

---

## Antes del primer cliente real (checklist para Diego, no para la IA)
- Pasar Gemini al plan de pago (sin uso de datos para entrenar) o cambiar de proveedor.
- Contrato de encargado del tratamiento (RGPD) con el club y DPA de Supabase/Google.
- Revisar que ninguna consulta se salta el filtro por `negocio_id`.
