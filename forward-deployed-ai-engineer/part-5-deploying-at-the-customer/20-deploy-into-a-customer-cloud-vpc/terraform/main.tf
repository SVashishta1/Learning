# A private home for the assistant inside the customer's AWS account:
#   VPC -> 2 private subnets (no internet gateway, no public IPs)
#       -> VPC endpoints so the VM reaches Bedrock, Secrets Manager, logs, SSM and ECR privately
#       -> 1 VM with an IAM role (no keys on disk) that may call ONLY the allowed Bedrock models and read ONE secret

# ---------------------------------------------------------------- network
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true # needed for private DNS names of the VPC endpoints
  enable_dns_hostnames = true
  tags                 = { Name = "${var.name}-vpc" }
}

resource "aws_subnet" "private" {
  count                   = length(var.azs) # one subnet per availability zone
  vpc_id                  = aws_vpc.main.id
  availability_zone       = var.azs[count.index]
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index) # 10.42.0.0/24, 10.42.1.0/24
  map_public_ip_on_launch = false                                    # nothing here ever gets a public IP
  tags                    = { Name = "${var.name}-private-${count.index}" }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id # no route to 0.0.0.0/0: there is simply no way out to the internet
  tags   = { Name = "${var.name}-private" }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

resource "aws_security_group" "app" {
  name        = "${var.name}-app"
  description = "The assistant VM: HTTPS-in from the corporate network only"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "App port from the corporate network, via the internal load balancer"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.corporate_cidr]
  }

  egress {
    description = "HTTPS only, and only inside the VPC (to the VPC endpoints)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
}

resource "aws_security_group" "endpoints" {
  name        = "${var.name}-endpoints"
  description = "VPC endpoints accept HTTPS from the app"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
}

# PrivateLink "interface endpoints": a private network card inside YOUR subnets for an AWS service.
# With private_dns_enabled, the normal service name (e.g. bedrock-runtime.eu-central-1.amazonaws.com)
# resolves to these private IPs, so the SDK needs no change.
resource "aws_vpc_endpoint" "interface" {
  for_each            = toset(var.interface_endpoints)
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.endpoints.id]
  private_dns_enabled = true
  tags                = { Name = "${var.name}-${each.value}" }
}

# S3 uses a cheaper "gateway endpoint" (a route), needed for pulling image layers from ECR.
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]
}

# ---------------------------------------------------------------- secret
resource "aws_secretsmanager_secret" "app" {
  name        = "${var.name}/app"
  description = "App secrets. The VALUE is set by a human (console or CLI), never in Terraform code or state."
}

# ---------------------------------------------------------------- identity: an IAM role instead of keys
data "aws_iam_policy_document" "assume_ec2" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"] # only EC2 machines may wear this role
    }
  }
}

data "aws_iam_policy_document" "app" {
  statement {
    sid       = "CallOnlyApprovedModels"
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = var.bedrock_model_arns
  }
  statement {
    sid       = "ReadOnlyOurSecret"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.app.arn]
  }
  statement {
    sid       = "PullOurImage"
    actions   = ["ecr:GetAuthorizationToken", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"]
    resources = ["*"] # GetAuthorizationToken cannot be limited to one repository
  }
  statement {
    sid       = "WriteLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:${var.region}:*:log-group:/${var.name}*"]
  }
}

resource "aws_iam_role" "app" {
  name               = "${var.name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_ec2.json
}

resource "aws_iam_role_policy" "app" {
  name   = "${var.name}-least-privilege"
  role   = aws_iam_role.app.id
  policy = data.aws_iam_policy_document.app.json
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.app.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore" # shell access via SSM: no SSH port, no keys
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.name}-profile"
  role = aws_iam_role.app.name
}

# ---------------------------------------------------------------- the VM
resource "aws_instance" "app" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.private[0].id
  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile   = aws_iam_instance_profile.app.name

  metadata_options {
    http_tokens = "required" # IMDSv2 only: protects the role's temporary credentials
  }

  root_block_device {
    encrypted   = true
    volume_size = 30
  }

  # First boot: start the assistant container with the Bedrock provider (image pulled from the customer's ECR).
  user_data = <<-EOT
    #!/bin/bash
    dnf install -y docker && systemctl enable --now docker
    aws ecr get-login-password --region ${var.region} | docker login --username AWS --password-stdin ${split("/", var.image)[0]}
    docker run -d --restart unless-stopped -p 8000:8000 \
      -e LLM_PROVIDER=bedrock -e AWS_REGION=${var.region} \
      ${var.image}
  EOT

  tags = { Name = "${var.name}-vm" }
}
