module "basic_infra" {
  source = "./modules/basic-infra"

  environment         = var.environment
  resource_group_name = var.resource_group_name
  location            = var.location
  cost_center         = var.cost_center
  storage_accounts    = var.storage_accounts
  key_vaults          = var.key_vaults
}