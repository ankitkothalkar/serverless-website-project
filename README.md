Markdown

# Serverless Website & API on AWS

This project demonstrates how to deploy a fully serverless, secure, and cost-effective static website with a functional contact form on AWS. The entire infrastructure is provisioned and managed using **Terraform (Infrastructure as Code)**.

##  Project Overview

The goal of this project was to build a complete, production-ready website solution that is highly available and requires minimal maintenance. The architecture is designed to be scalable and cost-effective, leveraging AWS services to handle everything from hosting to form submissions.

### Key Features
- **Serverless Architecture:** No servers to manage, paying only for what you use.
- **Automated Deployment:** All infrastructure is defined in Terraform, allowing for consistent and repeatable deployments.
- **Secure & Fast Delivery:** The website is served globally via a Content Delivery Network (CDN) with HTTPS encryption.
- **Domain Redirection:** All traffic from `http` and `www` is automatically redirected to `https://yourdomain.com`.
- **Functional Contact Form:** A serverless API handles form submissions and sends emails.

## ️ Technology Stack

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
<<<<<<< HEAD

.
├── main.tf                 # Main Terraform configuration file
├── variables.tf            # Input variables for the project
├── lambda_function.py      # Python code for the Lambda function
├── README.md               # This file


##  How to Deploy

To deploy this project, you will need to configure your AWS credentials and create a `terraform.tfvars` file with your specific domain name and email addresses.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repository-name.git](https://github.com/your-username/your-repository-name.git)
    cd your-repository-name
    ```

2.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

3.  **Validate and Plan:**
    ```bash
    terraform plan
    ```

4.  **Apply the configuration:**
    ```bash
    terraform apply
    ```
    This command will provision all the necessary AWS resources.

5.  **Get API Endpoint URL:**
    After applying the Terraform configuration, get the API endpoint URL from the output. You will need this for your website's JavaScript code.
    ```bash
    terraform output form_api_url
    ```

6.  **Upload Website Files:**
    Upload your static website files (e.g., `index.html`, JavaScript files) to the S3 bucket.
    ```bash
    aws s3 cp . s3://[yourdomain.com/](https://yourdomain.com/) --recursive
    ```

7.  **Invalidate CloudFront Cache:**
    To ensure your website is serving the latest files, you must invalidate the CloudFront cache.
    ```bash
    aws cloudfront create-invalidation --distribution-id YOUR_CLOUDFRONT_DISTRIBUTION_ID --paths "/*"
    ```

##  Contribution

Feel free to open an issue or submit a pull request if you have suggestions for improvement

