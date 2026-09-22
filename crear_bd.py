"""Base de datos generica para negocios con membresia (datos inventados)."""
import random, sqlite3
from datetime import date, timedelta

BD = "negocios.db"
HOY = date.today()
random.seed(5)

ESQUEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE negocio (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    config TEXT NOT NULL DEFAULT '{}',
    fecha_alta TEXT NOT NULL);

CREATE TABLE cliente (
    id INTEGER PRIMARY KEY,
    negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    nombre TEXT NOT NULL,
    apellidos TEXT,
    telefono TEXT NOT NULL,
    email TEXT,
    dni TEXT,
    estado TEXT NOT NULL DEFAULT 'activo',
    fecha_alta TEXT NOT NULL,
    notas TEXT,
    extra TEXT NOT NULL DEFAULT '{}',
    UNIQUE (negocio_id, telefono));

CREATE TABLE plan (
    id INTEGER PRIMARY KEY,
    negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    importe REAL NOT NULL,
    meses INTEGER,
    sesiones INTEGER,
    activo INTEGER NOT NULL DEFAULT 1);

CREATE TABLE membresia (
    id INTEGER PRIMARY KEY,
    negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    plan_id INTEGER NOT NULL REFERENCES plan(id),
    estado TEXT NOT NULL,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT,
    sesiones_usadas INTEGER NOT NULL DEFAULT 0);

CREATE TABLE cobro (
    id INTEGER PRIMARY KEY,
    negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    membresia_id INTEGER NOT NULL REFERENCES membresia(id),
    periodo TEXT NOT NULL,
    importe REAL NOT NULL,
    fecha TEXT,
    metodo TEXT,
    estado TEXT NOT NULL,
    UNIQUE (membresia_id, periodo));

CREATE TABLE actividad (
    id INTEGER PRIMARY KEY,
    negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    nombre TEXT NOT NULL,
    dias TEXT NOT NULL,
    hora TEXT NOT NULL,
    duracion_min INTEGER NOT NULL,
    aforo INTEGER NOT NULL);

CREATE TABLE asistencia (
    id INTEGER PRIMARY KEY,
    negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    actividad_id INTEGER NOT NULL REFERENCES actividad(id),
    fecha TEXT NOT NULL,
    es_prueba INTEGER NOT NULL DEFAULT 0,
    UNIQUE (cliente_id, actividad_id, fecha));

CREATE TABLE evento (
    id INTEGER PRIMARY KEY,
    negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    cliente_id INTEGER REFERENCES cliente(id),
    tipo TEXT NOT NULL,
    fecha TEXT NOT NULL,
    detalle TEXT);

CREATE INDEX ix_cliente ON cliente(negocio_id, estado);
CREATE INDEX ix_membresia ON membresia(negocio_id, cliente_id);
CREATE INDEX ix_cobro ON cobro(negocio_id, periodo);
CREATE INDEX ix_asistencia ON asistencia(negocio_id, fecha);
CREATE INDEX ix_evento ON evento(negocio_id, cliente_id);
"""

NOMBRES = ["Lucia","Hugo","Martina","Pablo","Sofia","Alvaro","Carla","Daniel","Paula","Javier",
           "Irene","Sergio","Nerea","Adrian","Laura","Marcos","Elena","Ruben","Noelia","Ivan",
           "Sara","Mario","Alba","Victor","Claudia","Oscar","Raquel","Diego","Ines","Bruno"]
APELLIDOS = ["Garcia","Lopez","Martin","Sanchez","Perez","Gomez","Ruiz","Diaz","Moreno",
             "Alvarez","Romero","Navarro","Torres","Molina","Ortega","Delgado","Castro"]
METODOS = ["Bizum", "Efectivo", "Tarjeta", "Domiciliacion"]
usados = set()


def telefono():
    while True:
        t = f"6{random.randint(10000000, 99999999)}"
        if t not in usados:
            usados.add(t)
            return t


def meses_entre(inicio, fin):
    m, out = date(inicio.year, inicio.month, 1), []
    while m <= fin:
        out.append(m)
        m = date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    return out


def crear_negocio(c, nombre, tipo, config, planes, actividades, n_clientes):
    nid = c.execute("INSERT INTO negocio (nombre, tipo, config, fecha_alta) VALUES (?,?,?,?)",
                    (nombre, tipo, config, HOY.isoformat())).lastrowid
    plan_ids = [c.execute("""INSERT INTO plan (negocio_id, nombre, tipo, importe, meses, sesiones)
                             VALUES (?,?,?,?,?,?)""", (nid, *p)).lastrowid for p in planes]
    act_ids = [c.execute("""INSERT INTO actividad (negocio_id, nombre, dias, hora, duracion_min, aforo)
                            VALUES (?,?,?,?,?,?)""", (nid, *a)).lastrowid for a in actividades]
    act_dias = {a: [int(x) for x in actividades[i][1].split(",")] for i, a in enumerate(act_ids)}
    inicio_hist = HOY - timedelta(days=90)

    for _ in range(n_clientes):
        alta = HOY - timedelta(days=random.randint(5, 700))
        r = random.random()
        estado_m = "baja" if r < 0.12 else "congelada" if r < 0.19 else "activa"
        cid = c.execute("""INSERT INTO cliente (negocio_id, nombre, apellidos, telefono, email,
                           estado, fecha_alta) VALUES (?,?,?,?,?,?,?)""",
                        (nid, random.choice(NOMBRES),
                         f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}", telefono(),
                         f"cliente{random.randint(100,9999)}@ejemplo.com" if random.random() < 0.7 else None,
                         "inactivo" if estado_m == "baja" else "activo", alta.isoformat())).lastrowid
        pid = random.choices(plan_ids, [0.8] + [0.2 / max(1, len(plan_ids) - 1)] * (len(plan_ids) - 1))[0]
        fin = None
        if estado_m == "baja":
            fin = max(alta + timedelta(days=30), HOY - timedelta(days=random.randint(20, 80)))
        mid = c.execute("""INSERT INTO membresia (negocio_id, cliente_id, plan_id, estado,
                           fecha_inicio, fecha_fin) VALUES (?,?,?,?,?,?)""",
                        (nid, cid, pid, estado_m, alta.isoformat(),
                         fin.isoformat() if fin else None)).lastrowid
        c.execute("INSERT INTO evento (negocio_id, cliente_id, tipo, fecha, detalle) VALUES (?,?,?,?,?)",
                  (nid, cid, "alta", alta.isoformat(), "Alta y membresia"))
        if estado_m == "congelada":
            c.execute("INSERT INTO evento (negocio_id, cliente_id, tipo, fecha, detalle) VALUES (?,?,?,?,?)",
                      (nid, cid, "congelacion", (HOY - timedelta(days=random.randint(3, 30))).isoformat(),
                       "Membresia congelada"))
        if fin:
            c.execute("INSERT INTO evento (negocio_id, cliente_id, tipo, fecha, detalle) VALUES (?,?,?,?,?)",
                      (nid, cid, "baja", fin.isoformat(), "Baja voluntaria"))

        importe, meses = c.execute("SELECT importe, meses FROM plan WHERE id=?", (pid,)).fetchone()
        ultimo = fin or HOY
        for m in meses_entre(max(alta, inicio_hist), ultimo):
            if ((m.year - alta.year) * 12 + m.month - alta.month) % meses:
                continue
            if estado_m == "congelada" and m.month == HOY.month:
                continue
            dia = m + timedelta(days=random.randint(0, 8))
            if dia > HOY:
                estado_c, fecha_c = "pendiente", None
            else:
                estado_c = "pendiente" if random.random() < 0.08 else "pagado"
                fecha_c = dia.isoformat() if estado_c == "pagado" else None
            c.execute("""INSERT INTO cobro (negocio_id, membresia_id, periodo, importe, fecha, metodo, estado)
                         VALUES (?,?,?,?,?,?,?)""",
                      (nid, mid, m.strftime("%Y-%m"), importe, fecha_c,
                       random.choice(METODOS) if fecha_c else None, estado_c))

        fav = random.choice(act_ids)
        freq = random.choice([0.35, 0.5, 0.65])
        hasta = fin or HOY
        if estado_m == "activa" and random.random() < 0.1:
            hasta = HOY - timedelta(days=random.randint(15, 40))
        d = max(alta, inicio_hist)
        while d <= hasta:
            if estado_m != "congelada" and d.weekday() in act_dias[fav] and random.random() < freq:
                c.execute("""INSERT OR IGNORE INTO asistencia (negocio_id, cliente_id, actividad_id, fecha)
                             VALUES (?,?,?,?)""", (nid, cid, fav, d.isoformat()))
            d += timedelta(days=1)

    for _ in range(6):
        cid = c.execute("""INSERT INTO cliente (negocio_id, nombre, apellidos, telefono, estado, fecha_alta)
                           VALUES (?,?,?,?, 'prueba', ?)""",
                        (nid, random.choice(NOMBRES), random.choice(APELLIDOS), telefono(),
                         HOY.isoformat())).lastrowid
        a = random.choice(act_ids)
        dia = HOY - timedelta(days=random.randint(1, 20))
        c.execute("""INSERT OR IGNORE INTO asistencia (negocio_id, cliente_id, actividad_id, fecha, es_prueba)
                     VALUES (?,?,?,?,1)""", (nid, cid, a, dia.isoformat()))
    return nid


def main():
    c = sqlite3.connect(BD)
    c.executescript(ESQUEMA)
    horas = ["09:30", "10:45", "12:00", "16:00", "17:15", "18:30", "19:45", "21:00"]
    crear_negocio(c, "Club de Boxeo (demo)", "gimnasio",
                  '{"cliente": "socio", "actividad": "clase"}',
                  [("Cuota mensual", "recurrente", 65.0, 1, None),
                   ("Cuota trimestral", "recurrente", 180.0, 3, None)],
                  [(f"Boxeo {h}", "0,1,2,3,4", h, 60, 14) for h in horas],
                  55)
    crear_negocio(c, "Academia de Ingles (demo)", "academia",
                  '{"cliente": "alumno", "actividad": "grupo"}',
                  [("Mensualidad 2 dias", "recurrente", 70.0, 1, None),
                   ("Mensualidad intensivo", "recurrente", 110.0, 1, None)],
                  [("Ingles A2", "0,2", "17:00", 90, 10),
                   ("Ingles B1", "0,2", "18:30", 90, 10),
                   ("Ingles B2", "1,3", "18:30", 90, 10),
                   ("Conversacion C1", "4", "19:00", 60, 8)],
                  35)
    c.commit()
    for n, t in c.execute("SELECT id, nombre FROM negocio"):
        cli = c.execute("SELECT COUNT(*) FROM cliente WHERE negocio_id=? AND estado!='prueba'", (n,)).fetchone()[0]
        asi = c.execute("SELECT COUNT(*) FROM asistencia WHERE negocio_id=?", (n,)).fetchone()[0]
        cob = c.execute("SELECT COUNT(*) FROM cobro WHERE negocio_id=?", (n,)).fetchone()[0]
        print(f"{t}: {cli} clientes, {asi} asistencias, {cob} cobros")
    c.close()


if __name__ == "__main__":
    main()
