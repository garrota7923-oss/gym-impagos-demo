"""Deja un negocio de demo como nuevo: borra sus datos y los vuelve a inventar (misma logica que crear_bd.py)."""
import random
from datetime import date
import streamlit as st
import crear_bd
from db import motor

# Orden de borrado: primero lo que apunta a otras tablas
TABLAS = ["reserva", "asistencia", "cobro", "evento", "membresia", "cliente", "plan", "actividad"]


def es_demo(email):
    """Solo los emails puestos a mano en st.secrets["DEMO_EMAILS"]. Sin esa clave, nadie."""
    lista = st.secrets.get("DEMO_EMAILS") or []
    if isinstance(lista, str):
        lista = [lista]
    return bool(email) and email.strip().lower() in {e.strip().lower() for e in lista}


class _Res:
    def __init__(self, r):
        self.r = r

    @property
    def lastrowid(self):
        return self.r.fetchone()[0]

    def fetchone(self):
        return self.r.fetchone()


class _Cursor:
    """Traduce las ordenes de crear_bd.py (sqlite) a PostgreSQL."""
    def __init__(self, con):
        self.con = con

    def execute(self, sql, p=()):
        sql = sql.replace("?", "%s")
        if "INSERT OR IGNORE" in sql:
            sql = sql.replace("INSERT OR IGNORE", "INSERT") + " ON CONFLICT DO NOTHING"
        elif sql.lstrip().startswith("INSERT"):
            sql += " RETURNING id"
        return _Res(self.con.exec_driver_sql(sql, tuple(p)))


def reiniciar(nid, tipo, email):
    """Borra y regenera los datos del negocio nid en una sola transaccion (si algo falla, no cambia nada)."""
    if not es_demo(email):
        raise PermissionError("Este usuario no es de demo")
    _, _, planes, actividades, n = crear_bd.DEMOS.get(tipo, crear_bd.DEMOS["gimnasio"])
    crear_bd.HOY = date.today()
    crear_bd.usados.clear()
    random.seed(5)
    with motor().begin() as con:
        for t in TABLAS:
            con.exec_driver_sql(f"DELETE FROM {t} WHERE negocio_id=%s", (nid,))
        crear_bd.rellenar(_Cursor(con), nid, planes, actividades, n)
