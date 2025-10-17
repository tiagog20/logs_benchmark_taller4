terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.83"
    }
  }
}

provider "aws" {
  region = "us-east-1"  # Cambia esto si necesitas otra región
}

variable "prefix" {
  description = "Prefix for the bucket"
  type        = string
}

resource "random_id" "server" {
  byte_length = 8
}

resource "aws_s3_bucket" "create_bucket" {
  bucket        = "${var.prefix}-${random_id.server.hex}"
  force_destroy = true
  tags = {
    Name = "${var.prefix}-bucket"
  }
}
