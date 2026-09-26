# ESTADO.md — pizarra compartida (máx. ~30 líneas)

Claude y Codex: leed esto al empezar y actualizadlo al acabar. Borrad lo viejo; esto no es un historial.

## Ahora mismo
- App v2 en Streamlit Cloud con Supabase: login, socios, cobros (pendiente del mes, atrasados, "Recordar a todos"), clases, reservas del socio, pruebas y edicion de tablas.
- Fase A terminada (A1-A5, ver HECHO.md). FASE B: B1, B2 y B2b hechos. Siguiente: B3 (lector robusto). Plan nuevo B3-B8 en `examen/PLAN_IMPORTADOR.md`; `examen/` (100 archivos) solo para medir.
- B1: `python datos/generar_excels.py` (~10 s) crea 300 Excels en `datos/generados/` + `etiquetas.csv` (dia/hora/nombre/prueba/otro por celda) + `reservas.csv` (verdad para medir B3). Semilla 42, 30 "estilos de club".
- B2: `rasgos_celdas.py` (rasgos por celda, lo usan notebook y lector: si cambia, reentrenar) + `notebooks/modelo_celdas.ipynb` -> `modelos/modelo_celdas.joblib` (0,7 MB, 99,99% en examen 250/50).
- B2b: generador con 3 formatos (bloques, semana = dias en columnas y varios nombres por celda, lista = una fila por reserva) + `familias.csv`. Dejando fuera cada familia: 99,74% (peor 96,56%). Notebook ~3 min.
- B2b-2: `datos/a_mano/` = examen con 3 Excels inventados a mano (nunca para entrenar) + `etiquetas.csv` (por celda) + `esperado.csv` (reservas, verdad para B3). 100% por celda (antes 52%).
- Para B5: en "semana" una celda trae varios nombres (separar por / , ; -) y la marca de prueba va en el nombre concreto; en "lista" la marca de prueba puede ir en la columna de observaciones.
- B3/B4: anadir `scikit-learn==1.9.1` y `joblib` a requirements.txt (el modelo solo carga con esa version). OK de Diego ya dado.
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
