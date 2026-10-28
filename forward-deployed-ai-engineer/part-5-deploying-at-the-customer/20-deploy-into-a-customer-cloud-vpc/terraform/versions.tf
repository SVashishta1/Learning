terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws" # the plugin that knows how to talk to AWS
      version = "~> 5.0"        # any 5.x version (not 6.0)
    }
  }
}

provider "aws" {
  region = var.region # every resource below is created in this region
  default_tags {      # these tags are added to EVERY resource: customers use them for cost reports
    tags = { project = var.name, owner = "fde-team", managed_by = "terraform" }
  }
}
