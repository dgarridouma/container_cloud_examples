# Despliegue en Google Cloud Run — Guía paso a paso

> **Contexto del ejemplo:** aplicación Flask que lee datos de sensores (temperatura, presión, humedad) capturados con el emulador de SenseHat en una Raspberry Pi y almacenados en BigQuery. El objetivo es mostrar cómo contenedorizar la app y desplegarla en Cloud Run.

---

## Estructura de ficheros resultante

```
sensehat_cloudrun/
├── app.py                  # Aplicación Flask
├── requirements.txt        # Dependencias Python
├── Dockerfile              # Imagen de producción
├── .dockerignore           # Excluye ficheros innecesarios de la imagen
├── .env.example            # Plantilla de variables de entorno (SÍ se sube a Git)
├── .env                    # Valores reales locales       (NO se sube a Git)
└── templates/
    ├── db.html
    └── db_jquery.html
```

---

## Cómo funciona la autenticación en GCP

Una de las características más importantes de GCP es que las bibliotecas cliente (como `google-cloud-bigquery`) nunca necesitan que les pases credenciales explícitamente en el código. En su lugar usan **Application Default Credentials (ADC)**: un mecanismo que busca automáticamente las credenciales adecuadas según el entorno donde se ejecuta el código.

El flujo es el siguiente:

- **En local:** ADC usa las credenciales de tu usuario de GCP, obtenidas con `gcloud auth application-default login`. Se almacenan en un fichero JSON en tu máquina y la biblioteca las encuentra sola.
- **En Cloud Run:** ADC usa la **cuenta de servicio** adjunta al servicio. GCP la inyecta automáticamente en el entorno de ejecución del contenedor. No hay ficheros, no hay variables de entorno con claves, no hay nada que gestionar.

El resultado es que `bigquery.Client()` funciona sin ningún argumento de autenticación en ambos entornos, y **la imagen Docker no contiene ninguna credencial**. Si alguna vez hay que restringir o revocar el acceso, basta con modificar los permisos de la cuenta de servicio en IAM — sin tocar el código ni reconstruir la imagen.

---

## Buenas prácticas aplicadas

| Práctica | Dónde se aplica | Por qué |
|---|---|---|
| ADC en lugar de claves explícitas | `app.py`, Cloud Run | Nunca hay credenciales en el código ni en la imagen |
| Parámetros de BD en variables de entorno | `app.py`, Cloud Run | Dataset/tabla/location configurables sin reconstruir |
| Usuario no-root en el contenedor | `Dockerfile` | Reduce superficie de ataque |
| Gunicorn en lugar del servidor dev | `Dockerfile` CMD | El servidor de Flask no es apto para producción |
| Health-check endpoint `/health` | `app.py`, `Dockerfile` | Cloud Run lo usa para saber si el contenedor está listo |
| `.dockerignore` con `*.json` | Raíz del proyecto | Evita incluir claves de cuenta de servicio en la imagen |
| Imagen `python:slim` | `Dockerfile` FROM | Menor tamaño = menor superficie de ataque |

---

## Prerrequisitos

```bash
# Verifica que tienes instalado:
gcloud --version      # Google Cloud CLI
docker --version      # Docker Desktop o Docker Engine
```

```bash
# Login en GCP
gcloud auth login
gcloud auth application-default login   # credenciales para desarrollo local

# Instala el componente de Cloud Run si no lo tienes
gcloud components install beta
```

---

## Paso 1 — Variables (una sola vez)

```bash
# ── Identificadores GCP ────────────────────────────────────────────────────
PROJECT_ID="tu-proyecto-gcp"
REGION="europe-west1"               # o la región donde esté tu dataset de BQ

# ── Nombre e imagen (común a ambas opciones de registro) ──────────────────
IMAGE_NAME="sensehat-cloudrun"
IMAGE_TAG="v1"

# ── Opción A: Artifact Registry ───────────────────────────────────────────
AR_REPO="cloud-run-repo"            # nombre del repositorio en Artifact Registry
AR_LOCATION="europe-west1"          # debe coincidir con la región
AR_IMAGE="${AR_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"

# ── Opción B: Docker Hub ──────────────────────────────────────────────────
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

## Paso 2 — Configuración del proyecto

```bash
gcloud config set project $PROJECT_ID

# Habilitar las APIs necesarias
gcloud services enable \
  run.googleapis.com \
  bigquery.googleapis.com \
  artifactregistry.googleapis.com   # solo si usas Opción A
```

---

## Paso 3 — Cuenta de servicio para Cloud Run

> Aquí es donde se concede el acceso a BigQuery a nuestro servicio de Cloud Run. En lugar de gestionar claves o cadenas de conexión, simplemente asignamos los roles necesarios en IAM a la cuenta de servicio que usará el contenedor.

```bash
# Crear la cuenta de servicio
gcloud iam service-accounts create $SERVICE_ACCOUNT \
  --display-name "Cloud Run - SenseHat Viewer"

# Conceder permisos de lectura sobre BigQuery
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member "serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member "serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/bigquery.jobUser"
```

---

## Paso 4 — Build y push de la imagen

### Opción A — Artifact Registry

```bash
# Crear el repositorio (una sola vez)
gcloud artifacts repositories create $AR_REPO \
  --repository-format docker \
  --location $AR_LOCATION

# Configurar Docker para autenticarse con Artifact Registry
gcloud auth configure-docker ${AR_LOCATION}-docker.pkg.dev

# Build y push
docker build -t $AR_IMAGE .
docker push   $AR_IMAGE

# Alternativa: build en la nube con Cloud Build (sin Docker local) ✅ recomendada en clase
gcloud builds submit --tag $AR_IMAGE .
```

### Opción B — Docker Hub

```bash
docker login   # usa Access Token, no tu contraseña
               # Docker Hub → Account Settings → Personal access tokens

docker build -t $DH_IMAGE .
docker push   $DH_IMAGE
```
---

## Paso 5 — Despliegue en Cloud Run

### Opción A — Artifact Registry

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

### Opción B — Docker Hub

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

## Paso 6 — Obtener la URL y verificar

```bash
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format "value(status.url)")

echo "URL del servicio: $SERVICE_URL"

# Verifica el health-check
curl $SERVICE_URL/health
# Respuesta esperada: {"status": "ok"}

# Verifica los datos
curl $SERVICE_URL/
```

---

## Paso 7 — Probar el escalado a cero

```bash
# Con --min-instances 0, Cloud Run apaga el contenedor cuando no hay tráfico.

# 1. Espera ~5 minutos sin hacer peticiones
# 2. Comprueba el estado del servicio:
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format "value(status.conditions)"

# 3. Haz una petición → Cloud Run arranca el contenedor en segundos (cold start)
curl $SERVICE_URL/
```

---

## Desarrollo local con Docker

```bash
# 1. Asegúrate de tener credenciales locales
gcloud auth application-default login

# 2. Copia la plantilla y rellena tus valores
cp .env.example .env

# 3. Arranca el contenedor montando las credenciales ADC de tu máquina
docker build -t sensehat-cloudrun .
docker run --rm -p 8080:8080 \
  --env-file .env \
  -v "$HOME/.config/gcloud/application_default_credentials.json:/tmp/adc.json:ro" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/adc.json \
  sensehat-cloudrun

# Alternativamente, en Windows con CMD sería:
docker run --rm -p 8080:8080 --env-file .env -v "%APPDATA%\gcloud\application_default_credentials.json:/tmp/adc.json:ro" -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/adc.json sensehat-cloudrun

# Accede en: http://localhost:8080
```

> El montaje del fichero ADC es necesario solo en local. En Cloud Run no hace falta porque la cuenta de servicio lo gestiona automáticamente.

---

## Actualizar la aplicación

```bash
# 1. Modifica el código
# 2. Rebuild con nuevo tag
IMAGE_TAG="v2"

# Opción A
AR_IMAGE="${AR_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"
gcloud builds submit --tag $AR_IMAGE .

# Opción B
DH_IMAGE="${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
docker build -t $DH_IMAGE . && docker push $DH_IMAGE

# 3. Actualiza el servicio (zero-downtime rolling update)
# Opción A
gcloud run services update $SERVICE_NAME --image $AR_IMAGE --region $REGION

# Opción B
gcloud run services update $SERVICE_NAME --image $DH_IMAGE --region $REGION
```

---

## Limpieza de recursos

```bash
# Eliminar el servicio de Cloud Run
gcloud run services delete $SERVICE_NAME --region $REGION

# Eliminar el repositorio de Artifact Registry (solo Opción A)
gcloud artifacts repositories delete $AR_REPO --location $AR_LOCATION

# Eliminar la cuenta de servicio
gcloud iam service-accounts delete \
  "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"
```

---

## Diagrama de arquitectura

```
                         ┌──────────────────────────────────────┐
                         │              GCP                     │
                         │                                      │
  Artifact Registry [A]──┤                                      │
  o Docker Hub       [B]─┤──▶┌──────────────────────┐          │
                         │   │  Cloud Run            │          │
                         │   │                       │          │
                         │   │  Flask + Gunicorn     │          │
                         │   │  puerto 8080          │          │
                         │   │                       │          │
                         │   │  Service Account      │          │
                         │   │  (ADC automático)     │          │
                         │   └──────────┬────────────┘          │
                         │              │ ADC / sin claves       │
                         │   ┌──────────▼────────────┐          │
                         │   │  BigQuery             │          │
                         │   │  midataset.mitabla    │          │
                         │   └───────────────────────┘          │
                         └──────────────────────────────────────┘
                                    ▲
                                    │ HTTPS
                                    │
                               Usuario / Alumno
```
