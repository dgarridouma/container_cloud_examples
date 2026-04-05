# Terraform con Docker en GCP (Cloud Run)

## Variables

Sustituye `<PROJECT_ID>` por el ID de tu proyecto GCP en todos los comandos.

## Crear Service Account para Terraform

```bash
# Crea la service account que usará Terraform para autenticarse
gcloud iam service-accounts create terraform-sa --display-name "Terraform"

# Asigna el rol Editor para que pueda crear y gestionar recursos
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:terraform-sa@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/editor"

# Asigna el rol de administrador de seguridad IAM para poder gestionar permisos
# (necesario para hacer el servicio Cloud Run accesible públicamente)
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:terraform-sa@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/iam.securityAdmin"

# Descarga las credenciales de la service account en un fichero JSON
# Este fichero se pasará al contenedor de Terraform
gcloud iam service-accounts keys create credentials.json \
  --iam-account=terraform-sa@<PROJECT_ID>.iam.gserviceaccount.com
```

> Protege `credentials.json`. No lo incluyas en el control de versiones (añádelo al `.gitignore`).

## Habilitar APIs necesarias

Terraform necesita la API de Cloud Resource Manager para gestionar permisos IAM en GCP.
Si no está habilitada, el `apply` fallará con un error 403.

```bash
gcloud services enable cloudresourcemanager.googleapis.com --project=<PROJECT_ID>
```

## Ejecutar Terraform dentro de un contenedor Docker

El fichero `credentials.json` debe estar en la misma carpeta que el `main.tf`.

### Init (no requiere credenciales)

```bash
docker run -it --rm -v %cd%:/workspace -w /workspace hashicorp/terraform:latest init
```

### Apply

```bash
docker run -it --rm -v %cd%:/workspace -w /workspace \
  -e GOOGLE_APPLICATION_CREDENTIALS=/workspace/credentials.json \
  hashicorp/terraform:latest apply
```

### Destroy

```bash
docker run -it --rm -v %cd%:/workspace -w /workspace \
  -e GOOGLE_APPLICATION_CREDENTIALS=/workspace/credentials.json \
  hashicorp/terraform:latest destroy
```
