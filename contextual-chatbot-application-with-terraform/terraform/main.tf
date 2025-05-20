# -----------------------------------------------------
# Use Cloudformation template to create Amazon Bedrock 
# Knowledge Base and create an S3 bucket.
# -----------------------------------------------------

resource "random_integer" "kb_suffix" {
  min = 1000
  max = 9999
}

resource "aws_cloudformation_stack" "kb-stack" {
  name = "my-cloudformation-stack"
  template_body = file("cf.yaml")
  capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
  parameters = {
    KnowledgeBaseName = "kb-${random_integer.kb_suffix.result}",
    DataSourceName = "kb-ds-${random_integer.kb_suffix.result}",
    S3BucketName = "kb-bucket-${random_integer.kb_suffix.result}",
    AOSSCollectionName="kb-col-${random_integer.kb_suffix.result}"
  }
}

# -----------------------------------------------------
# Cognito User Pool
# -----------------------------------------------------

resource "aws_cognito_user_pool" "pool" {
  name = "my-user-pool"

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  alias_attributes = ["preferred_username","email","phone_number"]
  auto_verified_attributes = ["email"]

  # Add schema attributes to make email required
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable            = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  schema {
    name                = "name"
    attribute_data_type = "String"
    required            = true
    mutable            = true

    string_attribute_constraints {
      min_length = 1
      max_length = 50
    }
  }

    schema {
    name                = "phone_number"
    attribute_data_type = "String"
    required            = false
    mutable            = true

    string_attribute_constraints {
      min_length = 1
      max_length = 50
    }
  }


  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject = "Account Confirmation"
    email_message = "Your confirmation code is {####}"
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name = "my-app-client"

  user_pool_id = aws_cognito_user_pool.pool.id

  generate_secret     = false

  # Enable OAuth2 features
  allowed_oauth_flows = ["code", "implicit"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes = [
    "aws.cognito.signin.user.admin",
    "email",
    "openid",
    "profile"
  ]

  # Callback and Logout URLs
  callback_urls = [
    "https://${aws_cloudfront_distribution.ecs_distribution.domain_name}/oauth2/idpresponse",
    "https://${aws_cloudfront_distribution.ecs_distribution.domain_name}"
  ]
  logout_urls = [
    "https://${aws_cloudfront_distribution.ecs_distribution.domain_name}"
  ]
  
  # Supported identity providers
  supported_identity_providers = ["COGNITO"]

  # Enable all auth flows
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]
}
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "my-app-${random_integer.kb_suffix.result}"
  user_pool_id = aws_cognito_user_pool.pool.id
}

#create a Test user 
resource "aws_cognito_user" "test_user" {
  user_pool_id = aws_cognito_user_pool.pool.id
  username     = "test3"

  attributes = {
    email          = "test3@example.com"
    email_verified = true
  }

  password = "Test@1234567"

  depends_on = [aws_cognito_user_pool.pool]
}

# -----------------------------------------------------
# IAM Role for ECS Task Execution
# -----------------------------------------------------

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_cloudwatch_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_s3_full_access" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_bedrock_full_access" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_cognito" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonCognitoReadOnly"
}

# -----------------------------------------------------
# ECS Cluster and Task Definition
# -----------------------------------------------------

resource "aws_ecs_cluster" "my_cluster" {
  name = "my-ecs-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "my_task" {
  family                   = "my-task-family"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn 
  task_role_arn            = aws_iam_role.ecs_task_execution_role.arn
  container_definitions = jsonencode([

    {
      name  = "my-container"
      image = "${aws_ecr_repository.app_repo.repository_url}:${var.image_tag}"
      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/my-task-family"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      environment = [
        {
          name  = "COGNITO_CLIENT_ID"
          value = aws_cognito_user_pool_client.client.id
        },
        {
          name  = "COGNITO_POOL_ID"
          value = aws_cognito_user_pool.pool.id
        },
        {
          name  = "DataSourceId"
          value = aws_cloudformation_stack.kb-stack.outputs.DataSourceId
        },
        {
          name  = "KnowledgeBaseBucket"
          value = aws_cloudformation_stack.kb-stack.outputs.KnowledgeBaseBucket
        },
        {
          name  = "KnowledgeBaseId"
          value = aws_cloudformation_stack.kb-stack.outputs.KnowledgeBaseId
        }
      ]

    }
  ])
}
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/my-task-family"
  retention_in_days = 30
}

# -----------------------------------------------------
# Networking (VPC and Subnets)
# -----------------------------------------------------

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# -----------------------------------------------------
# Security Groups
# -----------------------------------------------------

resource "aws_security_group" "sg_ecs_tasks" {
  name        = "ecs-tasks-sg"
  description = "Allow inbound traffic to ECS tasks"
  vpc_id      = data.aws_vpc.default.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "alb_sg" {
  name        = "alb-sg"
  description = "Security group for ALB"
  vpc_id      = data.aws_vpc.default.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group_rule" "ecs_from_alb" {
  description = "ECS Security group rule allowing inbound traffic from ELB on port 8501"
  type                     = "ingress"
  from_port                = 8501
  to_port                  = 8501
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb_sg.id
  security_group_id        = aws_security_group.sg_ecs_tasks.id
}
resource "aws_security_group_rule" "ecs_from_local" {
  description = "ELB Security group rule allowing inbound traffic from Cloudfronts on port 8501"
  type                     = "ingress"
  from_port                = 8501
  to_port                  = 8501
  protocol                 = "tcp"
  cidr_blocks              = [data.aws_vpc.default.cidr_block]
  security_group_id        = aws_security_group.sg_ecs_tasks.id
}

# -----------------------------------------------------
# ECS Service
# -----------------------------------------------------

resource "aws_ecs_service" "my_service" {
  name            = "my-ecs-service"
  cluster         = aws_ecs_cluster.my_cluster.id
  task_definition = aws_ecs_task_definition.my_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.sg_ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ecs_tg.arn
    container_name   = "my-container"
    container_port   = 8501
  }
  force_new_deployment = true
}

# -----------------------------------------------------
# Application Load Balancer
# -----------------------------------------------------

resource "aws_lb" "ecs_alb" {
  name               = "ecs-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = data.aws_subnets.default.ids
}

resource "aws_lb_target_group" "ecs_tg" {
  name        = "ecs-target-group"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 60
    interval            = 300
    matcher             = "200,301,302"
  }
}

resource "aws_lb_listener" "ecs_alb_listener" {
  load_balancer_arn = aws_lb.ecs_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs_tg.arn
  }
}

# -----------------------------------------------------
# CloudFront Distribution
# -----------------------------------------------------

resource "aws_cloudfront_distribution" "ecs_distribution" {
  origin {
    domain_name = aws_lb.ecs_alb.dns_name
    origin_id   = aws_lb.ecs_alb.dns_name

    custom_origin_config {
      http_port              = 80
      origin_protocol_policy = "http-only"
      https_port             = 443
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = aws_lb.ecs_alb.dns_name

    # Use the UseOriginCacheHeaders managed policy
    cache_policy_id          = "83da9c7e-98b4-4e11-a168-04f0df8e2c65"  # UseOriginCacheControlHeaders
    origin_request_policy_id = "216adef6-5c7f-47e4-b989-5492eafa07d3"  # AllViewers


    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    minimum_protocol_version = "TLSv1.2_2021"
  }
  
  # Use price class for US only
  price_class = "PriceClass_100"
}


# -----------------------------------------------------
# Additional Security Group Rules
# -----------------------------------------------------

# Get the AWS-managed prefix list for CloudFront
data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

resource "aws_security_group_rule" "alb_cloudfront" {
  type        = "ingress"
  from_port   = 80
  to_port     = 80
  protocol    = "tcp"
  prefix_list_ids   = [data.aws_ec2_managed_prefix_list.cloudfront.id]
  security_group_id = aws_security_group.alb_sg.id
}

# -----------------------------------------------------
# ECR Repository
# -----------------------------------------------------

resource "aws_ecr_repository" "app_repo" {
  name                 = "my-app-repo"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
  force_delete = true
}

# -----------------------------------------------------
# Build and Push Docker Image
# -----------------------------------------------------

resource "null_resource" "docker_build_push" {
  triggers = {
    always_run = "${timestamp()}"
  }

  provisioner "local-exec" {
    command = <<-EOT
      # Build Docker image
      docker buildx build --platform linux/amd64 -t ${aws_ecr_repository.app_repo.repository_url}:${var.image_tag} .././src/ 

      # Authenticate Docker to ECR
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.app_repo.repository_url}

      # Push image to ECR
      docker push ${aws_ecr_repository.app_repo.repository_url}:${var.image_tag}
    EOT
  }

  depends_on = [aws_ecr_repository.app_repo]
}