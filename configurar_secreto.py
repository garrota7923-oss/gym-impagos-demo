"""Guarda la direccion de Supabase en .streamlit/secrets.toml sin tener que editar nada a mano."""
import getpass
import os
from urllib.parse import quote

print("Copia en Supabase la direccion del 'Session pooler' (boton Connect).")
url = input("Pegala aqui tal cual, con [YOUR-PASSWORD] dentro: ").strip().strip('"')

if not url.startswith("postgresql://postgres.") or "xxxx" in url:
    raise SystemExit("Esa no parece la direccion de tu proyecto. Debe empezar por postgresql://postgres.CODIGO")
if "[YOUR-PASSWORD]" not in url:
    raise SystemExit("No encuentro [YOUR-PASSWORD] en la direccion. Copiala de nuevo desde Supabase.")

clave = getpass.getpass("Contrasena de la base de datos (no se vera al escribir): ")
url = url.replace("[YOUR-PASSWORD]", quote(clave, safe=""))

os.makedirs(".streamlit", exist_ok=True)
with open(".streamlit/secrets.toml", "w", encoding="utf-8") as f:
    f.write(f'DATABASE_URL = "{url}"\n')
print("Guardado en .streamlit/secrets.toml")
