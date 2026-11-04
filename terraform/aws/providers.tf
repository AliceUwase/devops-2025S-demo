terraform {
  required_version = "1.17.1"

  cloud {
    
    organization = "alu-devops-auwase_25"

    workspaces {
      name = "campus-notifier-infra"
    }
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}


provider "aws" {
  region = var.region
}


