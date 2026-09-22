"""Crea las tablas en Supabase y copia los datos de negocios.db.
Uso: python migrar_a_supabase.py
Solo funciona si la base de Supabase esta vacia (no machaca datos)."""
import getpass
import sqlite3
import tomllib
from sqlalchemy import create_engine, text
from db import hash_clave

ESQUEMA = """
CREATE TABLE negocio (
    id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, tipo TEXT NOT NULL,
    config TEXT NOT NULL DEFAULT '{}', fecha_alta TEXT NOT NULL);
CREATE TABLE usuario (
    id SERIAL PRIMARY KEY, negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    email TEXT NOT NULL UNIQUE, nombre TEXT, clave TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'dueno', activo BOOLEAN NOT NULL DEFAULT TRUE);
CREATE TABLE cliente (
    id SERIAL PRIMARY KEY, negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    nombre TEXT NOT NULL, apellidos TEXT, telefono TEXT NOT NULL, email TEXT, dni TEXT,
    estado TEXT NOT NULL DEFAULT 'activo', fecha_alta TEXT NOT NULL, notas TEXT,
    extra TEXT NOT NULL DEFAULT '{}', token TEXT UNIQUE,
    UNIQUE (negocio_id, telefono));
CREATE TABLE plan (
    id SERIAL PRIMARY KEY, negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    nombre TEXT NOT NULL, tipo TEXT NOT NULL, importe NUMERIC(8,2) NOT NULL,
    meses INTEGER, sesiones INTEGER, activo INTEGER NOT NULL DEFAULT 1);
CREATE TABLE membresia (
    id SERIAL PRIMARY KEY, negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    cliente_id INTEGER NOT NULL REFERENCES cliente(id), plan_id INTEGER NOT NULL REFERENCES plan(id),
    estado TEXT NOT NULL, fecha_inicio TEXT NOT NULL, fecha_fin TEXT,
    sesiones_usadas INTEGER NOT NULL DEFAULT 0);
CREATE TABLE cobro (
    id SERIAL PRIMARY KEY, negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    membresia_id INTEGER NOT NULL REFERENCES membresia(id), periodo TEXT NOT NULL,
    importe NUMERIC(8,2) NOT NULL, fecha TEXT, metodo TEXT, estado TEXT NOT NULL,
    UNIQUE (membresia_id, periodo));
CREATE TABLE actividad (
    id SERIAL PRIMARY KEY, negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    nombre TEXT NOT NULL, dias TEXT NOT NULL, hora TEXT NOT NULL,
    duracion_min INTEGER NOT NULL, aforo INTEGER NOT NULL);
CREATE TABLE asistencia (
    id SERIAL PRIMARY KEY, negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    cliente_id INTEGER NOT NULL REFERENCES cliente(id), actividad_id INTEGER NOT NULL REFERENCES actividad(id),
    fecha TEXT NOT NULL, es_prueba INTEGER NOT NULL DEFAULT 0,
    UNIQUE (cliente_id, actividad_id, fecha));
CREATE TABLE reserva (
    id SERIAL PRIMARY KEY, negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    cliente_id INTEGER NOT NULL REFERENCES cliente(id), actividad_id INTEGER NOT NULL REFERENCES actividad(id),
    fecha TEXT NOT NULL, estado TEXT NOT NULL, creada_en TEXT NOT NULL,
    UNIQUE (cliente_id, actividad_id, fecha));
CREATE TABLE evento (
    id SERIAL PRIMARY KEY, negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    cliente_id INTEGER REFERENCES cliente(id), tipo TEXT NOT NULL, fecha TEXT NOT NULL, detalle TEXT);
CREATE INDEX ix_cliente ON cliente(negocio_id, estado);
CREATE INDEX ix_membresia ON membresia(negocio_id, cliente_id);
CREATE INDEX ix_cobro ON cobro(negocio_id, periodo);
CREATE INDEX ix_asistencia ON asistencia(negocio_id, fecha);
CREATE INDEX ix_reserva ON reserva(negocio_id, actividad_id, fecha, estado);
CREATE INDEX ix_evento ON evento(negocio_id, cliente_id);
"""
TABLAS = ["negocio", "cliente", "plan", "membresia", "cobro", "actividad", "asistencia", "reserva", "evento"]

with open(".streamlit/secrets.toml", "rb") as f:
    url = tomllib.load(f)["DATABASE_URL"]
pg = create_engine(url)
lite = sqlite3.connect("negocios.db")

with pg.begin() as c:
    ya = c.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='negocio'")).scalar()
    if ya:
        raise SystemExit("La base de Supabase ya tiene tablas. No hago nada para no borrar datos.")
    for sentencia in ESQUEMA.split(";"):
        if sentencia.strip():
            c.exec_driver_sql(sentencia)
    for t in TABLAS:
        cur = lite.execute(f"SELECT * FROM {t}")
        cols = [d[0] for d in cur.description]
        filas = cur.fetchall()
        if filas:
            sql = f"INSERT INTO {t} ({','.join(cols)}) VALUES ({','.join(['%s'] * len(cols))})"
            c.exec_driver_sql(sql, [tuple(f) for f in filas])
        c.exec_driver_sql(f"SELECT setval(pg_get_serial_sequence('{t}','id'), COALESCE(MAX(id),1)) FROM {t}")
        print(f"  {t}: {len(filas)} filas")

    # Cierra las tablas a la API publica de Supabase. Nuestra app entra como propietaria y no se ve afectada.
    for t in TABLAS + ["usuario"]:
        c.exec_driver_sql(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")

    print("\nAhora crea un usuario gerente para cada negocio.")
    for nid, nombre in c.exec_driver_sql("SELECT id, nombre FROM negocio ORDER BY id").fetchall():
        email = input(f"Email del gerente de '{nombre}': ").strip().lower()
        clave = getpass.getpass("Contrasena (no se ve al escribir): ")
        c.exec_driver_sql("INSERT INTO usuario (negocio_id, email, nombre, clave) VALUES (%s,%s,%s,%s)",
                          (nid, email, nombre, hash_clave(clave)))
print("\nMigracion terminada.")
