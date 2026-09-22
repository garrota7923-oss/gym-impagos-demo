import time
import streamlit as st
from db import q, clave_ok

st.set_page_config(page_title="Panel del club", page_icon="static/icono.svg", layout="wide")

# El socio entra con su enlace personal: solo ve sus reservas
if "t" in st.query_params:
    from reservas import vista_socio
    vista_socio(st.query_params["t"])
    st.stop()

from comun import estilo
import paginas
from editar import editar

st.logo("static/logo.svg", icon_image="static/icono.svg", size="large")

if "usuario" not in st.session_state:
    estilo()
    _, centro, _ = st.columns([1, 1.3, 1])
    with centro:
        st.image("static/icono.svg", width=64)
        st.title("Entra en tu panel")
        if st.session_state.pop("baja_ok", False):
            st.info("Tu negocio se ha dado de baja. Si fue un error, escribenos en los proximos 30 dias.")
        fallos = st.session_state.get("fallos", 0)
        with st.form("login"):
            email = st.text_input("Email")
            clave = st.text_input("Contrasena", type="password")
            if st.form_submit_button("Entrar", type="primary", width="stretch"):
                if fallos >= 5:
                    time.sleep(3)
                u = q("""SELECT u.* FROM usuario u JOIN negocio n ON n.id=u.negocio_id
                         WHERE u.email=%s AND u.activo AND n.activo""", (email.strip().lower(),))
                if len(u) and clave_ok(clave, u.iloc[0]["clave"]):
                    st.session_state["usuario"] = u.iloc[0].drop("clave").to_dict()
                    st.session_state["fallos"] = 0
                    st.rerun()
                st.session_state["fallos"] = fallos + 1
                st.error("El email o la contrasena no son correctos")
        st.caption("¿Has olvidado la contrasena? Escribenos y te la cambiamos.")
    st.stop()

usuario = st.session_state["usuario"]
with st.sidebar:
    st.caption(f"Sesion: {usuario['email']}")
    if st.button("Cerrar sesion", width="stretch"):
        del st.session_state["usuario"]
        st.rerun()

nav = st.navigation({
    "": [st.Page(paginas.inicio, title="Hoy", icon=":material/today:", url_path="hoy", default=True)],
    "Dia a dia": [
        st.Page(paginas.socios, title="Socios", icon=":material/group:", url_path="socios"),
        st.Page(paginas.nuevo, title="Apuntar", icon=":material/person_add:", url_path="apuntar"),
        st.Page(paginas.clases, title="Clases", icon=":material/event_available:", url_path="clases"),
        st.Page(paginas.cobros, title="Cobros", icon=":material/payments:", url_path="cobros"),
        st.Page(paginas.pruebas, title="Pruebas", icon=":material/waving_hand:", url_path="pruebas"),
    ],
    "Configuracion": [
        st.Page(editar, title="Editar datos", icon=":material/table_edit:", url_path="editar"),
        st.Page(paginas.ajustes, title="Ajustes", icon=":material/settings:", url_path="ajustes"),
    ],
})
nav.run()
