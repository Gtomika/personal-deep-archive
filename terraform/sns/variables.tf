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

variable "developer_email_address" {
  type = string
  description = "Email of developer that is subscribed to SNS topics such as error topic"
}

variable "archive_bucket_arn" {
  type = string
}