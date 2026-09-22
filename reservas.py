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
    st.markdown("<style>.block-container{max-width:640px}</style>", unsafe_allow_html=True)
    cli = q("""SELECT c.*, n.nombre AS negocio, n.activo AS negocio_activo, m.estado AS membresia,
                      p.tipo AS plan_tipo, p.sesiones, m.sesiones_usadas
               FROM cliente c JOIN negocio n ON n.id=c.negocio_id
               LEFT JOIN membresia m ON m.cliente_id=c.id
                    AND m.id=(SELECT MAX(id) FROM membresia WHERE cliente_id=c.id)
               LEFT JOIN plan p ON p.id=m.plan_id
               WHERE c.token=%s""", (token,))
    if cli.empty or not bool(cli.iloc[0]["negocio_activo"]):
        st.error("Este enlace no funciona. Pide uno nuevo en recepcion.")
        return
    cli = cli.iloc[0]
    st.image("static/icono.svg", width=48)
    st.title(cli["negocio"])
    st.write(f"Hola, **{cli['nombre']}**")
    if cli["membresia"] != "activa":
        st.warning("Tu cuota no esta activa ahora mismo, asi que no puedes reservar. Habla con recepcion.")
        return
    quedan = None
    if cli["plan_tipo"] == "bono":
        quedan = int(cli["sesiones"] - cli["sesiones_usadas"])
        st.info(f"Te quedan {quedan} clases de tu bono.")

    nid, cid = int(cli["negocio_id"]), int(cli["id"])
    acts = q("SELECT * FROM actividad WHERE negocio_id=%s AND activo ORDER BY hora", (nid,)).to_dict("records")
    mias = {(int(r["actividad_id"]), r["fecha"]) for r in q(
        "SELECT actividad_id, fecha FROM reserva WHERE cliente_id=%s AND estado='reservada'", (cid,)
    ).to_dict("records")}
    ocup = {(int(r["actividad_id"]), r["fecha"]): int(r["n"]) for r in q(
        """SELECT actividad_id, fecha, COUNT(*) AS n FROM reserva WHERE negocio_id=%s
           AND estado IN ('reservada','asistida') GROUP BY actividad_id, fecha""", (nid,)
    ).to_dict("records")}

    ahora = datetime.now()
    nombres = {a["id"]: a for a in acts}
    futuras = sorted([(a, f) for (a, f) in mias if f >= date.today().isoformat() and a in nombres],
                     key=lambda x: (x[1], nombres[x[0]]["hora"]))
    if futuras:
        st.subheader("Tus reservas")
        for aid, f in futuras:
            a = nombres[aid]
            with st.container(border=True):
                col1, col2 = st.columns([3, 2])
                d = date.fromisoformat(f)
                col1.markdown(f"**{DIAS[d.weekday()]} {d.day}/{d.month} a las {a['hora']}**  \n{a['nombre']}")
                inicio = datetime.fromisoformat(f"{f}T{a['hora']}")
                if inicio - ahora > timedelta(hours=HORAS_CANCELAR):
                    if col2.button("Cancelar", key=f"can{aid}{f}", width="stretch"):
                        cancelar(cid, aid, f)
                        st.rerun()
                else:
                    col2.caption("Ya no se puede cancelar")

    st.subheader("Reservar")
    dias_disp = [date.today() + timedelta(days=k) for k in range(DIAS_ANTELACION)]
    dia = st.segmented_control("Dia", dias_disp, default=dias_disp[0], label_visibility="collapsed",
                               format_func=lambda d: f"{DIAS[d.weekday()][:3]} {d.day}")
    dia = dia or dias_disp[0]
    del_dia = [a for a in acts if str(dia.weekday()) in a["dias"].split(",")]
    if not del_dia:
        st.info("Ese dia no hay clases")
    for a in del_dia:
        f = dia.isoformat()
        inicio = datetime.fromisoformat(f"{f}T{a['hora']}")
        libres = a["aforo"] - ocup.get((a["id"], f), 0)
        with st.container(border=True):
            col1, col2 = st.columns([3, 2])
            col1.markdown(f"**{a['hora']}**  {a['nombre']}  \n:gray[{max(libres, 0)} plazas libres]")
            if (a["id"], f) in mias:
                col2.success("Reservada")
            elif inicio < ahora:
                col2.caption("Ya ha empezado")
            elif libres <= 0:
                col2.caption("Completa")
            elif quedan is not None and quedan <= 0:
                col2.caption("Bono agotado")
            elif col2.button("Reservar", key=f"res{a['id']}{f}", type="primary", width="stretch"):
                ok, msg = reservar(cli, a["id"], f)
                (st.success if ok else st.error)(msg)
                st.rerun()
    st.caption(f"Tus datos los gestiona {cli['negocio']} solo para tus reservas y tu cuota. "
               "Para consultarlos, cambiarlos o borrarlos, pidelo en recepcion.")
