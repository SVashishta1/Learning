# Example 1: Terraform with no cloud at all.
# It invents a random server name and writes a config file on YOUR disk.
# Same workflow as a real cloud: init -> plan -> apply -> destroy.

# The "terraform" block: settings for Terraform itself.
terraform {
  required_version = ">= 1.6" # refuse to run on an older Terraform

  # Plugins ("providers") this folder needs, and where to download them from.
  required_providers {
    local = {
      source  = "hashicorp/local" # registry.terraform.io/hashicorp/local
      version = "~> 2.5"          # any 2.x version from 2.5 up (not 3.0)
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# Inputs: values you can change without touching the code.
variable "project_name" {
  description = "Short name used in every file and label."
  type        = string
  default     = "ai-platform"
}

variable "environment" {
  description = "dev or prod."
  type        = string
  default     = "dev"

  # Refuse typos before anything is created.
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be \"dev\" or \"prod\"."
  }
}

# A resource = one thing Terraform creates and then looks after.
# "random_pet" makes a funny readable name, like "dev-clever-otter".
resource "random_pet" "server_name" {
  length = 2
  prefix = var.environment
}

# Locals: named values computed inside this folder (like variables in a program).
locals {
  # prod uses the strong model, dev the cheap one: ? : means "if ... then ... else ...".
  model = var.environment == "prod" ? "claude-opus-5-5" : "claude-haiku-5-5"

  config = {
    project     = var.project_name
    environment = var.environment
    server      = random_pet.server_name.id # uses the OTHER resource's result
    model       = local.model
  }
}

# Writes a JSON file on your disk. ${...} puts a value inside text.
resource "local_file" "app_config" {
  filename        = "${path.module}/output/${var.environment}-config.json"
  content         = jsonencode(local.config)
  file_permission = "0644" # owner can write, everyone can read
}

# Outputs: values printed after "apply" (and readable with "terraform output").
output "server_name" {
  value = random_pet.server_name.id
}

output "config_file" {
  value = local_file.app_config.filename
}
