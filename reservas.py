"""Vista del socio: reservar y cancelar clases desde su enlace personal."""
import sqlite3
from datetime import date, datetime, timedelta
import streamlit as st

BD = "negocios.db"
DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
DIAS_ANTELACION = 7
HORAS_CANCELAR = 2


def reservar(cliente, actividad_id, fecha):
    """Reserva con control de aforo. Devuelve (ok, mensaje)."""
    c = sqlite3.connect(BD, timeout=10)
    try:
        c.execute("BEGIN IMMEDIATE")
        aforo = c.execute("SELECT aforo FROM actividad WHERE id=?", (actividad_id,)).fetchone()[0]
        ocupadas = c.execute("""SELECT COUNT(*) FROM reserva WHERE actividad_id=? AND fecha=?
                                AND estado IN ('reservada','asistida')""", (actividad_id, fecha)).fetchone()[0]
        if ocupadas >= aforo:
            c.rollback()
            return False, "La clase esta completa"
        c.execute("""INSERT INTO reserva (negocio_id, cliente_id, actividad_id, fecha, estado, creada_en)
                     VALUES (?,?,?,?,'reservada',?)
                     ON CONFLICT (cliente_id, actividad_id, fecha)
                     DO UPDATE SET estado='reservada', creada_en=excluded.creada_en""",
                  (cliente["negocio_id"], cliente["id"], actividad_id, fecha, datetime.now().isoformat()))
        c.commit()
        return True, "Plaza reservada"
    finally:
        c.close()


def cancelar(cliente_id, actividad_id, fecha):
    c = sqlite3.connect(BD, timeout=10)
    c.execute("""UPDATE reserva SET estado='cancelada' WHERE cliente_id=? AND actividad_id=? AND fecha=?
                 AND estado='reservada'""", (cliente_id, actividad_id, fecha))
    c.commit()
    c.close()


def vista_socio(token):
    c = sqlite3.connect(BD)
    c.row_factory = sqlite3.Row
    cli = c.execute("""SELECT c.*, n.nombre AS negocio, m.estado AS membresia
                       FROM cliente c JOIN negocio n ON n.id=c.negocio_id
                       LEFT JOIN membresia m ON m.cliente_id=c.id
                            AND m.id=(SELECT MAX(id) FROM membresia WHERE cliente_id=c.id)
                       WHERE c.token=?""", (token,)).fetchone()
    if cli is None:
        st.error("Este enlace no es valido. Pide uno nuevo en recepcion.")
        return
    st.title(cli["negocio"])
    st.write(f"Hola, **{cli['nombre']}**")
    if cli["membresia"] != "activa":
        st.warning("Tu membresia no esta activa, asi que no puedes reservar. Habla con recepcion.")
        return

    acts = c.execute("SELECT * FROM actividad WHERE negocio_id=? ORDER BY hora", (cli["negocio_id"],)).fetchall()
    mias = {(r["actividad_id"], r["fecha"]) for r in c.execute(
        "SELECT actividad_id, fecha FROM reserva WHERE cliente_id=? AND estado='reservada'", (cli["id"],))}
    ocup = {(r[0], r[1]): r[2] for r in c.execute(
        """SELECT actividad_id, fecha, COUNT(*) FROM reserva WHERE negocio_id=?
           AND estado IN ('reservada','asistida') GROUP BY actividad_id, fecha""", (cli["negocio_id"],))}
    c.close()

    ahora = datetime.now()
    proximas = [(a, f) for (a, f) in sorted(mias, key=lambda x: x[1])]
    if proximas:
        st.subheader("Tus reservas")
        nombres = {a["id"]: a for a in acts}
        for aid, f in proximas:
            if f < date.today().isoformat():
                continue
            a = nombres[aid]
            col1, col2 = st.columns([3, 1])
            d = date.fromisoformat(f)
            col1.write(f"{DIAS[d.weekday()]} {d.day}/{d.month} · {a['hora']} · {a['nombre']}")
            inicio = datetime.fromisoformat(f"{f}T{a['hora']}")
            if inicio - ahora > timedelta(hours=HORAS_CANCELAR):
                if col2.button("Cancelar", key=f"can{aid}{f}"):
                    cancelar(cli["id"], aid, f)
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
