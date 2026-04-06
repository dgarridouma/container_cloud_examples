import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns

st.set_page_config(page_title="Explorador Pingüinos", page_icon="🐧", layout="wide")
st.title("🐧 Explorador de datos — Pingüinos de Palmer")
st.markdown("Dataset de 344 pingüinos de tres especies del archipiélago Palmer (Antártida).")

df = sns.load_dataset("penguins").dropna()

st.sidebar.header("Filtros")
especies = st.sidebar.multiselect("Especie", options=df["species"].unique(), default=list(df["species"].unique()))
islas    = st.sidebar.multiselect("Isla",    options=df["island"].unique(),  default=list(df["island"].unique()))
sexo     = st.sidebar.multiselect("Sexo",    options=df["sex"].unique(),     default=list(df["sex"].unique()))
eje_x = st.sidebar.selectbox("Eje X", ["bill_length_mm","bill_depth_mm","flipper_length_mm","body_mass_g"], index=0)
eje_y = st.sidebar.selectbox("Eje Y", ["bill_length_mm","bill_depth_mm","flipper_length_mm","body_mass_g"], index=2)

df_f = df[df["species"].isin(especies) & df["island"].isin(islas) & df["sex"].isin(sexo)]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Pingüinos", len(df_f))
col2.metric("Especies", df_f["species"].nunique())
col3.metric("Islas", df_f["island"].nunique())
col4.metric("Peso medio (g)", f"{df_f['body_mass_g'].mean():.0f}")

st.divider()
col_izq, col_der = st.columns(2)
with col_izq:
    fig = px.scatter(df_f, x=eje_x, y=eje_y, color="species", symbol="sex",
                     hover_data=["island"], color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig, use_container_width=True)
with col_der:
    fig2 = px.violin(df_f, x="species", y="body_mass_g", color="species", box=True,
                     color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig2, use_container_width=True)

fig3 = px.histogram(df_f, x="island", color="species", barmode="group",
                    color_discrete_sequence=px.colors.qualitative.Set2)
st.plotly_chart(fig3, use_container_width=True)
st.dataframe(df_f, use_container_width=True)