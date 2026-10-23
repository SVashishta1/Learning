# Example 2: Terraform drives Docker on your own computer.
# It creates a private network and N copies of a tiny web server,
# exactly like it would create servers in a cloud.

terraform {
  required_version = ">= 1.6"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker" # a community provider, maintained outside HashiCorp
      version = "~> 4.0"
    }
  }
}

# The provider block configures the plugin. Empty = use the local Docker
# (the socket unix:///var/run/docker.sock on Linux and Mac).
# On Windows with Docker Desktop, use:  host = "npipe:////.//pipe//docker_engine"
provider "docker" {}

variable "replicas" {
  description = "How many copies of the web server to run."
  type        = number
  default     = 2
}

variable "base_port" {
  description = "Port of the first copy on your computer. Copy 2 gets base_port + 1, and so on."
  type        = number
  default     = 8081
}

variable "message" {
  description = "What every copy answers."
  type        = string
  default     = "Hello from a container that Terraform created"
}

# A private Docker network for the copies (like a VPC subnet in the cloud).
resource "docker_network" "ai" {
  name = "tf-ai-net"
}

# Download the image once. hashicorp/http-echo is a tiny server that answers fixed text.
resource "docker_image" "echo" {
  name         = "hashicorp/http-echo:1.0"
  keep_locally = false # "terraform destroy" also removes the image
}

# count = N makes N containers from one block. count.index is 0, 1, 2...
resource "docker_container" "api" {
  count = var.replicas
  name  = "tf-ai-api-${count.index}"
  image = docker_image.echo.image_id

  # Arguments for the http-echo program inside the container.
  command = ["-listen=:5678", "-text=${var.message} (copy ${count.index})"]

  # Publish container port 5678 on your computer's port base_port + index.
  ports {
    internal = 5678
    external = var.base_port + count.index
  }

  networks_advanced {
    name = docker_network.ai.name
  }
}

output "urls" {
  description = "Open these in a browser or with curl."
  # A "for expression": build one URL per container.
  value = [for i in range(var.replicas) : "http://localhost:${var.base_port + i}"]
}
