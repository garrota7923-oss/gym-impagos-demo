# ESTADO.md — pizarra compartida (máx. ~30 líneas)

Claude y Codex: leed esto al empezar y actualizadlo al acabar. Borrad lo viejo; esto no es un historial.

## Ahora mismo
- App v2 en Streamlit Cloud con Supabase: login, socios, cobros, clases, reservas del socio, pruebas y edición de tablas.
- Cobros: dos recuadros arriba, "Pendiente de <mes>" (incluye cuotas sin generar) y "Atrasado" (pendientes de meses anteriores).
- A1 hecha, revisada por Codex y en main (PR #2). Falta que Diego la pruebe en la app.
- A2 hecha en rama `recordar-atrasados` (paginas.py `cobros()`): recuadro "Recordar a todos" con WhatsApp por socio atrasado y un `evento` 'recordatorio' por socio. PR #4 abierto, revisado por Codex (sin P0/P1). Maximo un recordatorio por socio y dia.
- Pendiente A2 (P2 de Codex): el evento se registra al pulsar el boton, no al abrir cada WhatsApp (incluye socios sin telefono valido).

## Siguiente tarea
- (Diego la escribe aquí)

## Decisiones tomadas
- Solo negocios con cuota recurrente (no peluquerías ni pago suelto).
- Stack 100% gratis. Solo datos inventados.
- IA: nada de entrenar modelos propios por ahora; primero API barata con JSON + reglas.

## Pendiente de que Diego decida
- (vacío)
