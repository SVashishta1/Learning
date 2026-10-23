# READ-ONLY EXAMPLE: running "terraform apply" here creates real AWS resources
# that cost money (small, but real). Read it, run "terraform validate", and only
# apply it in your own account with a billing alarm set (lesson 24).

terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Where Terraform keeps its memory (the "state"). By default it is the local file
  # terraform.tfstate. Teams keep it in a shared, locked place instead, such as an S3 bucket:
  #
  # backend "s3" {
  #   bucket       = "my-company-terraform-state" # create this bucket by hand first
  #   key          = "ai-platform/dev.tfstate"    # the file name inside the bucket
  #   region       = "us-east-1"
  #   use_lockfile = true                         # stops two people applying at once
  # }
}

# The AWS provider. Credentials come from your environment (aws configure / SSO / CloudShell),
# NEVER from this file.
provider "aws" {
  region = var.region

  # Every resource gets these labels automatically: handy for finding and billing.
  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
    }
  }
}
