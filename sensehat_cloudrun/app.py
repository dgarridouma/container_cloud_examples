import os
from flask import Flask, render_template, Response
from google.cloud import bigquery

# ---------------------------------------------------------------------------
# Configuración — parámetros de BigQuery via variables de entorno.
# Las credenciales NO se gestionan aquí: en Cloud Run la cuenta de servicio
# adjunta al servicio se encarga automáticamente (ADC).
# ---------------------------------------------------------------------------
PROJECT_ID  = os.environ.get("GOOGLE_CLOUD_PROJECT")   # auto-detectado en Cloud Run
DATASET     = os.environ.get("BQ_DATASET",  "midataset")
TABLE       = os.environ.get("BQ_TABLE",    "mitabla")
LOCATION    = os.environ.get("BQ_LOCATION", "EU")

# ---------------------------------------------------------------------------
# Cliente BigQuery (se crea una sola vez al arrancar el contenedor)
# ---------------------------------------------------------------------------
client = bigquery.Client(project=PROJECT_ID)

# ---------------------------------------------------------------------------
# Aplicación Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)


def fetch_measurements(limit=None):
    query = f"SELECT * FROM `{DATASET}.{TABLE}` ORDER BY `when` DESC"
    if limit is not None:
        query += f" LIMIT {limit}"
    return client.query(query, location=LOCATION)


@app.route("/")
def list_plain():
    """Devuelve los 10 últimos registros como texto plano."""
    measurements = fetch_measurements(limit=10)
    lines = [
        f"{m['when']}  {m['temperature']}  {m['pressure']}  {m['humidity']}"
        for m in measurements
    ]
    return Response("\n".join(lines), mimetype="text/plain")


@app.route("/list_jinja")
def list_jinja():
    """Muestra los 100 últimos registros con una plantilla Jinja2."""
    measurements = fetch_measurements(limit=100)
    return render_template("db.html", readings=measurements)


@app.route("/list_jquery")
def list_jquery():
    """Muestra los 100 últimos registros con una plantilla jQuery."""
    measurements = fetch_measurements(limit=100)
    return render_template("db_jquery.html", readings=measurements)


@app.route("/health")
def health():
    """Health-check endpoint requerido por Cloud Run / load balancers."""
    return {"status": "ok"}, 200


# ---------------------------------------------------------------------------
# Punto de entrada local (en producción se usa gunicorn, ver Dockerfile)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
