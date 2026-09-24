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

- [ ] **B2. Notebook `notebooks/modelo_celdas.ipynb`.** Rasgos por celda (tipo, regex de dia/hora/CP, posicion, vecinos) + RandomForest de scikit-learn. Separar 250/50. Guardar el modelo con joblib en `modelos/modelo_celdas.joblib`: este archivo SI se sube a git (la app publicada lo necesita).
  Hecho cuando: >=98% de celdas bien clasificadas en el examen.

- [ ] **B3. Lector flexible (`lector_excel.py`).** Usa el modelo para extraer las reservas y devuelve tambien la confianza.
  Hecho cuando: >=97% de reservas correctas en los Excels de examen.

- [ ] **B4. Pagina "Importar" en el panel.** Subir Excel, vista previa editable con avisos, el gerente confirma, se guarda con `negocio_id`. Preguntar antes de crear tablas nuevas (perfil por club).

- [ ] **B5. Respaldo con Gemini solo cuando la confianza sea baja.** Enviar la estructura con nombres seudonimizados, recibir JSON.
  Hecho cuando: sin clave o si Gemini falla, la app sigue funcionando.

---

## Antes del primer cliente real (checklist para Diego, no para la IA)
- Pasar Gemini al plan de pago (sin uso de datos para entrenar) o cambiar de proveedor.
- Contrato de encargado del tratamiento (RGPD) con el club y DPA de Supabase/Google.
- Revisar que ninguna consulta se salta el filtro por `negocio_id`.
