# Terraform & AWS Provider Configuration
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- Website Hosting (S3) ---

resource "aws_s3_bucket" "website_bucket" {
  bucket = var.domain_name
}

resource "aws_cloudfront_origin_access_identity" "oai" {
  comment = "OAI to allow CloudFront to access S3 bucket"
}

resource "aws_s3_bucket_public_access_block" "public_access_block" {
  bucket                  = aws_s3_bucket.website_bucket.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "allow_cloudfront_access" {
  bucket = aws_s3_bucket.website_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontOaiAccess",
        Effect    = "Allow",
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.oai.iam_arn
        },
        Action   = "s3:GetObject",
        Resource = "${aws_s3_bucket.website_bucket.arn}/*"
      }
    ]
  })
}

resource "aws_s3_bucket_website_configuration" "website_config" {
  bucket = aws_s3_bucket.website_bucket.id
  index_document {
    suffix = "index.html"
  }
}

# --- www.domain.com redirect ---
# Note: S3 bucket for www is no longer configured as a website.
# Redirection is handled by CloudFront to avoid the S3 PermanentRedirect error.

resource "aws_s3_bucket" "www_redirect_bucket" {
  bucket = "www.${var.domain_name}"
}

resource "aws_cloudfront_distribution" "www_redirect_distribution" {
  origin {
    domain_name = aws_s3_bucket.www_redirect_bucket.bucket_regional_domain_name
    origin_id   = aws_s3_bucket.www_redirect_bucket.id
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = ""

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = aws_s3_bucket.www_redirect_bucket.id
    viewer_protocol_policy = "redirect-to-https"
    forwarded_values {
      query_string = false
      headers      = ["Host"]
      cookies {
        forward = "none"
      }
    }
  }

  aliases = ["www.${var.domain_name}"]

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.cert_validation.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}

# --- DNS & SSL (Route 53 & ACM) ---

resource "aws_route53_zone" "primary" {
  name = var.domain_name
}

resource "aws_acm_certificate" "cert" {
  domain_name           = var.domain_name
  validation_method     = "DNS"
  subject_alternative_names = ["*.${var.domain_name}"]
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.cert.domain_validation_options : dvo.domain_name => dvo
  }
  allow_overwrite = true
  name            = each.value.resource_record_name
  records         = [each.value.resource_record_value]
  ttl             = 60
  type            = each.value.resource_record_type
  zone_id         = aws_route53_zone.primary.zone_id
}

resource "aws_acm_certificate_validation" "cert_validation" {
  certificate_arn       = aws_acm_certificate.cert.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# --- CloudFront Distribution ---

resource "aws_cloudfront_distribution" "s3_distribution" {
  origin {
    domain_name = aws_s3_bucket.website_bucket.bucket_regional_domain_name
    origin_id   = aws_s3_bucket.website_bucket.id
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = aws_s3_bucket.website_bucket.id
    viewer_protocol_policy = "redirect-to-https"
    forwarded_values {
      query_string = false
      headers      = ["Origin"]
      cookies {
        forward = "none"
      }
    }
  }

  price_class = "PriceClass_100"
  aliases = [var.domain_name]

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.cert_validation.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}

# --- Route 53 DNS Records ---

resource "aws_route53_record" "domain_root" {
  zone_id = aws_route53_zone.primary.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.s3_distribution.domain_name
    zone_id                = aws_cloudfront_distribution.s3_distribution.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "www_redirect_record" {
  zone_id = aws_route53_zone.primary.zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.www_redirect_distribution.domain_name
    zone_id                = aws_cloudfront_distribution.www_redirect_distribution.hosted_zone_id
    evaluate_target_health = false
  }
}

# --- Form API (Lambda & API Gateway) ---

resource "aws_iam_role" "lambda_exec_role" {
  name = "FormProcessorRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "ses_send_email" {
  name        = "FormProcessorSESPolicy"
  description = "Allows Lambda to send emails using SES"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ses:SendEmail"
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ses_send_email_attachment" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.ses_send_email.arn
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "lambda_function.py"
  output_path = "lambda_function_payload.zip"
}

resource "aws_lambda_function" "form_processor" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "FormProcessorFunction"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.12"
  
  environment {
    variables = {
      SENDER_EMAIL    = var.sender_email
      RECIPIENT_EMAIL = var.recipient_email
    }
  }
}

resource "aws_api_gateway_rest_api" "form_api" {
  name        = "FormAPI"
  description = "API for handling form submissions"
}

resource "aws_api_gateway_resource" "contact_resource" {
  rest_api_id = aws_api_gateway_rest_api.form_api.id
  parent_id   = aws_api_gateway_rest_api.form_api.root_resource_id
  path_part   = "contact"
}

# ----------------- POST Method and Integration -----------------

resource "aws_api_gateway_method" "post_method" {
  rest_api_id   = aws_api_gateway_rest_api.form_api.id
  resource_id   = aws_api_gateway_resource.contact_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.form_api.id
  resource_id             = aws_api_gateway_resource.contact_resource.id
  http_method             = aws_api_gateway_method.post_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.form_processor.invoke_arn
}

# ----------------- CORS Configuration -----------------
# OPTIONS method for CORS preflight
resource "aws_api_gateway_method" "options_method" {
  rest_api_id   = aws_api_gateway_rest_api.form_api.id
  resource_id   = aws_api_gateway_resource.contact_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# MOCK integration for the OPTIONS request
resource "aws_api_gateway_integration" "options_integration" {
  rest_api_id             = aws_api_gateway_rest_api.form_api.id
  resource_id             = aws_api_gateway_resource.contact_resource.id
  http_method             = aws_api_gateway_method.options_method.http_method
  type                    = "MOCK"
  request_templates = {
    "application/json" = "{ \"statusCode\": 200 }"
  }
}

# Method response for OPTIONS, defining headers to allow
resource "aws_api_gateway_method_response" "options_method_response" {
  rest_api_id = aws_api_gateway_rest_api.form_api.id
  resource_id = aws_api_gateway_resource.contact_resource.id
  http_method = aws_api_gateway_method.options_method.http_method
  status_code = "200"
  response_models = {
    "application/json" = "Empty"
  }
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

# Integration response for OPTIONS, providing the actual CORS headers
resource "aws_api_gateway_integration_response" "options_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.form_api.id
  resource_id = aws_api_gateway_resource.contact_resource.id
  http_method = aws_api_gateway_method.options_method.http_method
  status_code = aws_api_gateway_method_response.options_method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'https://${var.domain_name}'"
  }
}

# Add Method and Integration Response to the POST method
resource "aws_api_gateway_method_response" "post_method_response" {
  rest_api_id   = aws_api_gateway_rest_api.form_api.id
  resource_id   = aws_api_gateway_resource.contact_resource.id
  http_method   = aws_api_gateway_method.post_method.http_method
  status_code   = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_integration_response" "post_integration_response" {
  rest_api_id         = aws_api_gateway_rest_api.form_api.id
  resource_id         = aws_api_gateway_resource.contact_resource.id
  http_method         = aws_api_gateway_method.post_method.http_method
  status_code         = aws_api_gateway_method_response.post_method_response.status_code
  selection_pattern   = ""

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'https://${var.domain_name}'"
  }
}

# ----------------- Deployment -----------------

resource "aws_api_gateway_deployment" "form_api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.form_api.id
  triggers = {
    # Is trigger se har 'terraform apply' par deployment force hoga
    redeployment_trigger = timestamp()
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod_stage" {
  deployment_id = aws_api_gateway_deployment.form_api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.form_api.id
  stage_name    = "prod"
}

resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.form_processor.function_name
  principal     = "apigateway.amazonaws.com"
  
  source_arn = "${aws_api_gateway_rest_api.form_api.execution_arn}/*/*"
}

# --- Final Outputs ---

output "website_url" {
  value = "https://${var.domain_name}"
}

output "form_api_url" {
  value = aws_api_gateway_stage.prod_stage.invoke_url
}