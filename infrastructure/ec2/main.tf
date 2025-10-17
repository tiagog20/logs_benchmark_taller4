terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.83"
    }
  }
}

provider "aws" {
  region  = "us-east-1"
  profile = "default"
  skip_credentials_validation = true
}

variable "prefix" {
  description = "Prefix for the resources"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket used for deployment"
  type        = string
}

variable "instance_type" {
  description = "Instance type to use"
  type        = string
}

variable "ami" {
  description = "AMI to use"
  type        = string
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "server" {
  name        = "${var.prefix}-sg"
  description = "Security group for SSM access"
  vpc_id      = data.aws_vpc.default.id
}

resource "aws_vpc_security_group_egress_rule" "to_all" {
  security_group_id = aws_security_group.server.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_iam_role" "this" {
  name = "${var.prefix}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_instance_profile" "this" {
  name = "${var.prefix}-profile"
  role = aws_iam_role.this.name
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_policy" "s3_full" {
  name        = "s3-full-policy-${var.prefix}"
  description = "Allows EC2 to access bucket"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Action = [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      Resource = [
        "arn:aws:s3:::${var.bucket_name}",
        "arn:aws:s3:::${var.bucket_name}/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "s3_full_attach" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.s3_full.arn
}

resource "aws_instance" "this" {
  ami                         = var.ami
  instance_type               = var.instance_type
  vpc_security_group_ids      = [aws_security_group.server.id]
  iam_instance_profile        = aws_iam_instance_profile.this.name
  associate_public_ip_address = true

  user_data = <<-EOF
              #!/bin/bash
              apt update -y
              apt install -y default-jdk scala python3 python3-pip awscli wget unzip
              wget https://downloads.apache.org/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz
              tar xvf spark-3.5.0-bin-hadoop3.tgz
              mv spark-3.5.0-bin-hadoop3 /opt/spark
              echo "export PATH=\\$PATH:/opt/spark/bin:/opt/spark/sbin" >> /home/ubuntu/.bashrc
              echo "export SPARK_HOME=/opt/spark" >> /home/ubuntu/.bashrc
              pip3 install pyspark boto3
              echo "✅ Spark instalado correctamente." > /home/ubuntu/status.txt
              EOF

  tags = {
    Name = "${var.prefix}-server"
  }

  depends_on = [
    aws_iam_instance_profile.this,
    aws_security_group.server
  ]
}

output "instance_id" {
  value       = aws_instance.this.id
  description = "EC2 ID for SSM"
}

output "instance_public_ip" {
  value       = aws_instance.this.public_ip
  description = "Public IP (informational)"
}
