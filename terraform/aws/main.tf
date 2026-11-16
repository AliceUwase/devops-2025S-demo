data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  owners = ["099720109477"] # Canonical
}


resource "aws_key_pair" "deployer" {
  key_name   = "campus-notifier-key"
  public_key = file(pathexpand(var.public_key_path))
}

resource "aws_security_group" "app" {
  #checkov:skip=CKV_AWS_382:Accepted risk - server needs outbound access for apt, pip and Docker image pulls; inbound is restricted to my IP
  name        = "campus-notifier-app"
  description = "App server: SSH and the app port, from my IP only"

  ingress {
    description = "SSH from my laptop"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  ingress {
    description = "Campus Event Notifier from my laptop"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  egress {
    description = "All outbound traffic (package and image downloads)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # -1 means "all protocols"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "db" {
  #checkov:skip=CKV_AWS_382:Accepted risk - server needs outbound access for apt and Postgres package updates; inbound is restricted to my IP and the app server
  name        = "campus-notifier-db"
  description = "DB server: SSH from my IP, Postgres from the app server only"

  ingress {
    description = "SSH from my laptop"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  ingress {
    description     = "Postgres from the app server only"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    description = "All outbound traffic (package downloads)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


resource "aws_instance" "app_server" {
  #checkov:skip=CKV_AWS_126:Accepted risk - detailed monitoring costs extra; basic 5-minute monitoring is enough for a class project
  #checkov:skip=CKV2_AWS_41:Accepted risk - instance calls no AWS APIs, so an IAM role would grant nothing
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.app.id]
  ebs_optimized          = true

  # Require IMDSv2 session tokens, so SSRF bugs can't read instance metadata
  metadata_options {
    http_tokens = "required"
  }

  # Encrypt the root disk at rest
  root_block_device {
    encrypted = true
  }

  tags = {
    Name = "campus-notifier-app"
  }
}

resource "aws_instance" "db_server" {
  #checkov:skip=CKV_AWS_126:Accepted risk - detailed monitoring costs extra; basic 5-minute monitoring is enough for a class project
  #checkov:skip=CKV2_AWS_41:Accepted risk - instance calls no AWS APIs, so an IAM role would grant nothing
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.db.id]
  ebs_optimized          = true

  # Require IMDSv2 session tokens, so SSRF bugs can't read instance metadata
  metadata_options {
    http_tokens = "required"
  }

  # Encrypt the root disk at rest (it holds the database)
  root_block_device {
    encrypted = true
  }

  tags = {
    Name = "campus-notifier-db"
  }
}
