"""Vista del socio: reservar y cancelar clases desde su enlace personal."""
from datetime import date, datetime, timedelta
import streamlit as st
from db import motor, q, run

DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
DIAS_ANTELACION = 7
HORAS_CANCELAR = 2


def reservar(cliente, actividad_id, fecha):
    """Reserva con control de aforo. Devuelve (ok, mensaje)."""
    with motor().begin() as c:
        # FOR UPDATE bloquea la clase: si dos reservan a la vez, el segundo espera al primero
        aforo = c.exec_driver_sql("SELECT aforo FROM actividad WHERE id=%s FOR UPDATE",
                                  (actividad_id,)).scalar()
        ocupadas = c.exec_driver_sql("""SELECT COUNT(*) FROM reserva WHERE actividad_id=%s AND fecha=%s
                                        AND estado IN ('reservada','asistida')""", (actividad_id, fecha)).scalar()
        if ocupadas >= aforo:
            return False, "La clase esta completa"
        c.exec_driver_sql("""INSERT INTO reserva (negocio_id, cliente_id, actividad_id, fecha, estado, creada_en)
                             VALUES (%s,%s,%s,%s,'reservada',%s)
                             ON CONFLICT (cliente_id, actividad_id, fecha)
                             DO UPDATE SET estado='reservada', creada_en=EXCLUDED.creada_en""",
                          (int(cliente["negocio_id"]), int(cliente["id"]), actividad_id, fecha,
                           datetime.now().isoformat()))
    return True, "Plaza reservada"


def cancelar(cliente_id, actividad_id, fecha):
    run("""UPDATE reserva SET estado='cancelada' WHERE cliente_id=%s AND actividad_id=%s AND fecha=%s
           AND estado='reservada'""", (cliente_id, actividad_id, fecha))


def vista_socio(token):
    cli = q("""SELECT c.*, n.nombre AS negocio, m.estado AS membresia
               FROM cliente c JOIN negocio n ON n.id=c.negocio_id
               LEFT JOIN membresia m ON m.cliente_id=c.id
                    AND m.id=(SELECT MAX(id) FROM membresia WHERE cliente_id=c.id)
               WHERE c.token=%s""", (token,))
    if cli.empty:
        st.error("Este enlace no es valido. Pide uno nuevo en recepcion.")
        return
    cli = cli.iloc[0]
    st.title(cli["negocio"])
    st.write(f"Hola, **{cli['nombre']}**")
    if cli["membresia"] != "activa":
        st.warning("Tu membresia no esta activa, asi que no puedes reservar. Habla con recepcion.")
        return

    nid, cid = int(cli["negocio_id"]), int(cli["id"])
    acts = q("SELECT * FROM actividad WHERE negocio_id=%s ORDER BY hora", (nid,)).to_dict("records")
    mias = {(int(r["actividad_id"]), r["fecha"]) for r in q(
        "SELECT actividad_id, fecha FROM reserva WHERE cliente_id=%s AND estado='reservada'", (cid,)
    ).to_dict("records")}
    ocup = {(int(r["actividad_id"]), r["fecha"]): int(r["n"]) for r in q(
        """SELECT actividad_id, fecha, COUNT(*) AS n FROM reserva WHERE negocio_id=%s
           AND estado IN ('reservada','asistida') GROUP BY actividad_id, fecha""", (nid,)
    ).to_dict("records")}

    ahora = datetime.now()
    nombres = {a["id"]: a for a in acts}
    futuras = sorted([(a, f) for (a, f) in mias if f >= date.today().isoformat()], key=lambda x: x[1])
    if futuras:
        st.subheader("Tus reservas")
        for aid, f in futuras:
            a = nombres[aid]
            col1, col2 = st.columns([3, 1])
            d = date.fromisoformat(f)
            col1.write(f"{DIAS[d.weekday()]} {d.day}/{d.month} · {a['hora']} · {a['nombre']}")
            inicio = datetime.fromisoformat(f"{f}T{a['hora']}")
            if inicio - ahora > timedelta(hours=HORAS_CANCELAR):
                if col2.button("Cancelar", key=f"can{aid}{f}"):
                    cancelar(cid, aid, f)
                    st.rerun()
            else:
                col2.caption("Ya no se puede cancelar")

    st.subheader("Reservar clase")
    dias_disp = [date.today() + timedelta(days=k) for k in range(DIAS_ANTELACION)]
    dia = st.radio("Dia", dias_disp, horizontal=True,
                   format_func=lambda d: f"{DIAS[d.weekday()][:3]} {d.day}")
    del_dia = [a for a in acts if dia.weekday() in [int(x) for x in a["dias"].split(",")]]
    if not del_dia:
        st.info("Ese dia no hay clases")
    for a in del_dia:
        f = dia.isoformat()
        inicio = datetime.fromisoformat(f"{f}T{a['hora']}")
        libres = a["aforo"] - ocup.get((a["id"], f), 0)
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{a['hora']}** · {a['nombre']} · {max(libres, 0)} plazas libres")
        if (a["id"], f) in mias:
            col2.success("Reservada")
        elif inicio < ahora:
            col2.caption("Ya empezo")
        elif libres <= 0:
            col2.caption("Completa")
        elif col2.button("Reservar", key=f"res{a['id']}{f}"):
            ok, msg = reservar(cli, a["id"], f)
            (st.success if ok else st.error)(msg)
            st.rerun()
