# PROPUESTAS.md — Ideas que no estan en TAREAS.md

Propuestas de Claude (23-09-2026) tras hacer A1. No son tareas: Diego decide cuales pasan a TAREAS.md.
Tamano: S = menos de 30 lineas · M = una tarde · L = varias sesiones.
Condiciones para todas: **gratis** (sin servicios de pago ni dependencias nuevas) y **legal** (RGPD, solo datos inventados en la demo).
Esto es orientacion, no asesoria legal: antes del primer cliente real, que lo revise un gestor o abogado.

## Cobros (sigue a A1/A2)
- **P1. Antiguedad de la deuda (S).** En "Atrasado", separar "1 mes" de "2 meses o mas", o marcar en la lista a quien debe 2+ cuotas. El gerente ve a quien llamar primero.
  Gratis: si. Legal: si, son datos que el club ya trata para cobrar.
- **P2. Deshacer "pagado" (S).** Si se marca un cobro como pagado por error, poder volverlo a pendiente desde la ficha del socio. Hay que comprobar antes si ya se puede con Editar.
  Gratis: si. Legal: si. Guardar un `evento` para que quede constancia del cambio.
- **P3. Justificante de pago (M).** Un texto para enviar por WhatsApp al cobrar ("Recibido 40 EUR, cuota de septiembre").
  Gratis: si (enlace wa.me, como ahora). Legal: **no puede llamarse "factura"** ni parecerlo; en Espana las facturas tienen requisitos propios (y Verifactu). Poner "Justificante, no es factura".

- **P10. Recordatorio registrado al abrir WhatsApp (S, P2 de Codex en A2).** Ahora el `evento` se apunta al pulsar "Recordar a todos", tambien para socios sin telefono valido. Opcion A: no apuntarlo sin telefono valido. Opcion B: boton "Enviado" por socio.

## Seguridad (tocar solo con OK de Diego)
- **P4. Revision automatica de `negocio_id` (S).** Un script que avise si alguna consulta de `q()`/`run()` no lleva `negocio_id`. Cubre el punto del checklist "Antes del primer cliente real".
  Gratis: si (solo Python). Legal: ayuda al RGPD (que un club no vea datos de otro).
- **P5. Limitar intentos de login (S/M).** No he visto limite en `gestion.py`: se pueden probar contrasenas sin parar.
  Gratis: si. Si hace falta guardar los intentos en la BD, es un cambio de esquema: preguntar antes. No guardar IPs (son dato personal).
- **P6. Recuperar contrasena del gerente (M).** Ahora no hay forma si la olvida.
  Opcion gratis y sin servicios nuevos: que Diego la resetee con `crear_usuario.py`. El envio de emails solo si hay un plan gratuito claro; si no, se descarta.

## Calidad y demo
- **P7. Pruebas minimas (M).** No hay tests. Unos pocos para `comun.py` (`tel_ok`, `euros`, `nombre_mes`, `cuotas_debidas`) atraparian fallos antes de Codex.
  Gratis: si, con `unittest` (viene con Python, sin dependencias nuevas).
- **P8. Guion de demo de 5 minutos (S).** Un README corto con los clics exactos que ensenar: Hoy → Cobros (atrasados) → WhatsApp → vista del socio. Encaja con A3.
  Gratis: si. Legal: en la demo, solo datos inventados.
- **P9. Limpiar scripts viejos (S).** `importador_excel.py` es un prototipo antiguo y B2 lo sustituye. Borrarlo o moverlo solo con OK de Diego.
  Gratis y legal: si.
- Demo: el visitante puede renombrar el negocio en Ajustes > Mi negocio y el reset no devuelve el nombre original.
- **Examen por opcion no vista (S).** Dejar fuera todos los Excels con un valor de formato (p. ej. horas "rango" o dias "corto"): eso si es un formato nuevo, a diferencia de dejar fuera una familia (99,99%, porque combina opciones ya vistas).
- **Dias con fecha como tipo DIA (S).** `rasgos_celdas.tipo` trata "Lunes 5 oct", "01/10/2026" y las celdas de fecha (datetime) como texto u hora; el modelo acierta por contexto, pero al dejar fuera la familia 9 (semana + "Lunes 5 oct") baja a 96,56%. Ampliar RE_DIA y reentrenar.
- **Excel .xls antiguo (S).** Hoy se pide guardarlo como .xlsx; leerlo directamente necesita `xlrd` (dependencia nueva, OK de Diego).
- **Cabeceras con fechas (S).** Una cabecera cuyas celdas son fechas de Excel (p. ej. meses como 01/09/2026) no se reconoce como cabecera. Anadir ese tipo al lector y un test.

## Descartado por coste o legalidad
- API oficial de WhatsApp para envios automaticos: cuesta dinero por mensaje y exige consentimiento. Se sigue con enlaces wa.me que pulsa el gerente.
- SMS o email masivos: servicios de pago y requisitos de consentimiento (LSSI).
