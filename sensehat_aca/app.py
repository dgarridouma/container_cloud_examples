import os
from flask import Flask, render_template, Response
from azure.cosmos import CosmosClient

# ---------------------------------------------------------------------------
# Configuración — todas las credenciales vienen de variables de entorno,
# NUNCA hardcodeadas en el código.
# ---------------------------------------------------------------------------
CONNECTION_STRING = os.environ["COSMOS_CONNECTION_STRING"]
DATABASE_NAME     = os.environ.get("COSMOS_DATABASE",  "mibd")
CONTAINER_NAME    = os.environ.get("COSMOS_CONTAINER",  "micontenedor")

# ---------------------------------------------------------------------------
# Cliente Cosmos DB (se crea una sola vez al arrancar el contenedor)
# ---------------------------------------------------------------------------
client    = CosmosClient.from_connection_string(CONNECTION_STRING)
database  = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

# ---------------------------------------------------------------------------
# Aplicación Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)


@app.route("/")
def index():
    """Devuelve los 10 últimos registros como texto plano."""
    query = "SELECT * FROM c ORDER BY c._ts DESC OFFSET 0 LIMIT 10"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    lines = []
    for item in items:
        body = item.get("Body", {})
        lines.append(
            f"{body.get('when','')}  "
            f"{body.get('temperature','')}  "
            f"{body.get('pressure','')}  "
            f"{body.get('humidity','')}"
        )
    return Response("\n".join(lines), mimetype="text/plain")


@app.route("/list_jinja")
def list_jinja():
    """Muestra los 100 últimos registros con una plantilla Jinja2."""
    query = "SELECT * FROM c ORDER BY c._ts DESC OFFSET 0 LIMIT 100"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return render_template("db.html", readings=items)


@app.route("/list_jquery")
def list_jquery():
    """Muestra los 100 últimos registros con una plantilla jQuery."""
    query = "SELECT * FROM c ORDER BY c._ts DESC OFFSET 0 LIMIT 100"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return render_template("db_jquery.html", readings=items)


@app.route("/health")
def health():
    """Health-check endpoint requerido por ACA / load balancers."""
    return {"status": "ok"}, 200


# ---------------------------------------------------------------------------
# Punto de entrada local (en producción se usa gunicorn, ver Dockerfile)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
