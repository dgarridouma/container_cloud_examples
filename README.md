# container_cloud_examples

Ejemplos prácticos de despliegue de contenedores en Azure y GCP. Incluye aplicaciones Python containerizadas y configuraciones Terraform para automatizar el despliegue de infraestructura.

---

## Estructura del repositorio

```
container_cloud_examples/
├── iris_streamlit/              # App Streamlit con dataset Iris
├── iris_streamlit_fastapi/      # Frontend Streamlit + Backend FastAPI
├── penguins_streamlit/          # App Streamlit con dataset pingüinos
├── sensehat_aca/                # App Flask visualizando datos de CosmosDB en ACA
├── sensehat_cloudrun/           # App Flask visualizando datos de BigQuery en Cloud Run
├── terraform_azure_containers/  # Terraform para ACI y ACA en Azure
└── terraform_gcp_containers/    # Terraform para Cloud Run en GCP
```

---

## iris_streamlit

App Streamlit interactiva con el dataset Iris. Permite explorar las variables del dataset con filtros y gráficos interactivos.

**Stack:** Python · Streamlit · Plotly · scikit-learn

**Ejecutar en local:**
```
pip install -r requirements.txt
streamlit run app.py
```

**Construir imagen:**
```
docker build -t iris-streamlit:v1 .
docker run -p 8501:8501 iris-streamlit:v1
```

---

## iris_streamlit_fastapi

Aplicación de dos contenedores: un frontend Streamlit que consume una API FastAPI con un modelo de clasificación RandomForest entrenado sobre el dataset Iris.

**Stack:** Python · Streamlit · FastAPI · scikit-learn · Docker Compose

```
iris_streamlit_fastapi/
├── api/
│   ├── main.py          # API FastAPI
│   ├── train_model.py   # Genera model.pkl
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py           # App Streamlit
│   ├── Dockerfile
│   └── requirements.txt
└── docker-compose.yml
```

**Preparar el modelo antes de construir:**
```
cd api
pip install -r requirements.txt
python train_model.py
```

**Ejecutar con Docker Compose:**
```
docker compose up --build
```

El frontend queda disponible en `http://localhost:8501`. La comunicación entre contenedores usa la red interna de Docker: el frontend llama a la API en `http://iris-api:8000`.

---

## penguins_streamlit

App Streamlit interactiva con dataset de pingüinos. Permite explorar las variables del dataset con filtros y gráficos interactivos.

**Stack:** Python · Streamlit · Plotly

**Ejecutar en local:**
```
pip install -r requirements.txt
streamlit run app.py
```

**Construir imagen:**
```
docker build -t penguins-streamlit:v1 .
docker run -p 8501:8501 penguins-streamlit:v1
```

---

## sensehat_aca

Aplicación Flask que visualiza datos de sensores (temperatura, presión y humedad) almacenados en Cosmos DB. Los datos fueron capturados en actividades previas usando el emulador de SenseHat en una Raspberry Pi. Diseñada como ejemplo de contenedorización y despliegue en Azure Container Apps (ACA).

**Stack:** Python · Flask · Gunicorn · Azure Cosmos DB

```
sensehat_aca/
├── app.py               # Aplicación Flask
├── requirements.txt
├── Dockerfile           # Imagen de producción (usuario no-root, Gunicorn)
├── .env.example         # Plantilla de variables de entorno
└── templates/
    ├── db.html          # Vista Jinja2
    └── db_jquery.html   # Vista jQuery
```

**Ejecutar en local:**
```
cp .env.example .env     # rellenar con la cadena de conexión real
docker build -t sensehat-aca:v1 .
docker run --rm -p 8080:8080 --env-file .env sensehat-aca:v1
```

**Desplegar en ACA:**  
Ver `README.md` en la carpeta del ejemplo. Incluye las dos opciones de registro (Azure Container Registry y Docker Hub).

**Rutas disponibles:**

| Ruta | Descripción |
|---|---|
| `/` | Últimos 10 registros en texto plano |
| `/list_jinja` | Últimos 100 registros con plantilla Jinja2 |
| `/list_jquery` | Últimos 100 registros con plantilla jQuery |
| `/health` | Health-check para ACA |

---

## sensehat_cloudrun

Aplicación Flask que visualiza datos de sensores (temperatura, presión y humedad) almacenados en BigQuery. Los datos fueron capturados en actividades previas usando el emulador de SenseHat en una Raspberry Pi. Diseñada como ejemplo de contenedorización y despliegue en Google Cloud Run con autenticación mediante Application Default Credentials (ADC).

**Stack:** Python · Flask · Gunicorn · Google BigQuery

```
sensehat_cloudrun/
├── app.py               # Aplicación Flask
├── requirements.txt
├── Dockerfile           # Imagen de producción (usuario no-root, Gunicorn)
├── .env.example         # Plantilla de variables de entorno
└── templates/
    ├── db.html          # Vista Jinja2
    └── db_jquery.html   # Vista jQuery
```

**Ejecutar en local:**
```
cp .env.example .env     # rellenar con proyecto y dataset
gcloud auth application-default login
docker build -t sensehat-cloudrun:v1 .
docker run --rm -p 8080:8080 --env-file .env   -v "%APPDATA%\gcloud\application_default_credentials.json:/tmp/adc.json:ro"   -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/adc.json   sensehat-cloudrun:v1
```

**Desplegar en Cloud Run:**  
Ver `README.md` en la carpeta del ejemplo. Incluye las dos opciones de registro (Artifact Registry y Docker Hub).

**Rutas disponibles:**

| Ruta | Descripción |
|---|---|
| `/` | Últimos 10 registros en texto plano |
| `/list_jinja` | Últimos 100 registros con plantilla Jinja2 |
| `/list_jquery` | Últimos 100 registros con plantilla jQuery |
| `/health` | Health-check para Cloud Run |

---

## terraform_azure_containers

Configuraciones Terraform para desplegar contenedores en Azure. Cubre dos servicios:

- **ACI (Azure Container Instances):** despliegue simple de un contenedor con IP pública.
- **ACA (Azure Container Apps):** despliegue con escalado automático, URL HTTPS y comunicación interna entre contenedores.

**Prerrequisitos:**
- Terraform instalado
- Azure CLI instalado y autenticado (`az login`)
- Imagen disponible en Azure Container Registry

**Uso:**
```
terraform init
terraform plan
terraform apply
```

---

## terraform_gcp_containers

Configuraciones Terraform para desplegar contenedores en GCP usando Cloud Run.

**Prerrequisitos:**
- Terraform instalado
- `gcloud` CLI instalado y autenticado (`gcloud auth application-default login`)

**Uso:**
```
terraform init
terraform plan
terraform apply
```

---

## Notas

- Las imágenes base en algunos ejemplos usan `mcr.microsoft.com/devcontainers/python:3.11` en lugar de `python:3.11-slim` de Docker Hub para evitar problemas de conectividad con el registro de Cloudflare.
