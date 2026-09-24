# ESTADO.md — pizarra compartida (máx. ~30 líneas)

Claude y Codex: leed esto al empezar y actualizadlo al acabar. Borrad lo viejo; esto no es un historial.

## Ahora mismo
- App v2 en Streamlit Cloud con Supabase: login, socios, cobros (pendiente del mes, atrasados, "Recordar a todos"), clases, reservas del socio, pruebas y edicion de tablas.
- Fase A: A1-A4 hechas (ver HECHO.md). Siguiente: A5 (proteger la demo), luego FASE B (B1).
- A3: Ajustes > "Datos y baja" > "Dejar la demo como nueva" (`demo.py`). Tres candados: email en `DEMO_EMAILS` (secrets), `negocio_id` en `DEMO_NEGOCIOS={1}` (fijado en codigo) y el usuario pertenece a ese negocio. A4: todo por lotes, ~27 viajes a la BD (antes ~200); muestra el tiempo al acabar. Probado en Postgres local: mismos datos y negocio 2 identico. Falta medir en Streamlit Cloud (<5 s). Falta `DEMO_EMAILS` en Streamlit Cloud.

## Siguiente tarea
- (Diego la escribe aquí)

## Decisiones tomadas
- Ante opciones, siempre la mas segura (p. ej. demo solo por lista explicita de emails).
- Solo negocios con cuota recurrente (no peluquerías ni pago suelto).
- Stack 100% gratis. Solo datos inventados.
- IA: modelo propio pequeno (RandomForest) para leer Excels de horarios + Gemini solo de respaldo (FASE B).

## Pendiente de que Diego decida
- (vacío)
