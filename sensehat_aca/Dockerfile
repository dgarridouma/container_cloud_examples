# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Flask + Cosmos DB viewer para Azure Container Apps
# Buenas prácticas aplicadas:
#   · Imagen base slim (menor superficie de ataque)
#   · Usuario no-root
#   · Sin secretos en la imagen (se inyectan en tiempo de ejecución)
#   · Gunicorn como servidor WSGI de producción
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

# --- Metadatos ---
#LABEL maintainer="tu-email@ejemplo.com"
LABEL maintainer="dgm@uma.es"
LABEL description="Cosmos DB viewer — ejemplo ACA"

# --- Variables de build (no son secretos, sólo configuración) ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# --- Dependencias del sistema (mínimas) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# --- Dependencias Python ---
#     Se copian primero para aprovechar la caché de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Código de la aplicación ---
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# --- Usuario no-root (buena práctica de seguridad) ---
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

EXPOSE ${PORT}

# --- Healthcheck (ACA lo usa para saber si el contenedor está listo) ---
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# --- Gunicorn: servidor WSGI de producción ---
#   · 2 workers es un buen punto de partida para ACA con 0.5–1 vCPU
#   · Ajusta --workers según los recursos asignados en ACA
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "app:app"]
