variable "app_name" {
  type = string
}

variable "aws_region" {
  type = string
  description = "Deployment AWS region"
}

variable "aws_account_id" {
  type = string
}

variable "aws_key_id" {
  type = string
  sensitive = true
  description = "AWS access key ID"
}

variable "aws_secret_key" {
  type = string
  sensitive = true
  description = "AWS secret key"
}

variable "aws_terraform_role_arn" {
  type = string
  description = "ARN of the role Terraform must assume"
}

variable "aws_assume_role_external_id" {
  type = string
  sensitive = true
  description = "Secret required to assume the Terraform role"
}

variable "developer_email_address" {
  type = string
  description = "Email of developer that is subscribed to SNS topics such as error topic"
}