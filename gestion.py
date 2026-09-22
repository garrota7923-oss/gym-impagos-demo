import json
import re
import secrets
import time
from datetime import date
import pandas as pd
import streamlit as st
from db import q, run, clave_ok

st.set_page_config(page_title="Gestion de membresias", layout="wide")

if "t" in st.query_params:
    from reservas import vista_socio
    vista_socio(st.query_params["t"])
    st.stop()


def evento(nid, cid, tipo, detalle):
    run("INSERT INTO evento (negocio_id, cliente_id, tipo, fecha, detalle) VALUES (%s,%s,%s,%s,%s)",
        (nid, cid, tipo, date.today().isoformat(), detalle))


def tel_ok(t):
    return re.fullmatch(r"(34)?[6789]\d{8}", re.sub(r"[\s.+-]", "", t or "")) is not None


def tel_norm(t):
    return re.sub(r"[\s.+-]", "", t or "").removeprefix("34")


def fmt(d):
    return pd.to_datetime(d).strftime("%d/%m/%Y") if pd.notna(d) and d else "-"


# ---------- Login ----------
if "usuario" not in st.session_state:
    st.title("Acceso para gerentes")
    fallos = st.session_state.get("fallos", 0)
    with st.form("login"):
        email = st.text_input("Email")
        clave = st.text_input("Contrasena", type="password")
        if st.form_submit_button("Entrar"):
            if fallos >= 5:
                time.sleep(3)                       # frena a quien prueba contrasenas a lo loco
            u = q("SELECT * FROM usuario WHERE email=%s AND activo", (email.strip().lower(),))
            if len(u) and clave_ok(clave, u.iloc[0]["clave"]):
                st.session_state["usuario"] = u.iloc[0].drop("clave").to_dict()
                st.session_state["fallos"] = 0
                st.rerun()
            st.session_state["fallos"] = fallos + 1
            st.error("Email o contrasena incorrectos")
    st.stop()

usuario = st.session_state["usuario"]
nid = int(usuario["negocio_id"])
st.sidebar.write(f"Sesion: **{usuario['email']}**")
if st.sidebar.button("Cerrar sesion"):
    del st.session_state["usuario"]
    st.rerun()
negocios = q("SELECT * FROM negocio WHERE id=%s", (nid,))
cfg = json.loads(negocios.set_index("id").loc[nid, "config"])
CLI = cfg.get("cliente", "cliente")            # socio / alumno / miembro
CLIS = CLI + "s"
hoy = date.today()
mes = hoy.strftime("%Y-%m")

planes = q("SELECT * FROM plan WHERE negocio_id=%s AND activo=1", (nid,))
clientes = q("""
    SELECT c.*, m.id AS membresia_id, m.estado AS membresia, p.nombre AS plan, p.importe,
           (SELECT MAX(fecha) FROM asistencia a WHERE a.cliente_id=c.id) AS ultima,
           (SELECT estado FROM cobro co WHERE co.membresia_id=m.id AND co.periodo=%s) AS cobro_mes
    FROM cliente c
    LEFT JOIN membresia m ON m.cliente_id=c.id
         AND m.id=(SELECT MAX(id) FROM membresia WHERE cliente_id=c.id)
    LEFT JOIN plan p ON p.id=m.plan_id
    WHERE c.negocio_id=%s""", (mes, nid))
clientes["dias sin venir"] = (pd.Timestamp(hoy) - pd.to_datetime(clientes["ultima"])).dt.days
socios = clientes[clientes["estado"] != "prueba"]
pruebas = clientes[clientes["estado"] == "prueba"]


def situacion(r):
    if r["membresia"] == "baja":
        return "Baja"
    if r["membresia"] == "congelada":
        return "Congelado"
    if r["cobro_mes"] == "pendiente":
        return "Pendiente de pago"
    if pd.isna(r["dias sin venir"]) or r["dias sin venir"] > 14:
        return "Riesgo de baja"
    return "Al dia"


socios = socios.assign(situacion=socios.apply(situacion, axis=1))
activos = socios[socios["membresia"] == "activa"]
cobros_mes = q("SELECT estado, SUM(importe) AS total FROM cobro WHERE negocio_id=%s AND periodo=%s GROUP BY estado",
               (nid, mes)).set_index("estado")["total"]

st.title(negocios.set_index("id").loc[nid, "nombre"])
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(f"{CLIS.capitalize()} activos", len(activos))
k2.metric(f"Cobrado {mes}", f"{cobros_mes.get('pagado', 0):.0f} / "
                           f"{cobros_mes.get('pagado', 0) + cobros_mes.get('pendiente', 0):.0f} €")
k3.metric("Pendientes de pago", int((socios["situacion"] == "Pendiente de pago").sum()))
k4.metric("Riesgo de baja (+14 dias)", int((socios["situacion"] == "Riesgo de baja").sum()))
k5.metric("Clases de prueba", len(pruebas))

t1, t2, t3, t4, t5, t6 = st.tabs([CLIS.capitalize(), f"Alta de {CLI}", "Ficha", "Cobros del mes",
                                   "Pruebas", "Clases de hoy"])

# ---------- Listado ----------
with t1:
    ORDEN = ["Pendiente de pago", "Riesgo de baja", "Al dia", "Congelado", "Baja"]
    a, b = st.columns([1, 2])
    filtro = a.multiselect("Situacion", ORDEN, default=ORDEN[:4])
    buscar = b.text_input("Buscar por nombre o telefono")
    v = socios[socios["situacion"].isin(filtro)].copy()
    if buscar:
        s = buscar.lower()
        v = v[(v["nombre"] + " " + v["apellidos"].fillna("")).str.lower().str.contains(s)
              | v["telefono"].str.contains(s)]
    v["situacion"] = pd.Categorical(v["situacion"], ORDEN, ordered=True)
    v = v.sort_values(["situacion", "dias sin venir"], ascending=[True, False])
    v["ultima clase"] = v["ultima"].map(fmt)
    st.caption(f"{len(v)} {CLIS}")
    st.dataframe(v[["id", "nombre", "apellidos", "telefono", "plan", "situacion",
                    "ultima clase", "dias sin venir"]].rename(columns={"id": "nº"}),
                 hide_index=True, width="stretch")

# ---------- Alta ----------
with t2:
    st.caption("Obligatorio: nombre y telefono. El numero se genera solo.")
    with st.form("alta", clear_on_submit=True):
        a, b = st.columns(2)
        nombre = a.text_input("Nombre *", key="a_nombre")
        apellidos = b.text_input("Apellidos", key="a_apellidos")
        tel = a.text_input("Telefono *", key="a_tel", placeholder="600123456")
        email = b.text_input("Email", key="a_email")
        dni = a.text_input("DNI (opcional)", key="a_dni")
        plan = b.selectbox("Plan", planes["id"],
                           format_func=lambda i: f"{planes.set_index('id').loc[i, 'nombre']} "
                                                 f"({planes.set_index('id').loc[i, 'importe']:.0f} €)")
        if st.form_submit_button(f"Dar de alta"):
            t = tel_norm(tel)
            existe = clientes[clientes["telefono"] == t]
            if not nombre.strip():
                st.error("El nombre es obligatorio")
            elif not tel_ok(tel):
                st.error("Telefono no valido: debe ser un numero espanol de 9 digitos")
            elif not existe.empty:
                e = existe.iloc[0]
                st.error(f"Ese telefono ya es de {e['nombre']} (nº {e['id']}, estado {e['estado']})")
            else:
                cid = run("""INSERT INTO cliente (negocio_id, nombre, apellidos, telefono, email, dni,
                             estado, fecha_alta, token) VALUES (%s,%s,%s,%s,%s,%s,'activo',%s,%s) RETURNING id""",
                          (nid, nombre.strip(), apellidos.strip() or None, t, email.strip() or None,
                           dni.strip().upper() or None, hoy.isoformat(), secrets.token_urlsafe(8)))
                mid = run("""INSERT INTO membresia (negocio_id, cliente_id, plan_id, estado, fecha_inicio)
                             VALUES (%s,%s,%s,'activa',%s) RETURNING id""", (nid, cid, int(plan), hoy.isoformat()))
                run("""INSERT INTO cobro (negocio_id, membresia_id, periodo, importe, estado)
                       VALUES (%s,%s,%s,%s,'pendiente')""",
                    (nid, mid, mes, float(planes.set_index("id").loc[plan, "importe"])))
                evento(nid, cid, "alta", "Alta y membresia")
                st.success(f"{nombre} dado de alta con el numero {cid}")
                st.rerun()

# ---------- Ficha ----------
with t3:
    o = socios.sort_values("nombre")
    cid = st.selectbox(CLI.capitalize(), o["id"],
                       format_func=lambda i: f"{o.set_index('id').loc[i, 'nombre']} "
                                             f"{o.set_index('id').loc[i, 'apellidos'] or ''} (nº {i})")
    s = o.set_index("id").loc[cid]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Situacion", s["situacion"])
    m2.metric("Plan", s["plan"] or "-")
    m3.metric("Ultima clase", fmt(s["ultima"]))
    m4.metric(f"{CLI.capitalize()} desde", fmt(s["fecha_alta"]))

    host = st.context.headers.get("host", "localhost:8501")
    base = ("http://" if host.startswith(("localhost", "127.", "192.168.")) else "https://") + host
    if s.get("token"):
        st.text_input("Enlace personal para reservar (envialo por WhatsApp o email)",
                      f"{base}/?t={s['token']}", disabled=False)
    with st.expander("Editar datos"):
        with st.form("editar"):
            a, b = st.columns(2)
            nombre = a.text_input("Nombre", s["nombre"])
            apellidos = b.text_input("Apellidos", s["apellidos"] or "")
            tel = a.text_input("Telefono", s["telefono"])
            email = b.text_input("Email", s["email"] or "")
            notas = st.text_area("Notas", s["notas"] or "", height=70)
            if st.form_submit_button("Guardar"):
                t = tel_norm(tel)
                if not tel_ok(tel):
                    st.error("Telefono no valido")
                elif t in clientes[clientes["id"] != cid]["telefono"].values:
                    st.error("Ese telefono ya es de otra persona")
                else:
                    run("UPDATE cliente SET nombre=%s, apellidos=%s, telefono=%s, email=%s, notas=%s WHERE id=%s",
                        (nombre.strip(), apellidos.strip() or None, t, email.strip() or None,
                         notas.strip() or None, int(cid)))
                    evento(nid, int(cid), "edicion", "Datos actualizados")
                    st.rerun()

    mid = int(s["membresia_id"])
    b1, b2, _ = st.columns([1, 1, 3])
    if s["membresia"] == "activa":
        if b1.button("Congelar membresia"):
            run("UPDATE membresia SET estado='congelada' WHERE id=%s", (mid,))
            evento(nid, int(cid), "congelacion", "Membresia congelada")
            st.rerun()
        if b2.button("Dar de baja"):
            run("UPDATE membresia SET estado='baja', fecha_fin=%s WHERE id=%s", (hoy.isoformat(), mid))
            run("UPDATE cliente SET estado='inactivo' WHERE id=%s", (int(cid),))
            evento(nid, int(cid), "baja", "Baja registrada")
            st.rerun()
    elif s["membresia"] == "congelada":
        if b1.button("Reactivar"):
            run("UPDATE membresia SET estado='activa' WHERE id=%s", (mid,))
            evento(nid, int(cid), "reactivacion", "Membresia reactivada")
            st.rerun()
    else:
        if b1.button("Volver a dar de alta"):
            run("UPDATE membresia SET estado='activa', fecha_fin=NULL WHERE id=%s", (mid,))
            run("UPDATE cliente SET estado='activo' WHERE id=%s", (int(cid),))
            evento(nid, int(cid), "reactivacion", "Vuelve a darse de alta")
            st.rerun()

    c1, c2, c3 = st.columns(3)
    c1.subheader("Cobros")
    c1.dataframe(q("SELECT periodo, importe, estado, fecha, metodo FROM cobro WHERE membresia_id=%s "
                   "ORDER BY periodo DESC", (mid,)), hide_index=True, width="stretch")
    c2.subheader("Asistencia")
    c2.dataframe(q("""SELECT a.fecha, ac.nombre AS clase FROM asistencia a JOIN actividad ac
                      ON ac.id=a.actividad_id WHERE a.cliente_id=%s ORDER BY a.fecha DESC LIMIT 30""",
                   (int(cid),)), hide_index=True, width="stretch")
    c3.subheader("Historial")
    c3.dataframe(q("SELECT fecha, tipo, detalle FROM evento WHERE cliente_id=%s ORDER BY fecha DESC",
                   (int(cid),)), hide_index=True, width="stretch")

# ---------- Cobros del mes ----------
with t4:
    pend = q("""SELECT co.id, c.nombre || ' ' || COALESCE(c.apellidos,'') AS persona, c.telefono,
                       p.nombre AS plan, co.importe
                FROM cobro co JOIN membresia m ON m.id=co.membresia_id
                JOIN cliente c ON c.id=m.cliente_id JOIN plan p ON p.id=m.plan_id
                WHERE co.negocio_id=%s AND co.periodo=%s AND co.estado='pendiente'
                ORDER BY persona""", (nid, mes))
    st.subheader(f"Pendientes de {mes}: {len(pend)} ({pend['importe'].sum():.0f} €)")
    metodo = st.selectbox("Metodo de pago", ["Bizum", "Efectivo", "Tarjeta", "Domiciliacion", "Transferencia"])
    for _, r in pend.iterrows():
        a, b, c = st.columns([3, 1, 1])
        a.write(f"**{r['persona']}** · {r['telefono']} · {r['plan']}")
        b.write(f"{r['importe']:.0f} €")
        if c.button("Marcar pagado", key=f"pag{r['id']}"):
            run("UPDATE cobro SET estado='pagado', fecha=%s, metodo=%s WHERE id=%s",
                (hoy.isoformat(), metodo, int(r["id"])))
            st.rerun()
    st.divider()
    faltan = q("""SELECT m.id, p.importe FROM membresia m JOIN plan p ON p.id=m.plan_id
                  WHERE m.negocio_id=%s AND m.estado='activa' AND p.meses=1
                  AND NOT EXISTS (SELECT 1 FROM cobro co WHERE co.membresia_id=m.id AND co.periodo=%s)""",
               (nid, mes))
    if len(faltan) and st.button(f"Generar cuotas de {mes} que faltan ({len(faltan)})"):
        for _, r in faltan.iterrows():
            run("INSERT INTO cobro (negocio_id, membresia_id, periodo, importe, estado) VALUES (%s,%s,%s,%s,'pendiente')",
                (nid, int(r["id"]), mes, float(r["importe"])))
        st.rerun()

# ---------- Pruebas ----------
with t5:
    st.caption(f"Quien viene a probar aun no es {CLI}. Si se apunta, pasa a {CLI} y conserva su historial.")
    if pruebas.empty:
        st.info("No hay clases de prueba pendientes")
    plan_p = st.selectbox("Plan al convertir", planes["id"], key="plan_prueba",
                          format_func=lambda i: planes.set_index("id").loc[i, "nombre"])
    for _, p in pruebas.iterrows():
        a, b, c = st.columns([3, 1, 1])
        a.write(f"**{p['nombre']} {p['apellidos'] or ''}** · {p['telefono']} · probo el {fmt(p['ultima'])}")
        if b.button(f"Hacer {CLI}", key=f"conv{p['id']}"):
            run("UPDATE cliente SET estado='activo', fecha_alta=%s WHERE id=%s", (hoy.isoformat(), int(p["id"])))
            mid = run("""INSERT INTO membresia (negocio_id, cliente_id, plan_id, estado, fecha_inicio)
                         VALUES (%s,%s,%s,'activa',%s) RETURNING id""", (nid, int(p["id"]), int(plan_p), hoy.isoformat()))
            run("INSERT INTO cobro (negocio_id, membresia_id, periodo, importe, estado) VALUES (%s,%s,%s,%s,'pendiente')",
                (nid, mid, mes, float(planes.set_index("id").loc[plan_p, "importe"])))
            evento(nid, int(p["id"]), "alta", "Alta tras clase de prueba")
            st.rerun()
        if c.button("Descartar", key=f"desc{p['id']}"):
            run("DELETE FROM asistencia WHERE cliente_id=%s", (int(p["id"]),))
            run("DELETE FROM cliente WHERE id=%s", (int(p["id"]),))
            st.rerun()

with t6:
    dia = st.date_input("Dia", hoy, format="DD/MM/YYYY", key="dia_clases")
    acts = q("SELECT * FROM actividad WHERE negocio_id=%s ORDER BY hora", (nid,))
    acts = acts[acts["dias"].apply(lambda x: dia.weekday() in [int(d) for d in x.split(",")])]
    if acts.empty:
        st.info("Ese dia no hay clases")
    for _, a in acts.iterrows():
        lista = q("""SELECT r.id, r.estado, c.nombre || ' ' || COALESCE(c.apellidos,'') AS persona
                     FROM reserva r JOIN cliente c ON c.id=r.cliente_id
                     WHERE r.actividad_id=%s AND r.fecha=%s AND r.estado IN ('reservada','asistida')
                     ORDER BY persona""", (int(a["id"]), dia.isoformat()))
        vinieron = int((lista["estado"] == "asistida").sum())
        with st.expander(f"{a['hora']} · {a['nombre']} · {len(lista)}/{a['aforo']} reservas · {vinieron} asistieron"):
            for _, r in lista.iterrows():
                x, y = st.columns([3, 1])
                x.write(r["persona"])
                if r["estado"] == "asistida":
                    y.success("Vino")
                elif y.button("Ha venido", key=f"asi{r['id']}"):
                    run("UPDATE reserva SET estado='asistida' WHERE id=%s", (int(r["id"]),))
                    rr = q("SELECT * FROM reserva WHERE id=%s", (int(r["id"]),)).iloc[0]
                    run("""INSERT INTO asistencia (negocio_id, cliente_id, actividad_id, fecha)
                           VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING""", (nid, int(rr["cliente_id"]), int(rr["actividad_id"]), rr["fecha"]))
                    st.rerun()
