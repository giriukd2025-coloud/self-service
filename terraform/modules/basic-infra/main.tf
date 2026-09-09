# Approved basic-infra catalog. Self-service requests can only reference
# these resource types — expanding the catalog is a platform-team change
# here, not something a requester can do themselves.

variable "environment" { type = string }
variable "resource_group_name" { type = string }
variable "location" {
  type    = string
  default = "eastus"
}

variable "storage_accounts" {
  type = list(object({
    name = string
    tier = string
  }))
  default = []
}

variable "key_vaults" {
  type = list(object({
    name                     = string
    soft_delete_retention_days = number
  }))
  default = []
}

variable "cost_center" { type = string }

resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location
  tags = {
    costCenter = var.cost_center
    managedBy  = "self-service-platform"
  }
}

resource "azurerm_storage_account" "this" {
  for_each                 = { for s in var.storage_accounts : s.name => s }
  name                      = each.value.name
  resource_group_name       = azurerm_resource_group.this.name
  location                  = azurerm_resource_group.this.location
  account_tier              = split("_", each.value.tier)[0]
  account_replication_type  = split("_", each.value.tier)[1]

  # Security-gate guardrails baked into the module itself, not left to the requester
  public_network_access_enabled  = false
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true

  tags = { costCenter = var.cost_center }
}

resource "azurerm_key_vault" "this" {
  for_each                    = { for k in var.key_vaults : k.name => k }
  name                        = each.value.name
  resource_group_name         = azurerm_resource_group.this.name
  location                    = azurerm_resource_group.this.location
  sku_name                    = "standard"
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = each.value.soft_delete_retention_days
  public_network_access_enabled = false   # enforced regardless of request input

  tags = { costCenter = var.cost_center }
}

data "azurerm_client_config" "current" {}

output "resource_group_name" {
  value = azurerm_resource_group.this.name
}

output "storage_account_names" {
  value = [for account in azurerm_storage_account.this : account.name]
}

output "key_vault_names" {
  value = [for vault in azurerm_key_vault.this : vault.name]
}
