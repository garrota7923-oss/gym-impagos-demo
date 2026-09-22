"""Editar los datos del negocio en tablas, como en un Excel, con protecciones."""
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from db import q, run
from comun import cargar, estilo, evento, tel_ok, tel_norm, nombre_mes


def _cambios(original, editado, columnas):
    """Devuelve (filas modificadas, ids borrados) comparando dos tablas con columna id."""
    orig = original.set_index("id")
    ed = editado.dropna(subset=["id"]).copy()
    ed["id"] = ed["id"].astype(int)
    ed = ed.set_index("id")
    borrados = [int(i) for i in orig.index if i not in ed.index]
    modificados = []
    for i, fila in ed.iterrows():
        if i not in orig.index:
            continue
        antes, ahora = orig.loc[i, columnas], fila[columnas]
        distinto = any(not (pd.isna(a) and pd.isna(b)) and str(a) != str(b) for a, b in zip(antes, ahora))
        if distinto:
            modificados.append((int(i), fila))
    nuevas = len(editado) - len(editado.dropna(subset=["id"]))
    return modificados, borrados, nuevas


def _limpio(v):
    return None if pd.isna(v) or str(v).strip() == "" else str(v).strip()


def editar():
    estilo()
    if "usuario" not in st.session_state:
        st.stop()
    c = cargar(int(st.session_state["usuario"]["negocio_id"]))
    nid = c["nid"]
    st.title("Editar datos")
    st.caption("Cambia lo que quieras directamente en las tablas y pulsa Guardar. "
               "Para borrar una fila, seleccionala con la casilla de la izquierda y pulsa la papelera.")
    t1, t2, t3 = st.tabs([c["CLIS"].capitalize(), "Cobros", "Asistencias"])

    # ---------------------------------------------------------------- Socios
    with t1:
        s = c["socios"][["id", "nombre", "apellidos", "telefono", "email", "dni", "notas"]].sort_values("id")
        s = s[s["nombre"] != "Datos borrados"].reset_index(drop=True)
        ed = st.data_editor(s, num_rows="dynamic", hide_index=True, width="stretch", key="ed_socios",
                            column_config={"id": st.column_config.NumberColumn("Nº", disabled=True),
                                           "nombre": "Nombre", "apellidos": "Apellidos", "telefono": "Telefono",
                                           "email": "Email", "dni": "DNI", "notas": "Notas"})
        mod, borr, nuevas = _cambios(s, ed, ["nombre", "apellidos", "telefono", "email", "dni", "notas"])
        if nuevas:
            st.info("Las personas nuevas se dan de alta en Apuntar, para asignarles su plan. "
                    "Las filas nuevas de esta tabla no se guardaran.")
        if borr:
            nombres = ", ".join(s.set_index("id").loc[borr, "nombre"].astype(str))
            st.warning(f"Vas a borrar los datos personales de: {nombres}. Se dan de baja y su nombre, "
                       "telefono, email y DNI se eliminan para siempre. Sus cobros se conservan para que "
                       "las cuentas cuadren.")
        confirmar = st.checkbox("Entiendo que lo borrado no se puede recuperar", key="conf_socios") if borr else True
        if st.button(f"Guardar cambios ({len(mod)} cambios, {len(borr)} borrados)", type="primary",
                     disabled=not (mod or borr), key="g_socios"):
            errores = []
            otros = c["clientes"].set_index("id")["telefono"]
            for i, f in mod:
                tel = tel_norm(f["telefono"])
                if not _limpio(f["nombre"]):
                    errores.append(f"nº {i}: falta el nombre")
                elif not tel_ok(f["telefono"]):
                    errores.append(f"nº {i}: telefono no valido")
                elif tel in otros.drop(i).values:
                    errores.append(f"nº {i}: ese telefono ya lo tiene otra persona")
            if borr and not confirmar:
                errores.append("marca la casilla de confirmacion para borrar")
            if errores:
                st.error("No se ha guardado nada. Revisa: " + "; ".join(errores))
            else:
                for i, f in mod:
                    run("""UPDATE cliente SET nombre=%s, apellidos=%s, telefono=%s, email=%s, dni=%s, notas=%s
                           WHERE id=%s AND negocio_id=%s""",
                        (_limpio(f["nombre"]), _limpio(f["apellidos"]), tel_norm(f["telefono"]),
                         _limpio(f["email"]), (_limpio(f["dni"]) or "").upper() or None, _limpio(f["notas"]), i, nid))
                    evento(nid, i, "edicion", "Datos editados en la tabla")
                for i in borr:
                    run("""UPDATE cliente SET nombre='Datos borrados', apellidos=NULL, telefono=%s, email=NULL,
                           dni=NULL, notas=NULL, token=NULL, estado='inactivo', extra='{}'
                           WHERE id=%s AND negocio_id=%s""", (f"borrado-{i}", i, nid))
                    run("UPDATE membresia SET estado='baja', fecha_fin=COALESCE(fecha_fin,%s) WHERE cliente_id=%s",
                        (date.today().isoformat(), i))
                    run("DELETE FROM reserva WHERE cliente_id=%s AND estado='reservada'", (i,))
                    evento(nid, i, "supresion", "Datos personales borrados a peticion")
                st.success("Cambios guardados")
                st.rerun()

    # ---------------------------------------------------------------- Cobros
    with t2:
        meses = q("SELECT DISTINCT LEFT(periodo,7) AS m FROM cobro WHERE negocio_id=%s ORDER BY 1 DESC", (nid,))["m"].tolist()
        if not meses:
            st.info("Todavia no hay cobros.")
        else:
            m = st.selectbox("Mes", meses, format_func=nombre_mes, key="mes_cobros")
            co = q("""SELECT co.id, c.nombre || ' ' || COALESCE(c.apellidos,'') AS persona, co.periodo,
                             co.importe, co.estado, co.fecha, co.metodo
                      FROM cobro co JOIN membresia mb ON mb.id=co.membresia_id JOIN cliente c ON c.id=mb.cliente_id
                      WHERE co.negocio_id=%s AND LEFT(co.periodo,7)=%s ORDER BY persona""", (nid, m))
            ec = st.data_editor(co, num_rows="dynamic", hide_index=True, width="stretch", key=f"ed_cobros{m}",
                                column_config={
                                    "id": None, "persona": st.column_config.TextColumn("Persona", disabled=True),
                                    "periodo": st.column_config.TextColumn("Periodo", disabled=True),
                                    "importe": st.column_config.NumberColumn("Importe (€)", min_value=0, format="%.2f"),
                                    "estado": st.column_config.SelectboxColumn(
                                        "Estado", options=["pendiente", "pagado", "devuelto"], required=True),
                                    "fecha": st.column_config.TextColumn("Pagado el", help="AAAA-MM-DD"),
                                    "metodo": st.column_config.SelectboxColumn(
                                        "Metodo", options=["Bizum", "Efectivo", "Tarjeta", "Domiciliacion", "Transferencia"])})
            mod, borr, nuevas = _cambios(co, ec, ["importe", "estado", "fecha", "metodo"])
            if nuevas:
                st.info("Las cuotas nuevas se crean desde Cobros. Las filas nuevas de esta tabla no se guardaran.")
            if borr:
                st.warning(f"Vas a borrar {len(borr)} cobros. Hazlo solo si se crearon por error.")
            confirmar = st.checkbox("Confirmo que quiero borrar esos cobros", key="conf_cobros") if borr else True
            if st.button(f"Guardar cobros ({len(mod)} cambios, {len(borr)} borrados)", type="primary",
                         disabled=not (mod or borr), key="g_cobros"):
                errores = [f"{f['persona']}: la fecha debe ser AAAA-MM-DD"
                           for i, f in mod if _limpio(f["fecha"]) and pd.to_datetime(f["fecha"], errors="coerce") is pd.NaT]
                if borr and not confirmar:
                    errores.append("marca la casilla de confirmacion para borrar")
                if errores:
                    st.error("No se ha guardado nada. Revisa: " + "; ".join(errores))
                else:
                    for i, f in mod:
                        pagado = f["estado"] == "pagado"
                        fecha = _limpio(f["fecha"]) or (date.today().isoformat() if pagado else None)
                        run("UPDATE cobro SET importe=%s, estado=%s, fecha=%s, metodo=%s WHERE id=%s AND negocio_id=%s",
                            (float(f["importe"]), f["estado"], fecha if pagado else None,
                             _limpio(f["metodo"]) if pagado else None, i, nid))
                    for i in borr:
                        run("DELETE FROM cobro WHERE id=%s AND negocio_id=%s", (i, nid))
                    st.success("Cobros guardados")
                    st.rerun()

    # ---------------------------------------------------------------- Asistencias
    with t3:
        a, b = st.columns(2)
        desde = a.date_input("Desde", date.today() - timedelta(days=14), format="DD/MM/YYYY", key="as_desde")
        hasta = b.date_input("Hasta", date.today(), format="DD/MM/YYYY", key="as_hasta")
        asi = q("""SELECT a.id, a.fecha, ac.hora, ac.nombre AS clase,
                          c.nombre || ' ' || COALESCE(c.apellidos,'') AS persona
                   FROM asistencia a JOIN actividad ac ON ac.id=a.actividad_id JOIN cliente c ON c.id=a.cliente_id
                   WHERE a.negocio_id=%s AND a.fecha BETWEEN %s AND %s ORDER BY a.fecha DESC, ac.hora""",
                (nid, desde.isoformat(), hasta.isoformat()))
        st.caption("Aqui solo se pueden borrar asistencias apuntadas por error. Para apuntarlas, usa Clases.")
        ea = st.data_editor(asi, num_rows="dynamic", hide_index=True, width="stretch", key="ed_asis",
                            disabled=["fecha", "hora", "clase", "persona"],
                            column_config={"id": None, "fecha": "Fecha", "hora": "Hora", "clase": "Clase",
                                           "persona": "Persona"})
        _, borr, _ = _cambios(asi, ea, ["fecha"])
        if st.button(f"Borrar {len(borr)} asistencias", disabled=not borr, key="g_asis"):
            for i in borr:
                run("DELETE FROM asistencia WHERE id=%s AND negocio_id=%s", (i, nid))
            st.success("Asistencias borradas")
            st.rerun()
