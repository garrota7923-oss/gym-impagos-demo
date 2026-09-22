import json
import re
import sqlite3
from datetime import date, timedelta
import pandas as pd
import streamlit as st

BD = "negocios.db"
st.set_page_config(page_title="Gestion de membresias", layout="wide")


def q(sql, p=()):
    with sqlite3.connect(BD) as c:
        return pd.read_sql_query(sql, c, params=p)


def run(sql, p=()):
    with sqlite3.connect(BD) as c:
        c.execute("PRAGMA foreign_keys = ON")
        cur = c.execute(sql, p)
        return cur.lastrowid


def evento(nid, cid, tipo, detalle):
    run("INSERT INTO evento (negocio_id, cliente_id, tipo, fecha, detalle) VALUES (?,?,?,?,?)",
        (nid, cid, tipo, date.today().isoformat(), detalle))


def tel_ok(t):
    return re.fullmatch(r"(34)?[6789]\d{8}", re.sub(r"[\s.+-]", "", t or "")) is not None


def tel_norm(t):
    return re.sub(r"[\s.+-]", "", t or "").removeprefix("34")


def fmt(d):
    return pd.to_datetime(d).strftime("%d/%m/%Y") if pd.notna(d) and d else "-"


negocios = q("SELECT * FROM negocio ORDER BY id")
nid = st.sidebar.selectbox("Negocio", negocios["id"],
                           format_func=lambda i: negocios.set_index("id").loc[i, "nombre"])
cfg = json.loads(negocios.set_index("id").loc[nid, "config"])
CLI = cfg.get("cliente", "cliente")
CLIS = CLI + "s"
hoy = date.today()
mes = hoy.strftime("%Y-%m")

planes = q("SELECT * FROM plan WHERE negocio_id=? AND activo=1", (nid,))
clientes = q("""
    SELECT c.*, m.id AS membresia_id, m.estado AS membresia, p.nombre AS plan, p.importe,
           (SELECT MAX(fecha) FROM asistencia a WHERE a.cliente_id=c.id) AS ultima,
           (SELECT estado FROM cobro co WHERE co.membresia_id=m.id AND co.periodo=?) AS cobro_mes
    FROM cliente c
    LEFT JOIN membresia m ON m.cliente_id=c.id
         AND m.id=(SELECT MAX(id) FROM membresia WHERE cliente_id=c.id)
    LEFT JOIN plan p ON p.id=m.plan_id
    WHERE c.negocio_id=?""", (mes, nid))
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
cobros_mes = q("SELECT estado, SUM(importe) AS total FROM cobro WHERE negocio_id=? AND periodo=? GROUP BY estado",
               (nid, mes)).set_index("estado")["total"]

st.title(negocios.set_index("id").loc[nid, "nombre"])
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(f"{CLIS.capitalize()} activos", len(activos))
k2.metric(f"Cobrado {mes}", f"{cobros_mes.get('pagado', 0):.0f} / "
                           f"{cobros_mes.get('pagado', 0) + cobros_mes.get('pendiente', 0):.0f} €")
k3.metric("Pendientes de pago", int((socios["situacion"] == "Pendiente de pago").sum()))
k4.metric("Riesgo de baja (+14 dias)", int((socios["situacion"] == "Riesgo de baja").sum()))
k5.metric("Clases de prueba", len(pruebas))

t1, t2, t3, t4, t5 = st.tabs([CLIS.capitalize(), f"Alta de {CLI}", "Ficha", "Cobros del mes", "Pruebas"])

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
                             estado, fecha_alta) VALUES (?,?,?,?,?,?,'activo',?)""",
                          (nid, nombre.strip(), apellidos.strip() or None, t, email.strip() or None,
                           dni.strip().upper() or None, hoy.isoformat()))
                mid = run("""INSERT INTO membresia (negocio_id, cliente_id, plan_id, estado, fecha_inicio)
                             VALUES (?,?,?,'activa',?)""", (nid, cid, int(plan), hoy.isoformat()))
                run("""INSERT INTO cobro (negocio_id, membresia_id, periodo, importe, estado)
                       VALUES (?,?,?,?,'pendiente')""",
                    (nid, mid, mes, float(planes.set_index("id").loc[plan, "importe"])))
                evento(nid, cid, "alta", "Alta y membresia")
                st.success(f"{nombre} dado de alta con el numero {cid}")
                st.rerun()

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
                    run("UPDATE cliente SET nombre=?, apellidos=?, telefono=?, email=?, notas=? WHERE id=?",
                        (nombre.strip(), apellidos.strip() or None, t, email.strip() or None,
                         notas.strip() or None, int(cid)))
                    evento(nid, int(cid), "edicion", "Datos actualizados")
                    st.rerun()

    mid = int(s["membresia_id"])
    b1, b2, _ = st.columns([1, 1, 3])
    if s["membresia"] == "activa":
        if b1.button("Congelar membresia"):
            run("UPDATE membresia SET estado='congelada' WHERE id=?", (mid,))
            evento(nid, int(cid), "congelacion", "Membresia congelada")
            st.rerun()
        if b2.button("Dar de baja"):
            run("UPDATE membresia SET estado='baja', fecha_fin=? WHERE id=?", (hoy.isoformat(), mid))
            run("UPDATE cliente SET estado='inactivo' WHERE id=?", (int(cid),))
            evento(nid, int(cid), "baja", "Baja registrada")
            st.rerun()
    elif s["membresia"] == "congelada":
        if b1.button("Reactivar"):
            run("UPDATE membresia SET estado='activa' WHERE id=?", (mid,))
            evento(nid, int(cid), "reactivacion", "Membresia reactivada")
            st.rerun()
    else:
        if b1.button("Volver a dar de alta"):
            run("UPDATE membresia SET estado='activa', fecha_fin=NULL WHERE id=?", (mid,))
            run("UPDATE cliente SET estado='activo' WHERE id=?", (int(cid),))
            evento(nid, int(cid), "reactivacion", "Vuelve a darse de alta")
            st.rerun()

    c1, c2, c3 = st.columns(3)
    c1.subheader("Cobros")
    c1.dataframe(q("SELECT periodo, importe, estado, fecha, metodo FROM cobro WHERE membresia_id=? "
                   "ORDER BY periodo DESC", (mid,)), hide_index=True, width="stretch")
    c2.subheader("Asistencia")
    c2.dataframe(q("""SELECT a.fecha, ac.nombre AS clase FROM asistencia a JOIN actividad ac
                      ON ac.id=a.actividad_id WHERE a.cliente_id=? ORDER BY a.fecha DESC LIMIT 30""",
                   (int(cid),)), hide_index=True, width="stretch")
    c3.subheader("Historial")
    c3.dataframe(q("SELECT fecha, tipo, detalle FROM evento WHERE cliente_id=? ORDER BY fecha DESC",
                   (int(cid),)), hide_index=True, width="stretch")

with t4:
    pend = q("""SELECT co.id, c.nombre || ' ' || COALESCE(c.apellidos,'') AS persona, c.telefono,
                       p.nombre AS plan, co.importe
                FROM cobro co JOIN membresia m ON m.id=co.membresia_id
                JOIN cliente c ON c.id=m.cliente_id JOIN plan p ON p.id=m.plan_id
                WHERE co.negocio_id=? AND co.periodo=? AND co.estado='pendiente'
                ORDER BY persona""", (nid, mes))
    st.subheader(f"Pendientes de {mes}: {len(pend)} ({pend['importe'].sum():.0f} €)")
    metodo = st.selectbox("Metodo de pago", ["Bizum", "Efectivo", "Tarjeta", "Domiciliacion", "Transferencia"])
    for _, r in pend.iterrows():
        a, b, c = st.columns([3, 1, 1])
        a.write(f"**{r['persona']}** · {r['telefono']} · {r['plan']}")
        b.write(f"{r['importe']:.0f} €")
        if c.button("Marcar pagado", key=f"pag{r['id']}"):
            run("UPDATE cobro SET estado='pagado', fecha=?, metodo=? WHERE id=?",
                (hoy.isoformat(), metodo, int(r["id"])))
            st.rerun()
    st.divider()
    faltan = q("""SELECT m.id, p.importe FROM membresia m JOIN plan p ON p.id=m.plan_id
                  WHERE m.negocio_id=? AND m.estado='activa' AND p.meses=1
                  AND NOT EXISTS (SELECT 1 FROM cobro co WHERE co.membresia_id=m.id AND co.periodo=?)""",
               (nid, mes))
    if len(faltan) and st.button(f"Generar cuotas de {mes} que faltan ({len(faltan)})"):
        for _, r in faltan.iterrows():
            run("INSERT INTO cobro (negocio_id, membresia_id, periodo, importe, estado) VALUES (?,?,?,?,'pendiente')",
                (nid, int(r["id"]), mes, float(r["importe"])))
        st.rerun()

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
            run("UPDATE cliente SET estado='activo', fecha_alta=? WHERE id=?", (hoy.isoformat(), int(p["id"])))
            mid = run("""INSERT INTO membresia (negocio_id, cliente_id, plan_id, estado, fecha_inicio)
                         VALUES (?,?,?,'activa',?)""", (nid, int(p["id"]), int(plan_p), hoy.isoformat()))
            run("INSERT INTO cobro (negocio_id, membresia_id, periodo, importe, estado) VALUES (?,?,?,?,'pendiente')",
                (nid, mid, mes, float(planes.set_index("id").loc[plan_p, "importe"])))
            evento(nid, int(p["id"]), "alta", "Alta tras clase de prueba")
            st.rerun()
        if c.button("Descartar", key=f"desc{p['id']}"):
            run("DELETE FROM asistencia WHERE cliente_id=?", (int(p["id"]),))
            run("DELETE FROM cliente WHERE id=?", (int(p["id"]),))
            st.rerun()
