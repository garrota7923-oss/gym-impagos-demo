# ESTADO.md — pizarra compartida (máx. ~30 líneas)

Claude y Codex: leed esto al empezar y actualizadlo al acabar. Borrad lo viejo; esto no es un historial.

## Ahora mismo
- App v2 en Streamlit Cloud con Supabase: login, socios, cobros (pendiente del mes, atrasados, "Recordar a todos"), clases, reservas del socio, pruebas y edicion de tablas.
- Fase A terminada (A1-A5, ver HECHO.md). FASE B: B1 hecho. Siguiente: B2 (notebook + RandomForest).
- B1: `python datos/generar_excels.py` (~10 s) crea 300 Excels en `datos/generados/` + `etiquetas.csv` (dia/hora/nombre/prueba/otro por celda) + `reservas.csv` (verdad para medir B3). Semilla 42, 30 "estilos de club".
- Diego dio OK a instalar scikit-learn, joblib y jupyter (para B2).
- A5: en cuentas `DEMO_EMAILS`, Ajustes oculta "Cambiar contrasena" y "Dar de baja". Sin `DEMO_EMAILS` en secrets no protege nada.
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
