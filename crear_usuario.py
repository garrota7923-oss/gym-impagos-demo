"""Crea un usuario gerente o le cambia la contrasena.
Uso: winpty python crear_usuario.py"""
import getpass
import tomllib
from sqlalchemy import create_engine
from db import hash_clave

with open(".streamlit/secrets.toml", "rb") as f:
    motor = create_engine(tomllib.load(f)["DATABASE_URL"])

with motor.begin() as c:
    # Limpia usuarios que se crearon sin email
    borrados = c.exec_driver_sql("DELETE FROM usuario WHERE email = ''").rowcount
    if borrados:
        print(f"Borrados {borrados} usuarios sin email.")

    negocios = c.exec_driver_sql("SELECT id, nombre FROM negocio ORDER BY id").fetchall()
    print("\nNegocios:")
    for nid, nombre in negocios:
        usuarios = [u[0] for u in c.exec_driver_sql(
            "SELECT email FROM usuario WHERE negocio_id=%s", (nid,)).fetchall()]
        print(f"  {nid}. {nombre}  (usuarios: {', '.join(usuarios) or 'ninguno'})")

    nid = int(input("\nNumero del negocio: ").strip())
    if nid not in [n[0] for n in negocios]:
        raise SystemExit("Ese numero no existe.")
    email = input("Email del gerente: ").strip().lower()
    if "@" not in email:
        raise SystemExit("Ese email no es valido.")
    clave = getpass.getpass("Contrasena (no se ve al escribir): ")
    if len(clave) < 8:
        raise SystemExit("La contrasena debe tener al menos 8 caracteres.")
    if clave != getpass.getpass("Repitela: "):
        raise SystemExit("Las contrasenas no coinciden.")

    c.exec_driver_sql("""INSERT INTO usuario (negocio_id, email, nombre, clave) VALUES (%s,%s,%s,%s)
                         ON CONFLICT (email) DO UPDATE SET clave=EXCLUDED.clave, negocio_id=EXCLUDED.negocio_id,
                         activo=TRUE""",
                      (nid, email, email.split("@")[0], hash_clave(clave)))
print(f"\nListo: {email} puede entrar en el negocio {nid}.")
