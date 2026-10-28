output "vpc_id" {
  value = aws_vpc.main.id
}

output "app_private_ip" {
  description = "Give this to the customer's network team for the internal load balancer"
  value       = aws_instance.app.private_ip
}

output "secret_name" {
  description = "Set its value once with: aws secretsmanager put-secret-value --secret-id <this> --secret-string ..."
  value       = aws_secretsmanager_secret.app.name
}

output "endpoint_services" {
  value = [for e in aws_vpc_endpoint.interface : e.service_name]
}
