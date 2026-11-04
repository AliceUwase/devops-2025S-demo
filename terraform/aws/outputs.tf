
output "instance_public_ip" {
  description = "App server address from the internet (SSH and browser)"
  value       = aws_instance.app_server.public_ip
}

output "instance_private_ip" {
  description = "App server address inside AWS"
  value       = aws_instance.app_server.private_ip
}

output "ssh_user" {
  description = "Username to log in with (Ubuntu images on AWS use 'ubuntu')"
  value       = "ubuntu"
}

output "app_port" {
  description = "Port the Campus Event Notifier is served on"
  value       = var.app_port
}

output "db_public_ip" {
  description = "Database server address from the internet (SSH only)"
  value       = aws_instance.db_server.public_ip
}

output "db_private_ip" {
  description = "Database server address inside AWS - use this as POSTGRES_HOST"
  value       = aws_instance.db_server.private_ip
}

output "db_ssh_port" {
  description = "Port to SSH into the database server"
  value       = 22
}

