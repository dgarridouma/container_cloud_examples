# Despliegue en Azure Container Apps — Guía paso a paso

> **Contexto del ejemplo:** aplicación Flask que lee datos de Cosmos DB y los visualiza. El objetivo es mostrar a los alumnos cómo contenedorizar una app existente y desplegarla en ACA siguiendo buenas prácticas.

---

## Estructura de ficheros resultante

```
sensehat_aca/
├── app.py                  # Aplicación Flask refactorizada
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

## Buenas prácticas aplicadas

| Práctica | Dónde se aplica | Por qué |
|---|---|---|
| Secretos en variables de entorno | `app.py`, ACA secrets | La cadena de conexión nunca va en el código |
| Usuario no-root en el contenedor | `Dockerfile` | Reduce superficie de ataque |
| Gunicorn en lugar del servidor dev | `Dockerfile` CMD | El servidor de Flask no es apto para producción |
| Health-check endpoint `/health` | `app.py`, `Dockerfile` | ACA necesita saber si el contenedor está listo |
| `.dockerignore` | Raíz del proyecto | Imágenes más pequeñas y sin fugas de `.env` |
| Imagen `python:slim` | `Dockerfile` FROM | Menor tamaño = menor superficie de ataque |

---

## Prerrequisitos

```bash
# Verifica que tienes instalado:
az --version          # Azure CLI ≥ 2.57
docker --version      # Docker Desktop o Docker Engine
```

```bash
# Login en Azure
az login

# Instala la extensión de Container Apps si no la tienes
az extension add --name containerapp --upgrade
```

---

## Paso 1 — Variables de entorno (una sola vez)

Ajusta estos valores antes de ejecutar los comandos siguientes:

```bash
# ── Identificadores Azure ──────────────────────────────────────────────────
RESOURCE_GROUP="rg-cosmos-viewer"
LOCATION="westeurope"

# ── Nombre e imagen (común a ambas opciones) ───────────────────────────────
IMAGE_NAME="cosmos-viewer"
IMAGE_TAG="v1"

# ── Opción A: Azure Container Registry ────────────────────────────────────
ACR_NAME="acrcosmosviewer"                 # único en Azure, solo letras/números

# ── Opción B: Docker Hub ───────────────────────────────────────────────────
DOCKERHUB_USER="tu-usuario-dockerhub"

# ── Azure Container Apps ───────────────────────────────────────────────────
ACA_ENV="aca-env-demo"
ACA_APP="cosmos-viewer-app"

# ── Cosmos DB (copia el valor del Portal > tu cuenta > Keys) ───────────────
COSMOS_CONN_STRING="AccountEndpoint=https://...;AccountKey=...;"
COSMOS_DATABASE="mibd"
COSMOS_CONTAINER="micontenedor"
```

---

## Paso 2 — Infraestructura base

```bash
# Grupo de recursos
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Entorno de Container Apps (red compartida para todos los contenedores del ejemplo)
az containerapp env create \
  --name $ACA_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

> **Solo si usas la Opción A (ACR):** crea también el registro:
> ```bash
> az acr create \
>   --resource-group $RESOURCE_GROUP \
>   --name $ACR_NAME \
>   --sku Basic \
>   --admin-enabled true
> ```

---

## Paso 3 — Build y push de la imagen

### Opción A — Azure Container Registry

```bash
# Build en la nube (no necesitas Docker instalado). No funciona en todas las suscripciones.
az acr build \
  --registry $ACR_NAME \
  --image ${IMAGE_NAME}:${IMAGE_TAG} \
  .

# Alternativa: build en local + push
az acr login --name $ACR_NAME
docker build -t ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG} .
docker push   ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}
```

### Opción B — Docker Hub

```bash
docker login   # usa Access Token, no tu contraseña (ver Paso 4a)

docker build -t ${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} .
docker push   ${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}
```

---

## Paso 4 — Despliegue en Azure Container Apps

### 4a — Credenciales del registro

**Opción A — ACR:**
```bash
ACR_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASS=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)
```

**Opción B — Docker Hub:**  
Genera un **Access Token** (nunca uses tu contraseña directamente):  
Docker Hub → Account Settings → Personal access tokens → Generate new token

```bash
DOCKERHUB_TOKEN="tu-access-token"
```

### 4b — Crear la Container App

**Opción A — ACR:**
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

**Opción B — Docker Hub:**
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

> **Punto clave**  
> La cadena de conexión (`$COSMOS_CONN_STRING`) se registra como **secret** en ACA y se referencia con `secretref:`. Esto significa que:
> - No aparece en los logs ni en la configuración visible.
> - Se puede rotar sin reconstruir la imagen.
> - La imagen Docker no contiene ningún secreto.

---

## Paso 5 — Obtener la URL y verificar

```bash
APP_URL=$(az containerapp show \
  --name $ACA_APP \
  --resource-group $RESOURCE_GROUP \
  --query "properties.configuration.ingress.fqdn" -o tsv)

echo "URL de la app: https://$APP_URL"

# Verifica el health-check
curl https://$APP_URL/health
# Respuesta esperada: {"status": "ok"}

# Verifica los datos
curl https://$APP_URL/
```

---

## Paso 6 — Probar el escalado a cero (característica clave de ACA)

```bash
# Con --min-replicas 0, ACA apaga el contenedor cuando no hay tráfico.
# Para comprobarlo en clase:

# 1. Espera ~5 minutos sin hacer peticiones
# 2. Comprueba réplicas activas:
az containerapp show \
  --name $ACA_APP \
  --resource-group $RESOURCE_GROUP \
  --query "properties.template.scale" -o table

# 3. Haz una petición → ACA arranca el contenedor en segundos (cold start)
curl https://$APP_URL/
```

---

## Actualizar la aplicación (flujo de CI/CD simplificado)

```bash
# 1. Modifica el código
# 2. Rebuild con nuevo tag

IMAGE_TAG="v2"

# Opción A — ACR
az acr build --registry $ACR_NAME --image ${IMAGE_NAME}:${IMAGE_TAG} .

# Opción B — Docker Hub
docker build -t ${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} .
docker push   ${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}

# 3. Actualiza la Container App (zero-downtime rolling update)

# Opción A
az containerapp update \
  --name $ACA_APP \
  --resource-group $RESOURCE_GROUP \
  --image ${ACR_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}

# Opción B
az containerapp update \
  --name $ACA_APP \
  --resource-group $RESOURCE_GROUP \
  --image docker.io/${DOCKERHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}
```

---

## Desarrollo local con Docker

```bash
# Copia la plantilla y rellena tus valores reales
cp .env.example .env
# Edita .env con tu cadena de conexión real

# Arranca el contenedor localmente
docker build -t cosmos-viewer .
docker run --rm -p 8080:8080 --env-file .env cosmos-viewer

# Accede en: http://localhost:8080
```

---

## Limpieza de recursos

```bash
# Elimina TODO el grupo de recursos (ACR si la usaste + ACA + entorno)
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

---

## Diagrama de arquitectura

```
┌──────────────────────────────────────────────────────┐
│                   Azure                              │
│                                                      │
│  ┌─────────────────────┐    ┌────────────────────┐   │
│  │  Azure Container    │    │  Azure Container   │   │
│  │  Registry (ACR)  [A]│──┐ │  Apps (ACA)        │   │
│  └─────────────────────┘  ├▶│                    │   │
│                            │ │  Flask + Gunicorn  │   │
│  Docker Hub            [B]─┘ │  puerto 8080       │   │
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
          │ HTTPS (ingress externo)
          │
       Usuario / Alumno
```
