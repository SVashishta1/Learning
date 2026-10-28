variable "name" {
  description = "Prefix for every resource name"
  type        = string
  default     = "northwind-assistant"
}

variable "region" {
  description = "AWS region. EU customer with EU data residency -> an EU region (check Claude model availability there)"
  type        = string
  default     = "eu-central-1"
}

variable "azs" {
  description = "Two availability zones (separate data centres) in the region"
  type        = list(string)
  default     = ["eu-central-1a", "eu-central-1b"]
}

variable "vpc_cidr" {
  description = "The private address range of the VPC. Agree it with the customer's network team to avoid overlaps"
  type        = string
  default     = "10.42.0.0/16"
}

variable "corporate_cidr" {
  description = "The customer's internal network (reached over VPN or Direct Connect) allowed to call the app"
  type        = string
  default     = "10.0.0.0/8"
}

variable "interface_endpoints" {
  description = "AWS services the VM reaches PRIVATELY (no internet). Check the Bedrock docs for the endpoint name of the API your SDK client uses."
  type        = list(string)
  default     = ["bedrock-runtime", "secretsmanager", "logs", "ssm", "ssmmessages", "ec2messages", "ecr.api", "ecr.dkr"]
}

variable "bedrock_model_arns" {
  description = "Only these models may be called (least privilege). Copy the exact ARNs from the Bedrock console."
  type        = list(string)
  default     = ["arn:aws:bedrock:eu-central-1::foundation-model/anthropic.*"]
}

variable "ami_id" {
  description = "Machine image for the VM (the customer's hardened image, or Amazon Linux 2023)"
  type        = string
  default     = "ami-00000000000000000"
}

variable "image" {
  description = "The assistant's container image in the customer's private registry (ECR)"
  type        = string
  default     = "123456789012.dkr.ecr.eu-central-1.amazonaws.com/northwind/assistant:1.0.0"
}

variable "instance_type" {
  type    = string
  default = "t3.medium"
}
