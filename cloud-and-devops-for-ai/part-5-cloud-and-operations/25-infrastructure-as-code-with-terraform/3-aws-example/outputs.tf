output "api_url" {
  description = "Open this about 2 minutes after apply (the server needs time to install Docker)."
  value       = "http://${aws_instance.api.public_ip}"
}

output "docs_bucket" {
  value = aws_s3_bucket.docs.bucket
}

output "instance_id" {
  description = "Use it with: aws ssm start-session --target <instance_id>"
  value       = aws_instance.api.id
}
