"""Actualiza la base de datos de Supabase para la version 2 del panel.
Se puede ejecutar varias veces sin problema. Uso: python actualizar_bd.py"""
import tomllib
from sqlalchemy import create_engine

with open(".streamlit/secrets.toml", "rb") as f:
    motor = create_engine(tomllib.load(f)["DATABASE_URL"])

CAMBIOS = [
    "ALTER TABLE negocio ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE negocio ADD COLUMN IF NOT EXISTS fecha_baja TEXT",
    "ALTER TABLE actividad ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE",
]
with motor.begin() as c:
    for sql in CAMBIOS:
        c.exec_driver_sql(sql)
print("Base de datos actualizada")
