import streamlit as st
import requests, os

st.set_page_config(page_title="Predictor Iris", page_icon="🌸", layout="centered")
st.title("🌸 Predictor de especies — Iris")

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.subheader("Medidas de la flor (cm)")
col1, col2 = st.columns(2)
with col1:
    sepal_length = st.slider("Longitud sépalo", 4.0, 8.0, 5.5, 0.1)
    sepal_width  = st.slider("Anchura sépalo",  2.0, 4.5, 3.0, 0.1)
with col2:
    petal_length = st.slider("Longitud pétalo", 1.0, 7.0, 4.0, 0.1)
    petal_width  = st.slider("Anchura pétalo",  0.1, 2.5, 1.0, 0.1)

if st.button("Predecir", type="primary"):
    try:
        r = requests.post(f"{API_URL}/predecir",
                          json={"features": [sepal_length, sepal_width, petal_length, petal_width]},
                          timeout=5)
        res = r.json()
        emoji = {"setosa": "🟢", "versicolor": "🟡", "virginica": "🔵"}.get(res["especie"], "⚪")
        st.success(f"{emoji} Especie predicha: **{res['especie'].capitalize()}**")
        st.subheader("Probabilidades")
        for nombre, prob in res["probabilidades"].items():
            st.progress(prob, text=f"{nombre}: {prob:.1%}")
    except requests.exceptions.ConnectionError:
        st.error(f"No se puede conectar con la API en {API_URL}")

with st.expander("ℹ️ Arquitectura"):
    st.markdown(f"""
    Esta app usa **dos contenedores**:
    - **Frontend**: esta interfaz Streamlit
    - **Backend**: API FastAPI con modelo RandomForest (Iris)

    La Streamlit llama a: `{API_URL}/predecir`
    """)