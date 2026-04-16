# container_cloud_examples

Ejemplos prácticos de despliegue de contenedores en Azure y GCP. Incluye aplicaciones Python containerizadas y configuraciones Terraform para automatizar el despliegue de infraestructura.

---

## Estructura del repositorio

```
container_cloud_examples/
├── iris_streamlit/              # App Streamlit con dataset Iris
├── iris_streamlit_fastapi/      # Frontend Streamlit + Backend FastAPI
├── penguins_streamlit/          # App Streamlit con dataset pingüinos
├── sensehat_aca/                # App visualizando datos en CosmosDB
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

## sensehat_aca

Aplicación mostrando datos de CosmosDB usando plantillas Jinja2. Los datos han sido almacenados en actividades previas.

**Stack:** Python · Flask · CosmosDB

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


