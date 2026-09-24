"""Deja un negocio de demo como nuevo: borra sus datos y los vuelve a inventar (misma logica que crear_bd.py)."""
import random
import re
import secrets
from datetime import date, timedelta
import streamlit as st
from psycopg2.extras import execute_values
import crear_bd
from db import motor

# Negocios de demo, fijados en el codigo: cambiarlos exige un PR (no basta con tocar secrets ni el nombre)
DEMO_NEGOCIOS = {1}
# Todo va por lotes al final, en este orden (primero lo que otras tablas apuntan).
# cliente y membresia reciben su id por adelantado de la secuencia para no hacer un viaje por fila.
EN_LOTE = ("cliente", "membresia", "evento", "cobro", "asistencia")
CON_ID = ("cliente", "membresia")
# Orden de borrado: primero lo que apunta a otras tablas
TABLAS = ["reserva", "asistencia", "cobro", "evento", "membresia", "cliente", "plan", "actividad"]


def es_demo(email):
    """Solo los emails puestos a mano en st.secrets["DEMO_EMAILS"]. Sin esa clave, nadie."""
    lista = st.secrets.get("DEMO_EMAILS") or []
    if isinstance(lista, str):
        lista = [lista]
    return bool(email) and email.strip().lower() in {e.strip().lower() for e in lista}


class _Res:
    def __init__(self, fila):
        self.fila = fila

    @property
    def lastrowid(self):
        return self.fila[0]

    def fetchone(self):
        return self.fila


class _Cursor:
    """Traduce las ordenes de crear_bd.py (sqlite) a PostgreSQL y las junta por tabla (un viaje por tabla)."""
    def __init__(self, con):
        self.con = con
        self.lotes = {}
        self.ids = {t: [] for t in CON_ID}
        self.planes = {}

    def _id(self, tabla):
        """Siguiente id de la secuencia; se piden de 1000 en 1000 (un viaje)."""
        if not self.ids[tabla]:
            self.ids[tabla] = [r[0] for r in self.con.exec_driver_sql(
                "SELECT nextval(pg_get_serial_sequence(%s, 'id')) FROM generate_series(1, 1000)", (tabla,))]
        return self.ids[tabla].pop(0)

    def execute(self, sql, p=()):
        sql = sql.strip()
        if sql.startswith("SELECT importe, meses FROM plan"):
            return _Res(self.planes[p[0]])
        tabla = re.match(r"INSERT (?:OR IGNORE )?INTO (\w+)", sql)
        tabla = tabla and tabla.group(1)
        if tabla in EN_LOTE:
            m = re.search(r"VALUES\s*\((.*)\)", sql, re.S)
            base = sql[:m.start()].replace("INSERT OR IGNORE", "INSERT") + "VALUES %s"
            plantilla = m.group(1).replace("?", "%s")
            if "INSERT OR IGNORE" in sql:
                base += " ON CONFLICT DO NOTHING"
            nuevo = None
            if tabla in CON_ID:
                nuevo = self._id(tabla)
                base = base.replace(f"INTO {tabla} (", f"INTO {tabla} (id, ", 1)
                plantilla, p = "%s, " + plantilla, (nuevo, *p)
            self.lotes.setdefault(tabla, {}).setdefault((base, f"({plantilla})"), []).append(tuple(p))
            return _Res((nuevo,))
        sql = sql.replace("?", "%s")
        if sql.startswith("INSERT"):
            sql += " RETURNING id"
        fila = self.con.exec_driver_sql(sql, tuple(p)).fetchone()
        if tabla == "plan":
            self.planes[fila[0]] = (p[3], p[4])  # (negocio_id, nombre, tipo, importe, meses, sesiones)
        return _Res(fila)

    def volcar(self):
        cur = self.con.connection.cursor()
        for tabla in EN_LOTE:
            for (base, plantilla), filas in self.lotes.get(tabla, {}).items():
                execute_values(cur, base, filas, template=plantilla, page_size=1000)
        self.lotes = {}


def reiniciar(nid, tipo, email):
    """Borra y regenera los datos del negocio nid en una sola transaccion (si algo falla, no cambia nada).
    Tres candados: email en DEMO_EMAILS, nid en DEMO_NEGOCIOS y el usuario de ese email es de ese negocio."""
    nid = int(nid)
    if not es_demo(email) or nid not in DEMO_NEGOCIOS:
        raise PermissionError("Este usuario o negocio no es de demo")
    _, _, planes, actividades, n = crear_bd.DEMOS.get(tipo, crear_bd.DEMOS["gimnasio"])
    crear_bd.HOY = date.today()
    crear_bd.usados.clear()
    random.seed(5)
    with motor().begin() as con:
        suyo = con.exec_driver_sql("SELECT negocio_id FROM usuario WHERE lower(email)=lower(%s) AND activo",
                                   (email.strip(),)).fetchall()
        if [r[0] for r in suyo] != [nid]:
            raise PermissionError("El usuario no pertenece a este negocio")
        # Todos los DELETE en un viaje: psycopg2 sustituye los parametros en el cliente, asi que admite varias ordenes
        con.exec_driver_sql("; ".join(f"DELETE FROM {t} WHERE negocio_id=%(nid)s" for t in TABLAS), {"nid": nid})
        cur = _Cursor(con)
        crear_bd.rellenar(cur, nid, planes, actividades, n)
        cur.volcar()
        _enlaces_y_reservas(con, nid)


def _enlaces_y_reservas(con, nid):
    """Enlace personal de cada socio y reservas de los proximos 6 dias (como migrar_reservas.py)."""
    db = con.connection.cursor()
    ids = [r[0] for r in con.exec_driver_sql("SELECT id FROM cliente WHERE negocio_id=%s", (nid,)).fetchall()]
    execute_values(db, "UPDATE cliente SET token=v.token FROM (VALUES %s) AS v(id, token, nid) "
                       "WHERE cliente.id=v.id AND cliente.negocio_id=v.nid",
                   [(i, secrets.token_urlsafe(8), nid) for i in ids], page_size=1000)
    socios = [r[0] for r in con.exec_driver_sql("""SELECT c.id FROM cliente c JOIN membresia m ON m.cliente_id=c.id
                                                   WHERE c.negocio_id=%s AND m.estado='activa'""", (nid,)).fetchall()]
    hoy, filas = date.today(), set()
    for aid, dias, aforo in con.exec_driver_sql("SELECT id, dias, aforo FROM actividad WHERE negocio_id=%s ORDER BY id",
                                                (nid,)).fetchall():
        dias = [int(x) for x in dias.split(",")]
        for k in range(6):
            d = hoy + timedelta(days=k)
            if d.weekday() in dias:
                n = min(len(socios), aforo, int(aforo * random.choice([0.2, 0.4, 0.6, 0.85, 1.0])))
                filas |= {(nid, cid, aid, d.isoformat(), "reservada", hoy.isoformat()) for cid in random.sample(socios, n)}
    execute_values(db, "INSERT INTO reserva (negocio_id, cliente_id, actividad_id, fecha, estado, creada_en) "
                       "VALUES %s ON CONFLICT DO NOTHING", sorted(filas), page_size=1000)
