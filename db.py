"""Conexion a la base de datos (Supabase / PostgreSQL) y utilidades comunes."""
import hashlib
import hmac
import secrets
from decimal import Decimal
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine


@st.cache_resource
def motor():
    return create_engine(st.secrets["DATABASE_URL"], pool_pre_ping=True, pool_size=3, max_overflow=2)


def q(sql, p=()):
    """Consulta que devuelve una tabla (DataFrame)."""
    with motor().connect() as c:
        df = pd.read_sql_query(sql, c, params=tuple(p))
    for col in df.columns:                     # los importes llegan como Decimal: pasar a numero
        if df[col].dtype == object and df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df


def run(sql, p=()):
    """Ejecuta una orden. Si la orden lleva RETURNING, devuelve ese valor."""
    with motor().begin() as c:
        r = c.exec_driver_sql(sql, tuple(p))
        return r.fetchone()[0] if r.returns_rows else None


def hash_clave(clave):
    sal = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal), 200_000).hex()
    return f"pbkdf2${sal}${h}"


def clave_ok(clave, guardada):
    try:
        _, sal, h = guardada.split("$")
    except (ValueError, AttributeError):
        return False
    calc = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal), 200_000).hex()
    return hmac.compare_digest(calc, h)
