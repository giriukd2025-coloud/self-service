variable "environment" {
  type = string
}

variable "subscription_id" {
  type      = string
  sensitive = true
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "cost_center" {
  type = string
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
    name                      = string
    soft_delete_retention_days = number
  }))
  default = []
}