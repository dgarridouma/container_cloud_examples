# Deployment on Google Cloud Run — Step-by-step guide

> **Example context:** Flask application that reads sensor data (temperature, pressure, humidity) captured with the SenseHat emulator on a Raspberry Pi and stored in BigQuery. The goal is to show how to containerize the app and deploy it to Cloud Run.

---

## Resulting file structure

```
sensehat_cloudrun/
├── app.py                  # Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile              # Production image
├── .dockerignore           # Excludes unnecessary files from the image
├── .env.example            # Environment variables template (IS uploaded to Git)
├── .env                    # Real local values                (NOT uploaded to Git)
└── templates/
    ├── db.html
    └── db_jquery.html
```

---

## How authentication works in GCP

One of the most important features of GCP is that client libraries (such as `google-cloud-bigquery`) never need you to pass credentials explicitly in the code. Instead they use **Application Default Credentials (ADC)**: a mechanism that automatically looks for the appropriate credentials depending on the environment where the code runs.

The flow is as follows:

- **Locally:** ADC uses your GCP user credentials, obtained with `gcloud auth application-default login`. They are stored in a JSON file on your machine and the library finds them automatically.
- **On Cloud Run:** ADC uses the **service account** attached to the service. GCP injects it automatically into the container's execution environment. No files, no environment variables with keys, nothing to manage.

The result is that `bigquery.Client()` works without any authentication arguments in both environments, and **the Docker image contains no credentials**. If access ever needs to be restricted or revoked, simply modify the service account permissions in IAM — without touching the code or rebuilding the image.

---

## Applied best practices

| Practice | Where it applies | Why |
|---|---|---|
| ADC instead of explicit keys | `app.py`, Cloud Run | No credentials ever in the code or the image |
| DB parameters in environment variables | `app.py`, Cloud Run | Dataset/table/location configurable without rebuilding |
| Non-root user in the container | `Dockerfile` | Reduces attack surface |
| Gunicorn instead of dev server | `Dockerfile` CMD | Flask's server is not suitable for production |
| Health-check endpoint `/health` | `app.py`, `Dockerfile` | Cloud Run uses it to know if the container is ready |
| `.dockerignore` with `*.json` | Project root | Prevents service account keys from being included in the image |
| `python:slim` image | `Dockerfile` FROM | Smaller size = smaller attack surface |

---

## Prerequisites

```bash
# Verify you have installed:
gcloud --version      # Google Cloud CLI
docker --version      # Docker Desktop or Docker Engine
```

```bash
# Login to GCP
gcloud auth login
gcloud auth application-default login   # credentials for local development

# Install the Cloud Run component if you don't have it
gcloud components install beta
```

---

## Step 1 — Variables (once only)

```bash
# ── GCP identifiers ────────────────────────────────────────────────────────
PROJECT_ID="tu-proyecto-gcp"
REGION="europe-west1"               # or the region where your BQ dataset is

# ── Image name (common to both registry options) ───────────────────────────
IMAGE_NAME="sensehat-cloudrun"
IMAGE_TAG="v1"

# ── Option A: Artifact Registry ───────────────────────────────────────────
AR_REPO="cloud-run-repo"            # repository name in Artifact Registry
AR_LOCATION="europe-west1"          # must match the region
AR_IMAGE="${AR_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"

# ── Option B: Docker Hub ──────────────────────────────────────────────────
DOCKERHUB_USER="tu-usuario-dockerhub"
DH_IMAGE="${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"

# ── BigQuery ──────────────────────────────────────────────────────────────
BQ_DATASET="midataset"
BQ_TABLE="mitabla"
BQ_LOCATION="EU"

# ── Cloud Run ─────────────────────────────────────────────────────────────
SERVICE_NAME="sensehat-viewer"
SERVICE_ACCOUNT="sensehat-cloudrun-sa"
```

---

## Step 2 — Project configuration

```bash
gcloud config set project $PROJECT_ID

# Enable the required APIs
gcloud services enable \
  run.googleapis.com \
  bigquery.googleapis.com \
  artifactregistry.googleapis.com   # only if using Option A
```

---

## Step 3 — Service account for Cloud Run

> This is where BigQuery access is granted to our Cloud Run service. Instead of managing keys or connection strings, we simply assign the necessary IAM roles to the service account that the container will use.

```bash
# Create the service account
gcloud iam service-accounts create $SERVICE_ACCOUNT \
  --display-name "Cloud Run - SenseHat Viewer"

# Grant read permissions on BigQuery
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member "serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member "serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/bigquery.jobUser"
```

---

## Step 4 — Build and push the image

### Option A — Artifact Registry

```bash
# Create the repository (once only)
gcloud artifacts repositories create $AR_REPO \
  --repository-format docker \
  --location $AR_LOCATION

# Configure Docker to authenticate with Artifact Registry
gcloud auth configure-docker ${AR_LOCATION}-docker.pkg.dev

# Build and push
docker build -t $AR_IMAGE .
docker push   $AR_IMAGE

# Alternative: cloud build with Cloud Build (no local Docker) ✅ recommended in class
gcloud builds submit --tag $AR_IMAGE .
```

### Option B — Docker Hub

```bash
docker login   # use an Access Token, not your password
               # Docker Hub → Account Settings → Personal access tokens

docker build -t $DH_IMAGE .
docker push   $DH_IMAGE
```
---

## Step 5 — Deploy to Cloud Run

### Option A — Artifact Registry

```bash
gcloud run deploy $SERVICE_NAME \
  --image $AR_IMAGE \
  --region $REGION \
  --platform managed \
  --service-account "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},BQ_DATASET=${BQ_DATASET},BQ_TABLE=${BQ_TABLE},BQ_LOCATION=${BQ_LOCATION}" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 3 \
  --memory 512Mi \
  --cpu 1 \
  --port 8080
```

### Option B — Docker Hub

```bash
DOCKERHUB_TOKEN="tu-access-token"

gcloud run deploy $SERVICE_NAME \
  --image $DH_IMAGE \
  --region $REGION \
  --platform managed \
  --service-account "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},BQ_DATASET=${BQ_DATASET},BQ_TABLE=${BQ_TABLE},BQ_LOCATION=${BQ_LOCATION}" \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 3 \
  --memory 512Mi \
  --cpu 1 \
  --port 8080
```

---

## Step 6 — Get the URL and verify

```bash
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format "value(status.url)")

echo "Service URL: $SERVICE_URL"

# Verify the health-check
curl $SERVICE_URL/health
# Expected response: {"status": "ok"}

# Verify the data
curl $SERVICE_URL/
```

---

## Step 7 — Test scale-to-zero

```bash
# With --min-instances 0, Cloud Run shuts down the container when there is no traffic.

# 1. Wait ~5 minutes without making any requests
# 2. Check the service status:
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format "value(status.conditions)"

# 3. Make a request → Cloud Run starts the container in seconds (cold start)
curl $SERVICE_URL/
```

---

## Local development with Docker

```bash
# 1. Make sure you have local credentials
gcloud auth application-default login

# 2. Copy the template and fill in your values
cp .env.example .env

# 3. Start the container mounting the ADC credentials from your machine
docker build -t sensehat-cloudrun .
docker run --rm -p 8080:8080 \
  --env-file .env \
  -v "$HOME/.config/gcloud/application_default_credentials.json:/tmp/adc.json:ro" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/adc.json \
  sensehat-cloudrun

# Alternatively, on Windows with CMD:
docker run --rm -p 8080:8080 --env-file .env -v "%APPDATA%\gcloud\application_default_credentials.json:/tmp/adc.json:ro" -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/adc.json sensehat-cloudrun

# Access at: http://localhost:8080
```

> Mounting the ADC file is only necessary locally. On Cloud Run it is not needed because the service account handles it automatically.

---

## Updating the application

```bash
# 1. Modify the code
# 2. Rebuild with a new tag
IMAGE_TAG="v2"

# Option A
AR_IMAGE="${AR_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"
gcloud builds submit --tag $AR_IMAGE .

# Option B
DH_IMAGE="${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
docker build -t $DH_IMAGE . && docker push $DH_IMAGE

# 3. Update the service (zero-downtime rolling update)
# Option A
gcloud run services update $SERVICE_NAME --image $AR_IMAGE --region $REGION

# Option B
gcloud run services update $SERVICE_NAME --image $DH_IMAGE --region $REGION
```

---

## Resource cleanup

```bash
# Delete the Cloud Run service
gcloud run services delete $SERVICE_NAME --region $REGION

# Delete the Artifact Registry repository (Option A only)
gcloud artifacts repositories delete $AR_REPO --location $AR_LOCATION

# Delete the service account
gcloud iam service-accounts delete \
  "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"
```

---

## Architecture diagram

```
                         ┌──────────────────────────────────────┐
                         │              GCP                     │
                         │                                      │
  Artifact Registry [A]──┤                                      │
  or Docker Hub     [B]─┤──▶┌──────────────────────┐          │
                         │   │  Cloud Run            │          │
                         │   │                       │          │
                         │   │  Flask + Gunicorn     │          │
                         │   │  port 8080            │          │
                         │   │                       │          │
                         │   │  Service Account      │          │
                         │   │  (automatic ADC)      │          │
                         │   └──────────┬────────────┘          │
                         │              │ ADC / no keys          │
                         │   ┌──────────▼────────────┐          │
                         │   │  BigQuery             │          │
                         │   │  midataset.mitabla    │          │
                         │   └───────────────────────┘          │
                         └──────────────────────────────────────┘
                                    ▲
                                    │ HTTPS
                                    │
                               User / Student
```
