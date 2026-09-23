# ESTADO.md — pizarra compartida (máx. ~30 líneas)

Claude y Codex: leed esto al empezar y actualizadlo al acabar. Borrad lo viejo; esto no es un historial.

## Ahora mismo
- App v2 en Streamlit Cloud con Supabase: login, socios, cobros (pendiente del mes, atrasados, "Recordar a todos"), clases, reservas del socio, pruebas y edicion de tablas.
- Fase A terminada (A1, A2, A3; ver HECHO.md). Siguiente: FASE B (B1, generador de Excels sinteticos).
- A3: Ajustes > "Datos y baja" > "Dejar la demo como nueva" (`demo.py`). Solo lo ven los emails de `st.secrets["DEMO_EMAILS"]` (lista). Diego debe anadirla en local y en Streamlit Cloud. Aun no probado contra Supabase.

## Siguiente tarea
- (Diego la escribe aquí)

## Decisiones tomadas
- Ante opciones, siempre la mas segura (p. ej. demo solo por lista explicita de emails).
- Solo negocios con cuota recurrente (no peluquerías ni pago suelto).
- Stack 100% gratis. Solo datos inventados.
- IA: modelo propio pequeno (RandomForest) para leer Excels de horarios + Gemini solo de respaldo (FASE B).

## Pendiente de que Diego decida
- (vacío)
