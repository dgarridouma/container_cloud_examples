# Terraform with Docker on Azure

## Communication between containers

- **ACI**: containers must be in the same container group to communicate via `localhost`. If separated, they can communicate by exposing a public IP, but it is less straightforward and more expensive.
- **ACA**: containers from different apps communicate through the environment's internal network, so they do not need to be together. It is better to separate them so that each service has its own lifecycle, scaling and independent configuration (although it is not mandatory).

## Create a Service Principal for Terraform

```bash
az ad sp create-for-rbac --name "terraform-sp" --role Contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>
```

The output returns the credentials needed for Terraform:

```json
{
  "appId": "<CLIENT_ID>",
  "displayName": "terraform-sp",
  "password": "<CLIENT_SECRET>",
  "tenant": "<TENANT_ID>"
}
```

> Protect these credentials. Do not include them in the code or in version control.

## Run Terraform inside a Docker container

### Init (no credentials required)

```bash
docker run -it --rm -v %cd%:/workspace -w /workspace hashicorp/terraform:latest init
```

### Apply

```bash
docker run -it --rm -v %cd%:/workspace -w /workspace \
  -e ARM_CLIENT_ID="<CLIENT_ID>" \
  -e ARM_CLIENT_SECRET="<CLIENT_SECRET>" \
  -e ARM_SUBSCRIPTION_ID="<SUBSCRIPTION_ID>" \
  -e ARM_TENANT_ID="<TENANT_ID>" \
  hashicorp/terraform:latest apply
```

### Destroy

```bash
docker run -it --rm -v %cd%:/workspace -w /workspace \
  -e ARM_CLIENT_ID="<CLIENT_ID>" \
  -e ARM_CLIENT_SECRET="<CLIENT_SECRET>" \
  -e ARM_SUBSCRIPTION_ID="<SUBSCRIPTION_ID>" \
  -e ARM_TENANT_ID="<TENANT_ID>" \
  hashicorp/terraform:latest destroy
```

## Azure Container Apps provider registration

If ACA is being used for the first time in the subscription, the provider must be registered:

```bash
az provider register --namespace Microsoft.App

# Check registration status
az provider show --namespace Microsoft.App --query registrationState
```
