variable "region" {
  description = "AWS region (the city), e.g. us-east-1 or eu-west-1."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used in resource names and tags."
  type        = string
  default     = "ai-platform"
}

variable "vpc_cidr" {
  description = "Address range of the whole VPC (the building)."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Address range of the public subnet (the ground floor)."
  type        = string
  default     = "10.0.0.0/24"
}

variable "instance_type" {
  description = "Size of the server. t3.micro is small and cheap."
  type        = string
  default     = "t3.micro"
}
