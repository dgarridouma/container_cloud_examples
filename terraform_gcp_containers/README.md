# Terraform with Docker on GCP (Cloud Run)

## Variables

Replace `<PROJECT_ID>` with your GCP project ID in all commands.

## Create a Service Account for Terraform

```bash
# Create the service account that Terraform will use to authenticate
gcloud iam service-accounts create terraform-sa --display-name "Terraform"

# Assign the Editor role so it can create and manage resources
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:terraform-sa@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/editor"

# Assign the IAM Security Admin role to be able to manage permissions
# (required to make the Cloud Run service publicly accessible)
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:terraform-sa@<PROJECT_ID>.iam.gserviceaccount.com" \
  --role="roles/iam.securityAdmin"

# Download the service account credentials to a JSON file
# This file will be passed to the Terraform container
gcloud iam service-accounts keys create credentials.json \
  --iam-account=terraform-sa@<PROJECT_ID>.iam.gserviceaccount.com
```

> Protect `credentials.json`. Do not include it in version control (add it to `.gitignore`).

## Enable required APIs

Terraform needs the Cloud Resource Manager API to manage IAM permissions in GCP.
If it is not enabled, `apply` will fail with a 403 error.

```bash
gcloud services enable cloudresourcemanager.googleapis.com --project=<PROJECT_ID>
```

## Run Terraform inside a Docker container

The `credentials.json` file must be in the same folder as `main.tf`.

### Init (no credentials required)

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
