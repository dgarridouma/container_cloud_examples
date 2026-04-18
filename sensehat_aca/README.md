# Deployment on Azure Container Apps — Step-by-step guide

> **Example context:** Flask application that reads data from Cosmos DB and visualizes it. The goal is to show students how to containerize an existing app and deploy it to ACA following best practices.

---

## Resulting file structure

```
sensehat_aca/
├── app.py                  # Refactored Flask application
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

## Applied best practices

| Practice | Where it applies | Why |
|---|---|---|
| Secrets in environment variables | `app.py`, ACA secrets | The connection string never goes in the code |
| Non-root user in the container | `Dockerfile` | Reduces attack surface |
| Gunicorn instead of dev server | `Dockerfile` CMD | Flask's server is not suitable for production |
| Health-check endpoint `/health` | `app.py`, `Dockerfile` | ACA needs to know if the container is ready |
| `.dockerignore` | Project root | Smaller images and no `.env` leaks |
| `python:slim` image | `Dockerfile` FROM | Smaller size = smaller attack surface |

---

## Prerequisites

```bash
# Verify you have installed:
az --version          # Azure CLI ≥ 2.57
docker --version      # Docker Desktop or Docker Engine
```

```bash
# Login to Azure
az login

# Install the Container Apps extension if you don't have it
az extension add --name containerapp --upgrade
```

---

## Step 1 — Environment variables (once only)

Adjust these values before running the following commands:

```bash
# ── Azure identifiers ──────────────────────────────────────────────────────
RESOURCE_GROUP="rg-cosmos-viewer"
LOCATION="westeurope"

# ── Image name (common to both options) ───────────────────────────────────
IMAGE_NAME="cosmos-viewer"
IMAGE_TAG="v1"

# ── Option A: Azure Container Registry ────────────────────────────────────
ACR_NAME="acrcosmosviewer"                 # unique in Azure, letters/numbers only

# ── Option B: Docker Hub ───────────────────────────────────────────────────
DOCKERHUB_USER="tu-usuario-dockerhub"

# ── Azure Container Apps ───────────────────────────────────────────────────
ACA_ENV="aca-env-demo"
ACA_APP="cosmos-viewer-app"

# ── Cosmos DB (copy the value from Portal > your account > Keys) ───────────
COSMOS_CONN_STRING="AccountEndpoint=https://...;AccountKey=...;"
COSMOS_DATABASE="mibd"
COSMOS_CONTAINER="micontenedor"
```

---

## Step 2 — Base infrastructure

```bash
# Resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Container Apps environment (shared network for all containers in the example)
az containerapp env create \
  --name $ACA_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

> **Only if you use Option A (ACR):** also create the registry:
> ```bash
> az acr create \
>   --resource-group $RESOURCE_GROUP \
>   --name $ACR_NAME \
>   --sku Basic \
>   --admin-enabled true
> ```

---

## Step 3 — Build and push the image

### Option A — Azure Container Registry

```bash
# Cloud build (Docker not required locally). Does not work on all subscriptions.
az acr build \
  --registry $ACR_NAME \
  --image ${IMAGE_NAME}:${IMAGE_TAG} \
  .

# Alternative: local build + push
az acr login --name $ACR_NAME
docker build -t ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG} .
docker push   ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}
```

### Option B — Docker Hub

```bash
docker login   # use an Access Token, not your password (see Step 4a)

docker build -t ${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} .
docker push   ${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}
```

---

## Step 4 — Deploy to Azure Container Apps

### 4a — Registry credentials

**Option A — ACR:**
```bash
ACR_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASS=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)
```

**Option B — Docker Hub:**  
Generate an **Access Token** (never use your password directly):  
Docker Hub → Account Settings → Personal access tokens → Generate new token

```bash
DOCKERHUB_TOKEN="tu-access-token"
```

### 4b — Create the Container App

**Option A — ACR:**
```bash
az containerapp create \
  --name $ACA_APP \
  --resource-group $RESOURCE_GROUP \
  --environment $ACA_ENV \
  --image ${ACR_SERVER}/${IMAGE_NAME}:${IMAGE_TAG} \
  --registry-server $ACR_SERVER \
  --registry-username $ACR_USER \
  --registry-password $ACR_PASS \
  --target-port 8080 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1Gi \
  --secrets cosmos-conn-string="$COSMOS_CONN_STRING" \
  --env-vars \
      COSMOS_CONNECTION_STRING=secretref:cosmos-conn-string \
      COSMOS_DATABASE=$COSMOS_DATABASE \
      COSMOS_CONTAINER=$COSMOS_CONTAINER
```

**Option B — Docker Hub:**
```bash
az containerapp create \
  --name $ACA_APP \
  --resource-group $RESOURCE_GROUP \
  --environment $ACA_ENV \
  --image docker.io/${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} \
  --registry-server docker.io \
  --registry-username $DOCKERHUB_USER \
  --registry-password $DOCKERHUB_TOKEN \
  --target-port 8080 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1Gi \
  --secrets cosmos-conn-string="$COSMOS_CONN_STRING" \
  --env-vars \
      COSMOS_CONNECTION_STRING=secretref:cosmos-conn-string \
      COSMOS_DATABASE=$COSMOS_DATABASE \
      COSMOS_CONTAINER=$COSMOS_CONTAINER
```

> **Key point**  
> The connection string (`$COSMOS_CONN_STRING`) is registered as a **secret** in ACA and referenced with `secretref:`. This means:
> - It does not appear in logs or visible configuration.
> - It can be rotated without rebuilding the image.
> - The Docker image contains no secrets.

---

## Step 5 — Get the URL and verify

```bash
APP_URL=$(az containerapp show \
  --name $ACA_APP \
  --resource-group $RESOURCE_GROUP \
  --query "properties.configuration.ingress.fqdn" -o tsv)

echo "App URL: https://$APP_URL"

# Verify the health-check
curl https://$APP_URL/health
# Expected response: {"status": "ok"}

# Verify the data
curl https://$APP_URL/
```

---

## Step 6 — Test scale-to-zero (key ACA feature)

```bash
# With --min-replicas 0, ACA shuts down the container when there is no traffic.
# To verify this in class:

# 1. Wait ~5 minutes without making any requests
# 2. Check active replicas:
az containerapp show \
  --name $ACA_APP \
  --resource-group $RESOURCE_GROUP \
  --query "properties.template.scale" -o table

# 3. Make a request → ACA starts the container in seconds (cold start)
curl https://$APP_URL/
```

---

## Updating the application (simplified CI/CD flow)

```bash
# 1. Modify the code
# 2. Rebuild with a new tag

IMAGE_TAG="v2"

# Option A — ACR
az acr build --registry $ACR_NAME --image ${IMAGE_NAME}:${IMAGE_TAG} .

# Option B — Docker Hub
docker build -t ${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} .
docker push   ${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}

# 3. Update the Container App (zero-downtime rolling update)

# Option A
az containerapp update \
  --name $ACA_APP \
  --resource-group $RESOURCE_GROUP \
  --image ${ACR_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}

# Option B
az containerapp update \
  --name $ACA_APP \
  --resource-group $RESOURCE_GROUP \
  --image docker.io/${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}
```

---

## Local development with Docker

```bash
# Copy the template and fill in your real values
cp .env.example .env
# Edit .env with your real connection string

# Start the container locally
docker build -t cosmos-viewer .
docker run --rm -p 8080:8080 --env-file .env cosmos-viewer

# Access at: http://localhost:8080
```

---

## Resource cleanup

```bash
# Delete the ENTIRE resource group (ACR if used + ACA + environment)
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

---

## Architecture diagram

```
┌──────────────────────────────────────────────────────┐
│                   Azure                              │
│                                                      │
│  ┌─────────────────────┐    ┌────────────────────┐   │
│  │  Azure Container    │    │  Azure Container   │   │
│  │  Registry (ACR)  [A]│──┐ │  Apps (ACA)        │   │
│  └─────────────────────┘  ├▶│                    │   │
│                            │ │  Flask + Gunicorn  │   │
│  Docker Hub            [B]─┘ │  port 8080         │   │
│  usuario/cosmos-viewer   │   │                    │   │
│                              │  secrets:          │   │
│                              │  COSMOS_CONN_STR   │   │
│                              └────────┬───────────┘   │
│                                       │               │
│                              ┌────────▼───────────┐   │
│                              │   Cosmos DB        │   │
│                              │   mibd/micontenedor│   │
│                              └────────────────────┘   │
└──────────────────────────────────────────────────────┘
          ▲
          │ HTTPS (external ingress)
          │
       User / Student
```
