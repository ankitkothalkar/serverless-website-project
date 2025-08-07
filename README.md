# Serverless Website & API on AWS

This project demonstrates how to deploy a fully serverless, secure, and cost-effective static website with a functional contact form on AWS. The entire infrastructure is provisioned and managed using **Terraform (Infrastructure as Code)**.

## 🚀 Project Overview

The goal of this project was to build a complete, production-ready website solution that is highly available and requires minimal maintenance. The architecture is designed to be scalable and cost-effective, leveraging AWS services to handle everything from hosting to form submissions.

### Key Features
- **Serverless Architecture:** No servers to manage, paying only for what you use.
- **Automated Deployment:** All infrastructure is defined in Terraform, allowing for consistent and repeatable deployments.
- **Secure & Fast Delivery:** The website is served globally via a Content Delivery Network (CDN) with HTTPS encryption.
- **Domain Redirection:** All traffic from `http` and `www` is automatically redirected to `https://yourdomain.com`.
- **Functional Contact Form:** A serverless API handles form submissions and sends emails.

## 🛠️ Technology Stack

- **Terraform:** For infrastructure provisioning and management.
- **AWS S3:** To host the static website files.
- **AWS CloudFront:** As the CDN to serve content and handle domain redirection.
- **AWS Lambda:** A Python function to process form data.
- **AWS API Gateway:** To create a secure and scalable API endpoint for the form.
- **AWS Route 53:** For DNS management.
- **AWS Certificate Manager (ACM):** To provision and manage SSL/TLS certificates.
- **AWS SES (Simple Email Service):** For sending emails from the Lambda function.
- **Zoho Mail:** For a professional email solution integrated with the domain.
- **AWS CloudWatch:** For monitoring and debugging the Lambda function and API.

## 📁 Project Structure