# One small, safe AI-API server in its own network, plus a private bucket for documents.
# Picture: lesson 24's building. VPC = building, subnet = floor, internet gateway = street door,
# route table = hallway signs, security group = door guard.

# ---------- Look things up (data sources read, they never create) ----------

# Which availability zones (buildings) exist in this region right now?
data "aws_availability_zones" "available" {
  state = "available"
}

# The newest Amazon Linux 2023 image ID, published by AWS in Parameter Store.
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# ---------- Network ----------

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true # servers can look up names like api.anthropic.com
  enable_dns_hostnames = true
  tags                 = { Name = "${var.project_name}-vpc" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id # "put this floor in THAT building"
  cidr_block              = var.public_subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0] # the first zone
  map_public_ip_on_launch = true                                           # servers here get a public IP
  tags                    = { Name = "${var.project_name}-public-a" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project_name}-igw" }
}

# Hallway sign: "every address that is not inside the VPC -> go out through the street door".
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${var.project_name}-public-rt" }
}

# Hang the sign on the public floor.
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ---------- Door guard (security group) ----------

resource "aws_security_group" "api" {
  name        = "${var.project_name}-api-sg"
  description = "AI API server: HTTP in from anywhere, everything out"
  vpc_id      = aws_vpc.main.id
}

# Let anyone in on port 80 (HTTP). No SSH rule at all: we connect with Session Manager instead.
resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.api.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

# Let the server call out to anything (Claude API, package downloads). "-1" = every protocol.
resource "aws_vpc_security_group_egress_rule" "all_out" {
  security_group_id = aws_security_group.api.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# ---------- Identity for the server (IAM role) ----------

# Who may "wear" this role: the EC2 service, on behalf of our server.
data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "api" {
  name               = "${var.project_name}-api-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

# One AWS-managed key card: lets you open a shell on the server from the console
# (Systems Manager Session Manager), so no SSH port and no SSH keys are needed.
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.api.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Least privilege: the server may READ documents from our bucket, and nothing else in S3.
data "aws_iam_policy_document" "read_docs" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.docs.arn}/*"]
  }
  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.docs.arn]
  }
}

resource "aws_iam_role_policy" "read_docs" {
  name   = "read-docs-bucket"
  role   = aws_iam_role.api.id
  policy = data.aws_iam_policy_document.read_docs.json
}

# EC2 attaches roles through an "instance profile" (a holder for the role).
resource "aws_iam_instance_profile" "api" {
  name = "${var.project_name}-api-profile"
  role = aws_iam_role.api.name
}

# ---------- The server ----------

resource "aws_instance" "api" {
  ami                    = data.aws_ssm_parameter.al2023.value
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.api.id]
  iam_instance_profile   = aws_iam_instance_profile.api.name

  # Only allow the safer version 2 of the instance metadata service.
  metadata_options {
    http_tokens = "required"
  }

  # A script that runs once at first boot: install Docker, start a tiny web server on port 80.
  user_data = <<-SCRIPT
    #!/bin/bash
    dnf install -y docker
    systemctl enable --now docker
    docker run -d --restart unless-stopped -p 80:5678 hashicorp/http-echo:1.0 \
      -text="Hello from ${var.project_name} on AWS"
  SCRIPT

  tags = { Name = "${var.project_name}-api" }
}

# ---------- Private storage for documents (S3) ----------

# Bucket names are global across ALL AWS customers, so add a random ending.
resource "random_id" "bucket_suffix" {
  byte_length = 4 # 8 hex characters
}

resource "aws_s3_bucket" "docs" {
  bucket        = "${var.project_name}-docs-${random_id.bucket_suffix.hex}"
  force_destroy = true # allow "terraform destroy" to delete it even with files inside (practice only!)
}

# Four locks that make sure nothing in this bucket can ever be made public.
resource "aws_s3_bucket_public_access_block" "docs" {
  bucket                  = aws_s3_bucket.docs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Keep old versions of every file, so a mistake or overwrite can be undone.
resource "aws_s3_bucket_versioning" "docs" {
  bucket = aws_s3_bucket.docs.id
  versioning_configuration {
    status = "Enabled"
  }
}
