# container_cloud_examples

Practical examples of container deployment on Azure and GCP. Includes containerized Python applications and Terraform configurations to automate infrastructure deployment.

---

## Repository Structure

```
container_cloud_examples/
├── iris_streamlit/              # Streamlit app with Iris dataset
├── iris_streamlit_fastapi/      # Streamlit frontend + FastAPI backend
├── penguins_streamlit/          # Streamlit app with penguins dataset
├── sensehat_aca/                # Flask app visualizing CosmosDB data on ACA
├── sensehat_cloudrun/           # Flask app visualizing BigQuery data on Cloud Run
├── terraform_azure_containers/  # Terraform for ACI and ACA on Azure
└── terraform_gcp_containers/    # Terraform for Cloud Run on GCP
```

---

## iris_streamlit

Interactive Streamlit app with the Iris dataset. Allows exploring the dataset variables with filters and interactive charts.

**Stack:** Python · Streamlit · Plotly · scikit-learn

**Run locally:**
```
pip install -r requirements.txt
streamlit run app.py
```

**Build image:**
```
docker build -t iris-streamlit:v1 .
docker run -p 8501:8501 iris-streamlit:v1
```

---

## iris_streamlit_fastapi

Two-container application: a Streamlit frontend that consumes a FastAPI API with a RandomForest classification model trained on the Iris dataset.

**Stack:** Python · Streamlit · FastAPI · scikit-learn · Docker Compose

```
iris_streamlit_fastapi/
├── api/
│   ├── main.py          # FastAPI API
│   ├── train_model.py   # Generates model.pkl
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py           # Streamlit app
│   ├── Dockerfile
│   └── requirements.txt
└── docker-compose.yml
```

**Prepare the model before building:**
```
cd api
pip install -r requirements.txt
python train_model.py
```

**Run with Docker Compose:**
```
docker compose up --build
```

The frontend is available at `http://localhost:8501`. Communication between containers uses Docker's internal network: the frontend calls the API at `http://iris-api:8000`.

---

## penguins_streamlit

Interactive Streamlit app with the penguins dataset. Allows exploring the dataset variables with filters and interactive charts.

**Stack:** Python · Streamlit · Plotly

**Run locally:**
```
pip install -r requirements.txt
streamlit run app.py
```

**Build image:**
```
docker build -t penguins-streamlit:v1 .
docker run -p 8501:8501 penguins-streamlit:v1
```

---

## sensehat_aca

Flask application that visualizes sensor data (temperature, pressure and humidity) stored in Cosmos DB. The data was captured in previous activities using the SenseHat emulator on a Raspberry Pi. Designed as an example of containerization and deployment on Azure Container Apps (ACA).

**Stack:** Python · Flask · Gunicorn · Azure Cosmos DB

```
sensehat_aca/
├── app.py               # Flask application
├── requirements.txt
├── Dockerfile           # Production image (non-root user, Gunicorn)
├── .env.example         # Environment variables template
└── templates/
    ├── db.html          # Jinja2 view
    └── db_jquery.html   # jQuery view
```

**Run locally:**
```
cp .env.example .env     # fill in with the real connection string
docker build -t sensehat-aca:v1 .
docker run --rm -p 8080:8080 --env-file .env sensehat-aca:v1
```

**Deploy to ACA:**  
See `README.md` in the example folder. Includes both registry options (Azure Container Registry and Docker Hub).

**Available routes:**

| Route | Description |
|---|---|
| `/` | Last 10 records in plain text |
| `/list_jinja` | Last 100 records with Jinja2 template |
| `/list_jquery` | Last 100 records with jQuery template |
| `/health` | Health-check for ACA |

---

## sensehat_cloudrun

Flask application that visualizes sensor data (temperature, pressure and humidity) stored in BigQuery. The data was captured in previous activities using the SenseHat emulator on a Raspberry Pi. Designed as an example of containerization and deployment on Google Cloud Run with authentication via Application Default Credentials (ADC).

**Stack:** Python · Flask · Gunicorn · Google BigQuery

```
sensehat_cloudrun/
├── app.py               # Flask application
├── requirements.txt
├── Dockerfile           # Production image (non-root user, Gunicorn)
├── .env.example         # Environment variables template
└── templates/
    ├── db.html          # Jinja2 view
    └── db_jquery.html   # jQuery view
```

**Run locally:**
```
cp .env.example .env     # fill in with project and dataset
gcloud auth application-default login
docker build -t sensehat-cloudrun:v1 .
docker run --rm -p 8080:8080 --env-file .env   -v "%APPDATA%\gcloud\application_default_credentials.json:/tmp/adc.json:ro"   -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/adc.json   sensehat-cloudrun:v1
```

**Deploy to Cloud Run:**  
See `README.md` in the example folder. Includes both registry options (Artifact Registry and Docker Hub).

**Available routes:**

| Route | Description |
|---|---|
| `/` | Last 10 records in plain text |
| `/list_jinja` | Last 100 records with Jinja2 template |
| `/list_jquery` | Last 100 records with jQuery template |
| `/health` | Health-check for Cloud Run |

---

## terraform_azure_containers

Terraform configurations to deploy containers on Azure. Covers two services:

- **ACI (Azure Container Instances):** simple single-container deployment with a public IP.
- **ACA (Azure Container Apps):** deployment with auto-scaling, HTTPS URL and internal communication between containers.

**Prerequisites:**
- Terraform installed
- Azure CLI installed and authenticated (`az login`)
- Image available in Azure Container Registry

**Usage:**
```
terraform init
terraform plan
terraform apply
```

---

## terraform_gcp_containers

Terraform configurations to deploy containers on GCP using Cloud Run.

**Prerequisites:**
- Terraform installed
- `gcloud` CLI installed and authenticated (`gcloud auth application-default login`)

**Usage:**
```
terraform init
terraform plan
terraform apply
```

---

## Notes

- The base images in some examples use `mcr.microsoft.com/devcontainers/python:3.11` instead of Docker Hub's `python:3.11-slim` to avoid connectivity issues with the Cloudflare registry.
