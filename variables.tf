# variables.tf

variable "domain_name" {
  description = "The domain name for the website."
  type        = string
}

variable "aws_region" {
  description = "The AWS region to deploy the resources in."
  type        = string
  default     = "us-east-1"
}

variable "sender_email" {
  description = "The verified sender email address in AWS SES."
  type        = string
}

variable "recipient_email" {
  description = "The recipient email address for form submissions."
  type        = string
}