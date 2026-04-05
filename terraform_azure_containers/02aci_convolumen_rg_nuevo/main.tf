terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Crea el resource group que contendrá todos los recursos
resource "azurerm_resource_group" "rg" {
  name     = "grupocontainerapp"
  location = "norwayeast"
}

# Cuenta de almacenamiento en Azure para alojar el File Share
resource "azurerm_storage_account" "sa" {
  name                     = "sademoredis001"  # debe ser único globalmente
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"             # replicación local, la más barata
}

# File Share dentro de la storage account: carpeta compartida tipo NFS
resource "azurerm_storage_share" "redis_share" {
  name                 = "redis-data"
  storage_account_name = azurerm_storage_account.sa.name
  quota                = 1  # 1 GB
}

# Container Group: unidad de despliegue en ACI que agrupa varios contenedores
resource "azurerm_container_group" "app" {
  name                = "demo-group"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"

  # Contenedor Redis con volumen montado en /data para persistencia
  container {
    name   = "redis"
    image  = "redis:7"
    cpu    = 0.25
    memory = 0.5

    ports {
      port     = 6379
      protocol = "TCP"
    }

    # En ACI el volumen se define directamente en el contenedor (no hay paso intermedio)
    volume {
      name                 = "redis-volume"
      mount_path           = "/data"
      storage_account_name = azurerm_storage_account.sa.name
      storage_account_key  = azurerm_storage_account.sa.primary_access_key
      share_name           = azurerm_storage_share.redis_share.name
    }
  }

  # Contenedor de la app web
  # No necesita REDIS_HOST porque su valor por defecto es localhost
  container {
    name   = "web"
    image  = "dgarridouma/get-started:part2" # nombreregistro.azurecr.io/get-started:part2
    cpu    = 0.25
    memory = 0.5

    ports {
      port     = 80
      protocol = "TCP"
    }
  }

  # IP pública con DNS para acceder a la app desde internet
  ip_address_type = "Public"
  dns_name_label      = "get-started-${random_string.suffix.result}"

  # Credenciales de registro
  # Pueden ser de Docker Hub para evitar límites de rate limiting en IPs compartidas de Azure
  # O un registro de Azure Container Registries
  # Se pueden poner tantos bloques de este tipo como registros se usen
  image_registry_credential {
    server   = "index.docker.io" # nombreregistro.azurecr.io
    username = "YOURUSER"
    password = "YOURPASSWORD"
  }

  # Solo exponemos el puerto 80 al exterior; el 6379 queda interno
  exposed_port {
    port     = 80
    protocol = "TCP"
  }
}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# URL pública de la app web tras el despliegue
output "app_url" {
  value = "http://${azurerm_container_group.app.fqdn}"
}
