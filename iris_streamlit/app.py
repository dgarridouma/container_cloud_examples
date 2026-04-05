import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.datasets import load_iris

st.set_page_config(page_title="Explorador Iris", page_icon="🌸", layout="wide")
st.title("🌸 Explorador de datos — Iris")
st.markdown("Visualización interactiva del dataset Iris.")

iris = load_iris()
df = pd.DataFrame(iris.data, columns=["Longitud sépalo", "Anchura sépalo", "Longitud pétalo", "Anchura pétalo"])
df["Especie"] = [iris.target_names[i] for i in iris.target]

st.sidebar.header("Filtros")
especies = st.sidebar.multiselect("Selecciona especies", options=df["Especie"].unique(), default=list(df["Especie"].unique()))
eje_x = st.sidebar.selectbox("Eje X", df.columns[:-1], index=0)
eje_y = st.sidebar.selectbox("Eje Y", df.columns[:-1], index=2)

df_filtrado = df[df["Especie"].isin(especies)]

col1, col2, col3 = st.columns(3)
col1.metric("Total muestras", len(df_filtrado))
col2.metric("Especies seleccionadas", len(especies))
col3.metric("Variables", 4)

st.divider()
col_izq, col_der = st.columns(2)
with col_izq:
    fig = px.scatter(df_filtrado, x=eje_x, y=eje_y, color="Especie",
                     color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig, use_container_width=True)
with col_der:
    fig2 = px.box(df_filtrado, x="Especie", y=eje_y, color="Especie",
                  color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Datos")
st.dataframe(df_filtrado, use_container_width=True)