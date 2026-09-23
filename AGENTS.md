# AGENTS.md — gym-impagos-demo

Instrucciones compartidas para Claude y Codex. Léelas enteras antes de tocar nada. Son cortas a propósito: cada línea se carga en cada turno.

## Qué es
Panel web (SaaS) para negocios con **cuota recurrente** (gimnasios, clubes de boxeo, academias): socios, cobros/impagos, clases, reservas, clases de prueba. Multi-negocio: cada negocio solo ve sus datos. Dueño: Diego (no programador senior; explica simple).

## Stack (todo gratis)
Python 3.11 · Streamlit · pandas · SQLAlchemy + psycopg2 · Supabase (PostgreSQL) · Streamlit Community Cloud. Diego trabaja en Windows con Git Bash.

## Mapa de archivos
- `gestion.py` — entrada de la app: login, menú y vista del socio (`?t=token`).
- `paginas.py` — pantallas del panel (Hoy, Socios, Apuntar, Clases, Cobros, Pruebas, Ajustes). El más grande: lee solo la función que necesites.
- `editar.py` — edición de tablas. `reservas.py` — reservas del socio (aforo, cancelación).
- `comun.py` — utilidades (formatos, teléfonos, WhatsApp, `cargar(nid)`, estados de socio).
- `db.py` — conexión (`q()` lee, `run()` escribe) y hash de contraseñas.
- Scripts sueltos (no los ejecutes sin permiso): `crear_bd.py`, `generar_datos.py`, `migrar_a_supabase.py`, `actualizar_bd.py`, `migrar_reservas.py`, `crear_usuario.py`, `configurar_secreto.py`, `importador_excel.py` (prototipo antiguo).
- Tablas: negocio, usuario, cliente, plan, membresia, cobro, actividad, asistencia, reserva, evento.

## Reglas de código
- SQL siempre parametrizado (`%s`), nunca f-strings con datos.
- **Toda consulta filtra por `negocio_id`** del usuario en sesión. Saltarse esto = fuga de datos entre clientes.
- Textos de la interfaz en español y sin tildes (como el código existente).
- Cambios pequeños, mínimos y en el estilo actual. No reescribas archivos enteros ni añadas dependencias.
- Comprueba con `python -m py_compile <archivo>` lo que toques. Arrancar: `streamlit run gestion.py`.

## Ahorro de tokens (obligatorio)
- No leas `negocios.db`, `.streamlit/secrets.toml`, `static/`, `__pycache__/` ni archivos enteros si basta con `grep`/buscar la función.
- Antes de empezar, lee `ESTADO.md` (y solo eso) para saber en qué punto estamos.
- Respuestas cortas: qué cambiaste, en qué archivos y cómo probarlo. Sin repetir código que no cambió.
- Una tarea = una conversación. Al acabar, actualiza `ESTADO.md` en 2–4 líneas y termina.

## PARA y pregunta a Diego antes de...
1. Cambiar el esquema de la base de datos o ejecutar cualquier script contra Supabase.
2. Borrar archivos, datos o funcionalidades.
3. Añadir dependencias, servicios externos o algo que pueda costar dinero.
4. Tocar login, contraseñas, permisos o `negocio_id` (seguridad).
5. Hacer `git push`, commits en `main` o desplegar.
6. Cualquier decisión de producto (qué ve el cliente, precios, textos de venta).
7. Si la tarea es ambigua o vas a tardar más de lo previsto.
Pregunta **una sola vez, en corto y con opciones** (A/B), y espera respuesta.

## Nunca
- Subir o mostrar secretos (`DATABASE_URL`, contraseñas, claves API).
- Usar datos personales reales: solo datos inventados. Los Excel reales de clubes (`HORARIOS*`, `*FABRIKA*`) están en `.gitignore` y no se leen.

## Reparto de trabajo
- **Claude**: planifica, programa y habla con Diego.
- **Codex**: revisa los cambios de Claude (`/codex:review`) y resuelve atascos concretos (`/codex:rescue`). No reescribe lo que funciona.
- Nunca los dos a la vez sobre la misma tarea.
