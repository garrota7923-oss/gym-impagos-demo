import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Panel del club", layout="wide")
st.title("Panel del club de boxeo")
st.caption("Demo con datos ficticios")

df = pd.read_csv("reservas.csv", parse_dates=["fecha"])
AFORO = 14
HORAS = ["09:30","10:45","12:00","16:00","17:15","18:30","19:45","21:00"]
DIAS = ["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado"]

meses = sorted(df["fecha"].dt.to_period("M").astype(str).unique())
elegidos = st.multiselect("Meses", meses, default=meses)
d = df[df["fecha"].dt.to_period("M").astype(str).isin(elegidos)]
if d.empty:
    st.warning("Elige al menos un mes")
    st.stop()

hoy = df["fecha"].max()
ultima = df[df["tipo_reserva"] == "socio"].groupby("socio_id")["fecha"].max()
activos = (ultima >= hoy - pd.Timedelta(days=14)).sum()
riesgo = ultima[(ultima < hoy - pd.Timedelta(days=14)) & (ultima >= hoy - pd.Timedelta(days=45))]
pruebas = d[d["tipo_reserva"] == "prueba"]["socio_id"].unique()
convertidos = df[(df["socio_id"].isin(pruebas)) & (df["tipo_reserva"] == "socio")]["socio_id"].nunique()
clases = d.groupby(["fecha", "hora"]).size()
ocupacion = clases.mean() / AFORO

c1, c2, c3, c4 = st.columns(4)
c1.metric("Reservas", f"{len(d):,}".replace(",", "."))
c2.metric("Socios activos (14 dias)", int(activos))
c3.metric("Ocupacion media", f"{ocupacion:.0%}")
tasa = f" ({convertidos/len(pruebas):.0%})" if len(pruebas) else ""
c4.metric("Pruebas que se apuntan", f"{convertidos}/{len(pruebas)}{tasa}")

st.subheader("Personas por clase segun horario")
por_hora = clases.groupby(level="hora").mean().round(1).reset_index(name="media")
st.altair_chart(alt.Chart(por_hora).mark_bar().encode(
    x=alt.X("hora:N", sort=HORAS, title="Horario", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("media:Q", title="Personas por clase", scale=alt.Scale(domain=[0, AFORO])),
    tooltip=["hora", "media"]), width="stretch")

st.subheader("Ocupacion media por dia y hora")
tabla = (clases.reset_index(name="n")
         .assign(dia=lambda x: x["fecha"].dt.dayofweek.map(dict(enumerate(DIAS))))
         .pivot_table(index="dia", columns="hora", values="n", aggfunc="mean")
         .reindex(index=DIAS, columns=HORAS))
st.dataframe((tabla / AFORO).style.format("{:.0%}").background_gradient(cmap="RdYlGn", axis=None),
             width="stretch")

st.subheader("Reservas por semana")
semanal = (d.assign(semana=d["fecha"].dt.to_period("W").dt.start_time)
           .groupby("semana").agg(reservas=("socio_id", "size"), dias=("fecha", "nunique"))
           .reset_index())
semanal = semanal[semanal["dias"] == 6]
st.altair_chart(alt.Chart(semanal).mark_line(point=True).encode(
    x=alt.X("semana:T", title="Semana", axis=alt.Axis(format="%d %b")),
    y=alt.Y("reservas:Q", title="Reservas", scale=alt.Scale(zero=True)),
    tooltip=[alt.Tooltip("semana:T", format="%d/%m/%Y"), "reservas"]), width="stretch")

st.subheader(f"Socios que llevan mas de 2 semanas sin venir ({len(riesgo)})")
st.caption("Candidatos a un mensaje para recuperarlos antes de que se den de baja")
nombres = df.drop_duplicates("socio_id").set_index("socio_id")["nombre"]
tabla_riesgo = pd.DataFrame({
    "socio": nombres.reindex(riesgo.index).values,
    "ultima clase": riesgo.dt.date.values,
    "dias sin venir": (hoy - riesgo).dt.days.values,
}).sort_values("dias sin venir", ascending=False)
st.dataframe(tabla_riesgo, hide_index=True, width="stretch")
