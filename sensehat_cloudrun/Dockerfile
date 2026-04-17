# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Flask + BigQuery viewer para Google Cloud Run
# Buenas prácticas aplicadas:
#   · Imagen base slim (menor superficie de ataque)
#   · Usuario no-root
#   · Sin credenciales en la imagen (ADC las gestiona en tiempo de ejecución)
#   · Gunicorn como servidor WSGI de producción
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

LABEL maintainer="tu-email@ejemplo.com"
LABEL description="BigQuery viewer — ejemplo Cloud Run"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/
COPY static/ static/

RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "app:app"]
