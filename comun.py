"""Piezas comunes del panel: datos del negocio, formatos y enlaces."""
import json
import re
from datetime import date
from urllib.parse import quote
import pandas as pd
import streamlit as st
from db import q, run

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
LETRAS = ["L", "M", "X", "J", "V", "S", "D"]
ORDEN = ["Pendiente de pago", "Bono agotado", "Riesgo de baja", "Al dia", "Congelado", "Baja"]


def evento(nid, cid, tipo, detalle):
    run("INSERT INTO evento (negocio_id, cliente_id, tipo, fecha, detalle) VALUES (%s,%s,%s,%s,%s)",
        (nid, cid, tipo, date.today().isoformat(), detalle))


def tel_ok(t):
    return re.fullmatch(r"(34)?[6789]\d{8}", re.sub(r"[\s.+-]", "", t or "")) is not None


def tel_norm(t):
    return re.sub(r"[\s.+-]", "", t or "").removeprefix("34")


def fmt(d):
    return pd.to_datetime(d).strftime("%d/%m/%Y") if pd.notna(d) and d else "-"


def euros(x):
    return f"{x:,.0f} €".replace(",", ".")


def nombre_mes(periodo):
    a, m = periodo.split("-")[:2]
    return f"{MESES[int(m) - 1]} {a}"


def dias_texto(dias):
    return " ".join(LETRAS[int(d)] for d in dias.split(",") if d != "")


def dias_desde_texto(texto):
    out = [str(LETRAS.index(x)) for x in LETRAS if x in (texto or "").upper().replace(",", " ").split()]
    return ",".join(out)


def base_url():
    host = st.context.headers.get("host", "localhost:8501")
    return ("http://" if host.startswith(("localhost", "127.", "192.168.")) else "https://") + host


def enlace_socio(token):
    return f"{base_url()}/?t={token}"


def whatsapp(telefono, texto):
    return f"https://wa.me/34{tel_norm(telefono)}?text={quote(texto)}"


def meses_entre(inicio, fin):
    a = pd.to_datetime(inicio)
    b = pd.to_datetime(fin)
    return (b.year - a.year) * 12 + b.month - a.month


def estilo():
    st.markdown("""
    <style>
      h1, h2, h3 { letter-spacing: -0.01em; }
      [data-testid="stMetricValue"] { font-family: "Barlow Semi Condensed", sans-serif; font-weight: 700; }
      .parte { border-left: 6px solid #1F3FA6; background: #FFFFFF; padding: 1.1rem 1.4rem;
               border-radius: 0 0.6rem 0.6rem 0; margin-bottom: 0.6rem; }
      .parte.aviso { border-left-color: #C77700; }
      .parte.alerta { border-left-color: #B3261E; }
      .parte.bien { border-left-color: #2E7D4F; }
      .parte p { margin: 0; font-size: 1.05rem; }
      .parte b { font-size: 1.35rem; font-family: "Barlow Semi Condensed", sans-serif; }
      .etiqueta { display: inline-block; padding: 0.1rem 0.55rem; border-radius: 1rem;
                  font-size: 0.8rem; font-weight: 600; }
    </style>""", unsafe_allow_html=True)


def cargar(nid):
    """Todo lo que necesitan las pantallas sobre un negocio."""
    hoy = date.today()
    mes = hoy.strftime("%Y-%m")
    neg = q("SELECT * FROM negocio WHERE id=%s", (nid,)).iloc[0]
    cfg = json.loads(neg["config"] or "{}")
    planes = q("SELECT * FROM plan WHERE negocio_id=%s ORDER BY activo DESC, id", (nid,))
    clientes = q("""
        SELECT c.*, m.id AS membresia_id, m.estado AS membresia, m.fecha_inicio, m.sesiones_usadas,
               p.id AS plan_id, p.nombre AS plan, p.tipo AS plan_tipo, p.importe, p.meses, p.sesiones,
               (SELECT MAX(fecha) FROM asistencia a WHERE a.cliente_id=c.id) AS ultima,
               (SELECT estado FROM cobro co WHERE co.membresia_id=m.id AND co.periodo=%s) AS cobro_mes,
               (SELECT COUNT(*) FROM cobro co WHERE co.membresia_id=m.id AND co.estado='pendiente') AS pendientes
        FROM cliente c
        LEFT JOIN membresia m ON m.cliente_id=c.id
             AND m.id=(SELECT MAX(id) FROM membresia WHERE cliente_id=c.id)
        LEFT JOIN plan p ON p.id=m.plan_id
        WHERE c.negocio_id=%s""", (mes, nid))
    clientes["dias sin venir"] = (pd.Timestamp(hoy) - pd.to_datetime(clientes["ultima"])).dt.days
    clientes["restantes"] = clientes["sesiones"] - clientes["sesiones_usadas"]

    def situacion(r):
        if r["membresia"] == "baja":
            return "Baja"
        if r["membresia"] == "congelada":
            return "Congelado"
        if r["pendientes"] and r["pendientes"] > 0:
            return "Pendiente de pago"
        if r["plan_tipo"] == "bono" and r["restantes"] <= 0:
            return "Bono agotado"
        if pd.isna(r["dias sin venir"]) or r["dias sin venir"] > 14:
            return "Riesgo de baja"
        return "Al dia"

    socios = clientes[clientes["estado"] != "prueba"].copy()
    socios["situacion"] = socios.apply(situacion, axis=1) if len(socios) else []
    pruebas = clientes[clientes["estado"] == "prueba"].copy()
    cli = cfg.get("cliente", "cliente")
    return dict(nid=nid, negocio=neg, cfg=cfg, CLI=cli, CLIS=cli + "s", hoy=hoy, mes=mes,
                planes=planes, socios=socios, pruebas=pruebas, clientes=clientes)


def cuotas_debidas(ctx):
    """Membresias activas de pago recurrente a las que les toca cuota este mes y aun no la tienen."""
    s = ctx["socios"]
    s = s[(s["membresia"] == "activa") & (s["plan_tipo"] == "recurrente") & (s["cobro_mes"].isna())]
    if s.empty:
        return s
    toca = s.apply(lambda r: meses_entre(r["fecha_inicio"], ctx["hoy"]) % int(r["meses"] or 1) == 0, axis=1)
    return s[toca]
