"""Pantallas del panel del gerente."""
import io
import secrets
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from db import q, run, clave_ok, hash_clave
from comun import (cargar, cuotas_debidas, evento, tel_ok, tel_norm, fmt, euros, nombre_mes, dias_texto,
                   dias_desde_texto, enlace_socio, whatsapp, estilo, ORDEN, DIAS, LETRAS)


def ctx():
    estilo()
    if "usuario" not in st.session_state:
        st.stop()
    return cargar(int(st.session_state["usuario"]["negocio_id"]))


def parte(texto, tipo=""):
    st.markdown(f'<div class="parte {tipo}"><p>{texto}</p></div>', unsafe_allow_html=True)


def nombre_completo(r):
    ape = r["apellidos"] if isinstance(r["apellidos"], str) else ""
    return f"{r['nombre']} {ape}".strip()


# ------------------------------------------------------------------ Inicio
def inicio():
    c = ctx()
    s, hoy = c["socios"], c["hoy"]
    saludo = "Buenos dias" if pd.Timestamp.now().hour < 14 else "Buenas tardes"
    st.title(c["negocio"]["nombre"])
    st.caption(f"{saludo}. Hoy es {DIAS[hoy.weekday()].lower()} {hoy.day} de {nombre_mes(c['mes']).split()[0]}.")

    deben = s[s["situacion"] == "Pendiente de pago"]
    importe = q("""SELECT COALESCE(SUM(importe),0) AS t FROM cobro
                   WHERE negocio_id=%s AND estado='pendiente'""", (c["nid"],)).iloc[0]["t"]
    riesgo = s[s["situacion"] == "Riesgo de baja"].sort_values("dias sin venir", ascending=False)
    faltan = cuotas_debidas(c)

    st.subheader("Lo que hay que hacer hoy")
    if len(faltan):
        parte(f"<b>{len(faltan)}</b> cuotas de {nombre_mes(c['mes'])} todavia no estan generadas. "
              "Generalas en Cobros para saber quien debe.", "aviso")
    if len(deben):
        parte(f"<b>{len(deben)} {c['CLIS']}</b> tienen cuotas sin pagar, en total <b>{euros(importe)}</b>.", "alerta")
    if len(riesgo):
        parte(f"<b>{len(riesgo)} {c['CLIS']}</b> llevan mas de dos semanas sin venir. "
              "Un mensaje a tiempo evita muchas bajas.", "aviso")
    if len(c["pruebas"]):
        parte(f"<b>{len(c['pruebas'])}</b> personas han hecho una clase de prueba y aun no se han apuntado.")
    if not (len(faltan) or len(deben) or len(riesgo) or len(c["pruebas"])):
        parte("Todo al dia. No hay cobros pendientes ni socios en riesgo.", "bien")

    col1, col2 = st.columns(2)
    with col1.container(border=True):
        st.markdown("**Deben cuota**")
        if deben.empty:
            st.caption("Nadie. Bien.")
        for _, r in deben.head(6).iterrows():
            a, b = st.columns([3, 2])
            a.write(nombre_completo(r))
            b.link_button("Recordar por WhatsApp", whatsapp(
                r["telefono"], f"Hola {r['nombre']}, te recordamos que tienes pendiente la cuota de "
                               f"{c['negocio']['nombre']}. Cualquier duda, dinos. Gracias."), width="stretch")
        if len(deben) > 6:
            st.caption(f"Y {len(deben) - 6} mas. Los tienes todos en Cobros.")
    with col2.container(border=True):
        st.markdown("**Llevan tiempo sin venir**")
        if riesgo.empty:
            st.caption("Nadie. Bien.")
        for _, r in riesgo.head(6).iterrows():
            a, b = st.columns([3, 2])
            a.write(f"{nombre_completo(r)}  \n:gray[{int(r['dias sin venir']) if pd.notna(r['dias sin venir']) else 'sin'} dias]")
            b.link_button("Escribirle", whatsapp(
                r["telefono"], f"Hola {r['nombre']}, hace tiempo que no te vemos por {c['negocio']['nombre']}. "
                               f"¿Todo bien? Aqui tienes tu enlace para reservar: {enlace_socio(r['token'])}"),
                width="stretch")

    st.subheader("Como va el club")
    activos = s[s["membresia"] == "activa"]
    altas = s[pd.to_datetime(s["fecha_alta"]).dt.strftime("%Y-%m") == c["mes"]]
    bajas = q("""SELECT COUNT(*) AS n FROM evento WHERE negocio_id=%s AND tipo='baja'
                 AND LEFT(fecha,7)=%s""", (c["nid"], c["mes"])).iloc[0]["n"]
    cob = q("""SELECT estado, SUM(importe) AS t FROM cobro WHERE negocio_id=%s AND periodo LIKE %s
               GROUP BY estado""", (c["nid"], c["mes"] + "%")).set_index("estado")["t"]
    k = st.columns(4)
    k[0].metric(f"{c['CLIS'].capitalize()} activos", len(activos), border=True)
    k[1].metric(f"Cobrado en {nombre_mes(c['mes']).split()[0]}",
                f"{cob.get('pagado', 0):.0f} de {cob.get('pagado', 0) + cob.get('pendiente', 0):.0f} €", border=True)
    k[2].metric("Altas este mes", len(altas), border=True)
    k[3].metric("Bajas este mes", int(bajas), border=True)

    g1, g2 = st.columns(2)
    ingresos = q("""SELECT LEFT(periodo,7) AS mes, SUM(importe) AS euros FROM cobro
                    WHERE negocio_id=%s AND estado='pagado' GROUP BY 1 ORDER BY 1 DESC LIMIT 6""", (c["nid"],))
    with g1.container(border=True):
        st.markdown("**Ingresos cobrados por mes**")
        if len(ingresos):
            ingresos["mes"] = ingresos["mes"].map(lambda m: nombre_mes(m)[:3].capitalize() + " " + m[2:4])
            st.bar_chart(ingresos.iloc[::-1].set_index("mes"), height=220, color="#1F3FA6")
    semanas = q("""SELECT fecha FROM asistencia WHERE negocio_id=%s AND fecha >= %s""",
                (c["nid"], (hoy - timedelta(weeks=10)).isoformat()))
    with g2.container(border=True):
        st.markdown("**Asistencias por semana**")
        if len(semanas):
            sem = pd.to_datetime(semanas["fecha"]).dt.to_period("W").dt.start_time.value_counts().sort_index()
            sem.index = sem.index.strftime("%d/%m")
            st.line_chart(sem.rename("asistencias"), height=220, color="#1F3FA6")


# ------------------------------------------------------------------ Socios
def socios():
    c = ctx()
    s = c["socios"]
    st.title(c["CLIS"].capitalize())
    a, b = st.columns([2, 3])
    buscar = a.text_input("Buscar", placeholder="Nombre o telefono", label_visibility="collapsed")
    filtro = b.pills("Situacion", ORDEN, default=ORDEN[:4], selection_mode="multi", label_visibility="collapsed")
    v = s[s["situacion"].isin(filtro or ORDEN)].copy()
    if buscar:
        t = buscar.lower()
        v = v[v.apply(lambda r: t in nombre_completo(r).lower() or t in str(r["telefono"]), axis=1)]
    v["situacion"] = pd.Categorical(v["situacion"], ORDEN, ordered=True)
    v = v.sort_values(["situacion", "dias sin venir"], ascending=[True, False])
    v["nombre completo"] = v.apply(nombre_completo, axis=1)
    v["ultima clase"] = v["ultima"].map(fmt)
    sel = st.dataframe(
        v[["id", "nombre completo", "telefono", "plan", "situacion", "ultima clase", "dias sin venir"]],
        hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row", height=330,
        column_config={"id": st.column_config.NumberColumn("Nº", width="small"),
                       "nombre completo": "Nombre", "telefono": "Telefono", "plan": "Plan",
                       "situacion": "Situacion", "ultima clase": "Ultima clase",
                       "dias sin venir": st.column_config.NumberColumn("Dias sin venir", format="%d")})
    st.caption(f"{len(v)} {c['CLIS']}. Pulsa una fila para ver su ficha.")

    filas = sel.selection.rows if sel else []
    opciones = s.sort_values("nombre")["id"].astype(int).tolist()
    nombres = {int(r["id"]): f"{nombre_completo(r)} (nº {int(r['id'])})" for _, r in s.iterrows()}
    if filas:
        elegido = int(v.iloc[filas[0]]["id"])
        if st.session_state.get("_fila") != elegido:        # nueva fila pulsada en la tabla
            st.session_state["_fila"] = elegido
            st.session_state["ficha_sel"] = elegido
    if st.session_state.get("ficha_sel") not in opciones:
        st.session_state["ficha_sel"] = None
    cid = st.selectbox("Ficha de", opciones, key="ficha_sel", index=None,
                       format_func=lambda i: nombres[i], placeholder=f"Elige un {c['CLI']}")
    if cid is None:
        return
    ficha(c, int(cid))


def ficha(c, cid):
    s = c["socios"].set_index("id").loc[cid]
    nid, hoy, mes = c["nid"], c["hoy"], c["mes"]
    mid = int(s["membresia_id"])
    with st.container(border=True):
        a, b = st.columns([3, 2])
        a.subheader(nombre_completo(s))
        a.caption(f"{c['CLI'].capitalize()} nº {cid} desde el {fmt(s['fecha_alta'])} · {s['telefono']}")
        b.link_button("Enviar enlace de reservas por WhatsApp", whatsapp(
            s["telefono"], f"Hola {s['nombre']}, este es tu enlace para reservar clases en "
                           f"{c['negocio']['nombre']}: {enlace_socio(s['token'])}"), width="stretch", type="primary")
        m = st.columns(4)
        m[0].metric("Situacion", s["situacion"])
        m[1].metric("Plan", s["plan"] or "-")
        if s["plan_tipo"] == "bono":
            m[2].metric("Clases que le quedan", int(s["restantes"]))
        else:
            m[2].metric("Cuota", euros(s["importe"]) if pd.notna(s["importe"]) else "-")
        m[3].metric("Ultima clase", fmt(s["ultima"]))

        botones = st.columns(4)
        if s["membresia"] == "activa":
            if botones[0].button("Congelar", width="stretch"):
                run("UPDATE membresia SET estado='congelada' WHERE id=%s", (mid,))
                evento(nid, cid, "congelacion", "Membresia congelada")
                st.rerun()
            if botones[1].button("Dar de baja", width="stretch"):
                run("UPDATE membresia SET estado='baja', fecha_fin=%s WHERE id=%s", (hoy.isoformat(), mid))
                run("UPDATE cliente SET estado='inactivo' WHERE id=%s", (cid,))
                evento(nid, cid, "baja", "Baja registrada")
                st.rerun()
        elif s["membresia"] == "congelada":
            if botones[0].button("Reactivar", width="stretch", type="primary"):
                run("UPDATE membresia SET estado='activa' WHERE id=%s", (mid,))
                evento(nid, cid, "reactivacion", "Membresia reactivada")
                st.rerun()
        else:
            if botones[0].button("Volver a dar de alta", width="stretch", type="primary"):
                run("UPDATE membresia SET estado='activa', fecha_fin=NULL WHERE id=%s", (mid,))
                run("UPDATE cliente SET estado='activo' WHERE id=%s", (cid,))
                evento(nid, cid, "reactivacion", "Vuelve a darse de alta")
                st.rerun()
        if s["plan_tipo"] == "bono" and botones[2].button("Renovar bono", width="stretch"):
            n = q("SELECT COUNT(*) AS n FROM cobro WHERE membresia_id=%s", (mid,)).iloc[0]["n"]
            run("UPDATE membresia SET sesiones_usadas=0 WHERE id=%s", (mid,))
            run("INSERT INTO cobro (negocio_id, membresia_id, periodo, importe, estado) VALUES (%s,%s,%s,%s,'pendiente')",
                (nid, mid, f"{mes} bono {int(n) + 1}", float(s["importe"])))
            evento(nid, cid, "renovacion", "Bono renovado")
            st.rerun()

    t1, t2, t3, t4 = st.tabs(["Datos", "Cobros", "Asistencia", "Historial"])
    with t1:
        with st.form(f"editar{cid}"):
            a, b = st.columns(2)
            nombre = a.text_input("Nombre", s["nombre"])
            apellidos = b.text_input("Apellidos", s["apellidos"] or "")
            tel = a.text_input("Telefono", s["telefono"])
            email = b.text_input("Email", s["email"] or "")
            planes = c["planes"][c["planes"]["activo"] == 1]
            ids = planes["id"].tolist()
            plan = a.selectbox("Plan", ids, index=ids.index(int(s["plan_id"])) if int(s["plan_id"]) in ids else 0,
                               format_func=lambda i: planes.set_index("id").loc[i, "nombre"])
            dni = b.text_input("DNI (opcional)", s["dni"] or "")
            notas = st.text_area("Notas", s["notas"] or "", height=80)
            if st.form_submit_button("Guardar cambios", type="primary"):
                t = tel_norm(tel)
                if not nombre.strip():
                    st.error("Escribe el nombre")
                elif not tel_ok(tel):
                    st.error("Revisa el telefono: debe ser un numero espanol de 9 cifras")
                elif t in c["clientes"][c["clientes"]["id"] != cid]["telefono"].values:
                    st.error("Ese telefono ya pertenece a otra persona")
                else:
                    run("""UPDATE cliente SET nombre=%s, apellidos=%s, telefono=%s, email=%s, dni=%s, notas=%s
                           WHERE id=%s""", (nombre.strip(), apellidos.strip() or None, t, email.strip() or None,
                                           dni.strip().upper() or None, notas.strip() or None, cid))
                    if int(plan) != int(s["plan_id"]):
                        run("UPDATE membresia SET plan_id=%s, sesiones_usadas=0 WHERE id=%s", (int(plan), mid))
                        evento(nid, cid, "cambio de plan", planes.set_index("id").loc[plan, "nombre"])
                    evento(nid, cid, "edicion", "Datos actualizados")
                    st.rerun()
    with t2:
        st.dataframe(q("""SELECT periodo AS "Periodo", importe AS "Importe", estado AS "Estado",
                                 fecha AS "Pagado el", metodo AS "Metodo"
                          FROM cobro WHERE membresia_id=%s ORDER BY periodo DESC""", (mid,)),
                     hide_index=True, width="stretch")
    with t3:
        st.dataframe(q("""SELECT a.fecha AS "Fecha", ac.hora AS "Hora", ac.nombre AS "Clase"
                          FROM asistencia a JOIN actividad ac ON ac.id=a.actividad_id
                          WHERE a.cliente_id=%s ORDER BY a.fecha DESC LIMIT 60""", (cid,)),
                     hide_index=True, width="stretch")
    with t4:
        st.dataframe(q("""SELECT fecha AS "Fecha", tipo AS "Que paso", detalle AS "Detalle"
                          FROM evento WHERE cliente_id=%s ORDER BY fecha DESC, id DESC""", (cid,)),
                     hide_index=True, width="stretch")


# ------------------------------------------------------------------ Alta
def nuevo():
    c = ctx()
    st.title("Apuntar a alguien")
    tipo = st.segmented_control("Que quieres apuntar", [f"Nuevo {c['CLI']}", "Clase de prueba"],
                                default=f"Nuevo {c['CLI']}", label_visibility="collapsed")
    planes = c["planes"][c["planes"]["activo"] == 1]
    if planes.empty:
        st.warning("Primero crea al menos un plan en Ajustes > Planes y precios.")
        return
    if tipo == "Clase de prueba":
        acts = q("SELECT * FROM actividad WHERE negocio_id=%s AND activo ORDER BY hora", (c["nid"],))
        with st.form("prueba", clear_on_submit=True):
            st.caption("Quien viene a probar no es todavia " + c["CLI"] + ". Si luego se apunta, conservas su historial.")
            a, b = st.columns(2)
            nombre = a.text_input("Nombre *", key="p_nombre")
            tel = b.text_input("Telefono *", key="p_tel", placeholder="600123456")
            dia = a.date_input("Dia de la clase", c["hoy"], format="DD/MM/YYYY")
            act = b.selectbox("Clase", acts["id"].tolist() if len(acts) else [None],
                              format_func=lambda i: "-" if i is None else
                              f"{acts.set_index('id').loc[i, 'hora']} {acts.set_index('id').loc[i, 'nombre']}")
            origen = a.selectbox("Como nos ha conocido", ["Un amigo", "Instagram", "Google", "Pasaba por la puerta", "Otro"])
            if st.form_submit_button("Apuntar clase de prueba", type="primary"):
                t = tel_norm(tel)
                if not nombre.strip() or not tel_ok(tel):
                    st.error("Escribe el nombre y un telefono espanol de 9 cifras")
                elif t in c["clientes"]["telefono"].values:
                    st.error("Ese telefono ya esta registrado. Buscalo en " + c["CLIS"].capitalize())
                else:
                    partes = nombre.strip().split(" ", 1)
                    pid = run("""INSERT INTO cliente (negocio_id, nombre, apellidos, telefono, estado, fecha_alta,
                                 notas, token) VALUES (%s,%s,%s,%s,'prueba',%s,%s,%s) RETURNING id""",
                              (c["nid"], partes[0], partes[1] if len(partes) > 1 else None, t,
                               c["hoy"].isoformat(), f"Nos conocio por: {origen}", secrets.token_urlsafe(8)))
                    if act is not None:
                        run("""INSERT INTO asistencia (negocio_id, cliente_id, actividad_id, fecha, es_prueba)
                               VALUES (%s,%s,%s,%s,1) ON CONFLICT DO NOTHING""", (c["nid"], pid, int(act), dia.isoformat()))
                    evento(c["nid"], pid, "prueba", f"Clase de prueba el {fmt(dia)}")
                    st.success(f"Clase de prueba apuntada para {nombre.strip()}")
        return

    with st.form("alta", clear_on_submit=True):
        st.caption("Solo son obligatorios el nombre y el telefono. El numero de " + c["CLI"] + " se pone solo.")
        a, b = st.columns(2)
        nombre = a.text_input("Nombre *", key="a_nombre")
        apellidos = b.text_input("Apellidos", key="a_apellidos")
        tel = a.text_input("Telefono *", key="a_tel", placeholder="600123456")
        email = b.text_input("Email", key="a_email")
        plan = a.selectbox("Plan", planes["id"].tolist(), format_func=lambda i:
                           f"{planes.set_index('id').loc[i, 'nombre']} ({euros(planes.set_index('id').loc[i, 'importe'])})")
        dni = b.text_input("DNI (opcional)", key="a_dni")
        cobrar = st.checkbox("Crear ya su primera cuota como pendiente", value=True)
        if st.form_submit_button("Dar de alta", type="primary"):
            t = tel_norm(tel)
            existe = c["clientes"][c["clientes"]["telefono"] == t]
            if not nombre.strip():
                st.error("Escribe el nombre")
            elif not tel_ok(tel):
                st.error("Revisa el telefono: debe ser un numero espanol de 9 cifras")
            elif not existe.empty:
                e = existe.iloc[0]
                st.error(f"Ese telefono ya es de {e['nombre']} (nº {e['id']}). "
                         + ("Si vino a probar, conviertelo desde Pruebas." if e["estado"] == "prueba" else ""))
            else:
                cid = run("""INSERT INTO cliente (negocio_id, nombre, apellidos, telefono, email, dni, estado,
                             fecha_alta, token) VALUES (%s,%s,%s,%s,%s,%s,'activo',%s,%s) RETURNING id""",
                          (c["nid"], nombre.strip(), apellidos.strip() or None, t, email.strip() or None,
                           dni.strip().upper() or None, c["hoy"].isoformat(), secrets.token_urlsafe(8)))
                alta_membresia(c, cid, int(plan), cobrar)
                evento(c["nid"], cid, "alta", "Alta y membresia")
                st.success(f"{nombre.strip()} ya es {c['CLI']}, con el numero {cid}. "
                           "Mandale su enlace de reservas desde su ficha.")


def alta_membresia(c, cid, plan_id, cobrar=True):
    p = c["planes"].set_index("id").loc[plan_id]
    mid = run("""INSERT INTO membresia (negocio_id, cliente_id, plan_id, estado, fecha_inicio)
                 VALUES (%s,%s,%s,'activa',%s) RETURNING id""", (c["nid"], cid, plan_id, c["hoy"].isoformat()))
    if cobrar:
        periodo = c["mes"] if p["tipo"] == "recurrente" else f"{c['mes']} bono 1"
        run("""INSERT INTO cobro (negocio_id, membresia_id, periodo, importe, estado)
               VALUES (%s,%s,%s,%s,'pendiente') ON CONFLICT DO NOTHING""", (c["nid"], mid, periodo, float(p["importe"])))
    return mid


# ------------------------------------------------------------------ Cobros
def cobros():
    c = ctx()
    st.title("Cobros")
    faltan = cuotas_debidas(c)
    mes = q("""SELECT COUNT(*) AS n, COALESCE(SUM(importe), 0) AS t FROM cobro
               WHERE negocio_id=%s AND estado='pendiente' AND periodo LIKE %s""", (c["nid"], c["mes"] + "%")).iloc[0]
    sin_generar = faltan["importe"].sum() if len(faltan) else 0
    atras = q("""SELECT COUNT(*) AS n, COALESCE(SUM(importe), 0) AS t FROM cobro
                 WHERE negocio_id=%s AND estado='pendiente' AND LEFT(periodo,7) < %s""", (c["nid"], c["mes"])).iloc[0]
    nota = f"{int(mes['n'])} cobros pendientes" + (f" · incluye {euros(sin_generar)} sin generar" if sin_generar else "")
    izq, der = st.columns(2)
    izq.metric(f"Pendiente de {nombre_mes(c['mes'])}", euros(float(mes["t"]) + float(sin_generar)), border=True)
    izq.caption(nota)
    der.metric("Atrasado", euros(float(atras["t"])), border=True)
    der.caption(f"{int(atras['n'])} cobros de meses anteriores")
    if len(faltan):
        with st.container(border=True):
            st.markdown(f"**Faltan por generar {len(faltan)} cuotas de {nombre_mes(c['mes'])}** "
                        f"({euros(faltan['importe'].sum())}). Al generarlas quedan como pendientes de pago.")
            if st.button(f"Generar las {len(faltan)} cuotas", type="primary"):
                for _, r in faltan.iterrows():
                    run("""INSERT INTO cobro (negocio_id, membresia_id, periodo, importe, estado)
                           VALUES (%s,%s,%s,%s,'pendiente') ON CONFLICT DO NOTHING""",
                        (c["nid"], int(r["membresia_id"]), c["mes"], float(r["importe"])))
                st.rerun()

    pend = q("""SELECT co.id, co.periodo, co.importe, c.id AS cid, c.nombre, c.apellidos, c.telefono, p.nombre AS plan
                FROM cobro co JOIN membresia m ON m.id=co.membresia_id
                JOIN cliente c ON c.id=m.cliente_id JOIN plan p ON p.id=m.plan_id
                WHERE co.negocio_id=%s AND co.estado='pendiente' ORDER BY co.periodo, c.nombre""", (c["nid"],))
    atrasados = pend[pend["periodo"].str[:7] < c["mes"]] if len(pend) else pend
    if len(atrasados):
        with st.container(border=True):
            a, b = st.columns([3, 1])
            a.markdown(f"**{atrasados['cid'].nunique()} socios con cuotas atrasadas** "
                       f"({euros(atrasados['importe'].sum())})")
            if b.button("Recordar a todos", width="stretch"):
                st.session_state["recordar_todos"] = True
                hechos = set(q("""SELECT cliente_id FROM evento WHERE negocio_id=%s AND tipo='recordatorio'
                                  AND fecha=%s""", (c["nid"], date.today().isoformat()))["cliente_id"])
                for cid, g in atrasados.groupby("cid", sort=False):
                    if int(cid) in hechos:
                        continue
                    evento(c["nid"], int(cid), "recordatorio",
                           f"Recordatorio de {len(g)} cuotas atrasadas ({euros(g['importe'].sum())})")
            if st.session_state.get("recordar_todos"):
                st.caption("Pulsa cada enlace para abrir su WhatsApp con el mensaje ya escrito.")
                for cid, g in atrasados.groupby("cid", sort=False):
                    r = g.iloc[0]
                    meses = ", ".join(nombre_mes(p) for p in g["periodo"])
                    a, b = st.columns([3, 1])
                    a.markdown(f"{nombre_completo(r)} · :gray[{meses}] · **{euros(g['importe'].sum())}**")
                    if tel_ok(r["telefono"]):
                        b.link_button("WhatsApp", whatsapp(r["telefono"], f"Hola {r['nombre']}, esperamos que estes "
                                      f"bien. Te recordamos que tienes pendiente la cuota de {meses} "
                                      f"({euros(g['importe'].sum())}). Si ya la has pagado, ignora este mensaje. "
                                      f"Gracias."), width="stretch")
                    else:
                        b.caption("Sin telefono valido")
                if st.button("Cerrar lista"):
                    st.session_state["recordar_todos"] = False
                    st.rerun()
    st.subheader(f"Pendientes de pago: {len(pend)} ({euros(pend['importe'].sum() if len(pend) else 0)})")
    if pend.empty:
        st.success("No hay nada pendiente de cobrar.")
    metodo = st.segmented_control("Como paga", ["Bizum", "Efectivo", "Tarjeta", "Domiciliacion", "Transferencia"],
                                  default="Bizum")
    for _, r in pend.iterrows():
        with st.container(border=True):
            a, b, d, e = st.columns([4, 2, 2, 2])
            a.markdown(f"**{nombre_completo(r)}**  \n:gray[{r['plan']} de {nombre_mes(r['periodo'])}]")
            b.markdown(f"### {euros(r['importe'])}")
            d.link_button("Recordar", whatsapp(r["telefono"], f"Hola {r['nombre']}, te recordamos la cuota de "
                          f"{nombre_mes(r['periodo'])} ({euros(r['importe'])}). Gracias."), width="stretch")
            if e.button("Marcar pagado", key=f"pag{r['id']}", width="stretch", type="primary"):
                run("UPDATE cobro SET estado='pagado', fecha=%s, metodo=%s WHERE id=%s",
                    (c["hoy"].isoformat(), metodo or "Efectivo", int(r["id"])))
                st.rerun()

    with st.expander(f"Cobrado en {nombre_mes(c['mes'])}"):
        pag = q("""SELECT c.nombre AS "Nombre", co.importe AS "Importe", co.fecha AS "Fecha", co.metodo AS "Metodo",
                          co.id FROM cobro co JOIN membresia m ON m.id=co.membresia_id JOIN cliente c ON c.id=m.cliente_id
                   WHERE co.negocio_id=%s AND co.estado='pagado' AND LEFT(co.fecha,7)=%s ORDER BY co.fecha DESC""",
                (c["nid"], c["mes"]))
        st.dataframe(pag.drop(columns="id"), hide_index=True, width="stretch")
        if len(pag):
            deshacer = st.selectbox("¿Te equivocaste? Vuelve a poner como pendiente:", [None] + pag["id"].tolist(),
                                    format_func=lambda i: "-" if i is None else
                                    f"{pag.set_index('id').loc[i, 'Nombre']} ({euros(pag.set_index('id').loc[i, 'Importe'])})")
            if deshacer and st.button("Deshacer pago"):
                run("UPDATE cobro SET estado='pendiente', fecha=NULL, metodo=NULL WHERE id=%s", (int(deshacer),))
                st.rerun()


# ------------------------------------------------------------------ Clases
def clases():
    from reservas import reservar
    c = ctx()
    st.title("Clases")
    dia = st.date_input("Dia", c["hoy"], format="DD/MM/YYYY", label_visibility="collapsed")
    acts = q("SELECT * FROM actividad WHERE negocio_id=%s AND activo ORDER BY hora", (c["nid"],))
    acts = acts[acts["dias"].apply(lambda x: str(dia.weekday()) in x.split(","))]
    st.caption(f"{DIAS[dia.weekday()]} {fmt(dia)}")
    if acts.empty:
        st.info("Ese dia no hay clases. Puedes cambiar los horarios en Ajustes.")
        return
    activos = c["socios"][c["socios"]["membresia"] == "activa"]
    for _, a in acts.iterrows():
        lista = q("""SELECT r.id, r.estado, r.cliente_id, c.nombre, c.apellidos
                     FROM reserva r JOIN cliente c ON c.id=r.cliente_id
                     WHERE r.actividad_id=%s AND r.fecha=%s AND r.estado IN ('reservada','asistida')
                     ORDER BY c.nombre""", (int(a["id"]), dia.isoformat()))
        vinieron = int((lista["estado"] == "asistida").sum())
        lleno = len(lista) >= a["aforo"]
        with st.expander(f"{a['hora']}   {a['nombre']}   {len(lista)} de {a['aforo']} plazas"
                         + (f", han venido {vinieron}" if vinieron else "") + ("   COMPLETA" if lleno else "")):
            for _, r in lista.iterrows():
                x, y = st.columns([4, 2])
                x.write(nombre_completo(r))
                if r["estado"] == "asistida":
                    y.success("Ha venido")
                elif y.button("Ha venido", key=f"asi{r['id']}", width="stretch"):
                    marcar_asistencia(c, int(r["id"]))
                    st.rerun()
            libres = activos[~activos["id"].isin(lista["cliente_id"])]
            if not lleno and len(libres):
                x, y = st.columns([4, 2])
                quien = x.selectbox("Apuntar a", [None] + libres.sort_values("nombre")["id"].tolist(),
                                    key=f"sel{a['id']}", label_visibility="collapsed",
                                    format_func=lambda i: f"Apuntar a alguien que ha venido sin reservar" if i is None
                                    else nombre_completo(libres.set_index("id").loc[i].to_dict() | {}))
                if quien and y.button("Apuntar y marcar", key=f"add{a['id']}", width="stretch", type="primary"):
                    r = c["socios"].set_index("id").loc[quien]
                    ok, msg = reservar({"id": quien, "negocio_id": c["nid"]}, int(a["id"]), dia.isoformat())
                    if ok:
                        rid = q("SELECT id FROM reserva WHERE cliente_id=%s AND actividad_id=%s AND fecha=%s",
                                (int(quien), int(a["id"]), dia.isoformat())).iloc[0]["id"]
                        marcar_asistencia(c, int(rid))
                        st.rerun()
                    st.error(msg)


def marcar_asistencia(c, reserva_id):
    r = q("SELECT * FROM reserva WHERE id=%s", (reserva_id,)).iloc[0]
    run("UPDATE reserva SET estado='asistida' WHERE id=%s", (reserva_id,))
    nueva = run("""INSERT INTO asistencia (negocio_id, cliente_id, actividad_id, fecha)
                   VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id""",
                (c["nid"], int(r["cliente_id"]), int(r["actividad_id"]), r["fecha"]))
    if nueva:   # si tiene bono, gasta una clase
        run("""UPDATE membresia m SET sesiones_usadas = sesiones_usadas + 1 FROM plan p
               WHERE p.id=m.plan_id AND p.tipo='bono' AND m.cliente_id=%s AND m.estado='activa'""",
            (int(r["cliente_id"]),))


# ------------------------------------------------------------------ Pruebas
def pruebas():
    c = ctx()
    st.title("Clases de prueba")
    p = c["pruebas"]
    if p.empty:
        st.info("No hay nadie pendiente. Cuando venga alguien a probar, apuntalo en Apuntar > Clase de prueba.")
        return
    planes = c["planes"][c["planes"]["activo"] == 1]
    plan = st.selectbox("Plan que tendra si se apunta", planes["id"].tolist(),
                        format_func=lambda i: planes.set_index("id").loc[i, "nombre"])
    for _, r in p.sort_values("ultima", ascending=False).iterrows():
        with st.container(border=True):
            a, b, d, e = st.columns([4, 2, 2, 2])
            a.markdown(f"**{nombre_completo(r)}**  \n:gray[Probo el {fmt(r['ultima'])}. {r['notas'] or ''}]")
            b.link_button("Preguntarle", whatsapp(r["telefono"], f"Hola {r['nombre']}, ¿que tal la clase de prueba "
                          f"en {c['negocio']['nombre']}? Si quieres apuntarte, te ayudamos."), width="stretch")
            if d.button(f"Se apunta", key=f"conv{r['id']}", width="stretch", type="primary"):
                run("UPDATE cliente SET estado='activo', fecha_alta=%s WHERE id=%s", (c["hoy"].isoformat(), int(r["id"])))
                alta_membresia(c, int(r["id"]), int(plan))
                evento(c["nid"], int(r["id"]), "alta", "Alta tras clase de prueba")
                st.rerun()
            if e.button("No se apunta", key=f"desc{r['id']}", width="stretch"):
                run("DELETE FROM asistencia WHERE cliente_id=%s", (int(r["id"]),))
                run("DELETE FROM evento WHERE cliente_id=%s", (int(r["id"]),))
                run("DELETE FROM cliente WHERE id=%s", (int(r["id"]),))
                st.rerun()


# ------------------------------------------------------------------ Ajustes
def ajustes():
    c = ctx()
    nid = c["nid"]
    st.title("Ajustes")
    t1, t2, t3, t4, t5 = st.tabs(["Clases y horarios", "Planes y precios", "Mi negocio", "Mi cuenta", "Datos y baja"])

    with t1:
        st.caption("Edita directamente en la tabla. Dias: L M X J V S D separados por espacios. "
                   "Para quitar una clase, desmarca Activa (asi no pierdes su historial).")
        acts = q("SELECT id, nombre, dias, hora, duracion_min, aforo, activo FROM actividad WHERE negocio_id=%s ORDER BY hora",
                 (nid,))
        acts["dias"] = acts["dias"].map(dias_texto)
        ed = st.data_editor(acts, num_rows="dynamic", hide_index=True, width="stretch", key="ed_acts",
                            column_config={"id": None, "nombre": "Nombre", "dias": "Dias",
                                           "hora": st.column_config.TextColumn("Hora", help="Formato 18:30"),
                                           "duracion_min": st.column_config.NumberColumn("Minutos", min_value=15, step=15),
                                           "aforo": st.column_config.NumberColumn("Plazas", min_value=1, step=1),
                                           "activo": st.column_config.CheckboxColumn("Activa", default=True)})
        if st.button("Guardar clases", type="primary"):
            errores = []
            for _, r in ed.iterrows():
                if not isinstance(r["nombre"], str) or not r["nombre"].strip():
                    continue
                dias = dias_desde_texto(r["dias"])
                hora = str(r["hora"] or "").strip()
                if not dias or len(hora) != 5 or hora[2] != ":":
                    errores.append(r["nombre"])
                    continue
                vals = (r["nombre"].strip(), dias, hora, int(r["duracion_min"] or 60), int(r["aforo"] or 10),
                        bool(r["activo"]) if pd.notna(r["activo"]) else True)
                if pd.isna(r["id"]):
                    run("""INSERT INTO actividad (negocio_id, nombre, dias, hora, duracion_min, aforo, activo)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)""", (nid, *vals))
                else:
                    run("""UPDATE actividad SET nombre=%s, dias=%s, hora=%s, duracion_min=%s, aforo=%s, activo=%s
                           WHERE id=%s AND negocio_id=%s""", (*vals, int(r["id"]), nid))
            if errores:
                st.error("Revisa los dias u hora de: " + ", ".join(errores))
            else:
                st.success("Clases guardadas")

    with t2:
        st.caption("Recurrente: se cobra cada X meses. Bono: un numero de clases que se gasta al venir. "
                   "Para dejar de ofrecer un plan, desmarca Activo.")
        pl = c["planes"][["id", "nombre", "tipo", "importe", "meses", "sesiones", "activo"]].copy()
        pl["activo"] = pl["activo"] == 1
        ep = st.data_editor(pl, num_rows="dynamic", hide_index=True, width="stretch", key="ed_planes",
                            column_config={"id": None, "nombre": "Nombre",
                                           "tipo": st.column_config.SelectboxColumn("Tipo", options=["recurrente", "bono"],
                                                                                    default="recurrente"),
                                           "importe": st.column_config.NumberColumn("Precio (€)", min_value=0, format="%.2f"),
                                           "meses": st.column_config.NumberColumn("Cada cuantos meses", min_value=1),
                                           "sesiones": st.column_config.NumberColumn("Clases del bono", min_value=1),
                                           "activo": st.column_config.CheckboxColumn("Activo", default=True)})
        if st.button("Guardar planes", type="primary"):
            for _, r in ep.iterrows():
                if not isinstance(r["nombre"], str) or not r["nombre"].strip() or pd.isna(r["importe"]):
                    continue
                tipo = r["tipo"] if r["tipo"] in ("recurrente", "bono") else "recurrente"
                meses = int(r["meses"]) if tipo == "recurrente" and pd.notna(r["meses"]) else (1 if tipo == "recurrente" else None)
                ses = int(r["sesiones"]) if tipo == "bono" and pd.notna(r["sesiones"]) else (10 if tipo == "bono" else None)
                vals = (r["nombre"].strip(), tipo, float(r["importe"]), meses, ses,
                        1 if (r["activo"] if pd.notna(r["activo"]) else True) else 0)
                if pd.isna(r["id"]):
                    run("""INSERT INTO plan (negocio_id, nombre, tipo, importe, meses, sesiones, activo)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)""", (nid, *vals))
                else:
                    run("""UPDATE plan SET nombre=%s, tipo=%s, importe=%s, meses=%s, sesiones=%s, activo=%s
                           WHERE id=%s AND negocio_id=%s""", (*vals, int(r["id"]), nid))
            st.success("Planes guardados. Los cambios de precio se aplican a las cuotas nuevas.")

    with t3:
        with st.form("negocio"):
            nombre = st.text_input("Nombre del negocio", c["negocio"]["nombre"])
            vocab = st.selectbox("¿Como llamas a tus clientes?", ["socio", "alumno", "miembro", "cliente"],
                                 index=["socio", "alumno", "miembro", "cliente"].index(c["CLI"])
                                 if c["CLI"] in ["socio", "alumno", "miembro", "cliente"] else 0)
            if st.form_submit_button("Guardar", type="primary"):
                cfg = dict(c["cfg"], cliente=vocab)
                import json
                run("UPDATE negocio SET nombre=%s, config=%s WHERE id=%s", (nombre.strip(), json.dumps(cfg), nid))
                st.success("Guardado")
                st.rerun()

    with t4:
        u = st.session_state["usuario"]
        st.write(f"Entras como **{u['email']}**")
        with st.form("clave", clear_on_submit=True):
            actual = st.text_input("Contrasena actual", type="password")
            nueva = st.text_input("Contrasena nueva (minimo 8 caracteres)", type="password")
            repite = st.text_input("Repite la nueva", type="password")
            if st.form_submit_button("Cambiar contrasena", type="primary"):
                guardada = q("SELECT clave FROM usuario WHERE id=%s", (int(u["id"]),)).iloc[0]["clave"]
                if not clave_ok(actual, guardada):
                    st.error("La contrasena actual no es correcta")
                elif len(nueva) < 8 or nueva != repite:
                    st.error("La nueva debe tener 8 caracteres o mas y coincidir en los dos campos")
                else:
                    run("UPDATE usuario SET clave=%s WHERE id=%s", (hash_clave(nueva), int(u["id"])))
                    st.success("Contrasena cambiada")

    with t5:
        st.subheader("Descargar todos tus datos")
        st.caption("Un Excel con una hoja por tabla: clientes, cobros, asistencias, reservas y mas. Son tuyos.")
        if st.button("Preparar Excel"):
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as xl:
                for t in ["cliente", "membresia", "plan", "cobro", "actividad", "asistencia", "reserva", "evento"]:
                    df = q(f"SELECT * FROM {t} WHERE negocio_id=%s ORDER BY id", (nid,))
                    df.drop(columns=[x for x in ("token", "negocio_id") if x in df.columns]).to_excel(
                        xl, sheet_name=t, index=False)
            st.download_button("Descargar Excel", buf.getvalue(), file_name=f"datos_{date.today()}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        st.divider()
        st.subheader("Dar de baja el servicio")
        st.caption("Tu panel y los enlaces de reserva de tus " + c["CLIS"] + " dejaran de funcionar. "
                   "Descarga antes tus datos. Si cambias de opinion en los proximos 30 dias, escribenos y "
                   "reactivamos la cuenta; despues se borran.")
        with st.form("baja"):
            conf = st.text_input(f"Escribe el nombre del negocio para confirmar: {c['negocio']['nombre']}")
            if st.form_submit_button("Dar de baja mi negocio"):
                if conf.strip().lower() != c["negocio"]["nombre"].strip().lower():
                    st.error("El nombre no coincide. No se ha dado de baja nada.")
                else:
                    run("UPDATE negocio SET activo=FALSE, fecha_baja=%s WHERE id=%s", (date.today().isoformat(), nid))
                    run("UPDATE usuario SET activo=FALSE WHERE negocio_id=%s", (nid,))
                    del st.session_state["usuario"]
                    st.session_state["baja_ok"] = True
                    st.rerun()
