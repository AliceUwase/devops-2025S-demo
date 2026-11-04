
variable "region" {
  description = "AWS region to build the servers in"
  type        = string
  default     = "eu-north-1"  
}

variable "my_ip_cidr" {
  description = "the  laptop's public IPv4 address with /32"
 
}

variable "instance_type" {
  description = "Size of each server (how much CPU and memory)"
  type        = string
  default     = "c7i-flex.large" 
}

variable "public_key_path" {
  description = "Path to the SSH public key that will be allowed to log into both servers"
  type        = string
  default     = "~/.ssh/alu-devops.pub"
}

variable "app_port" {
  description = "Port the Campus Event Notifier listens on"
  type        = number
  default     = 8000
}
