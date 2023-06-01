variable "app_name" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "aws_account_id" {
  type = string
}


variable "error_notification_topic_arn" {
  type = string
}

variable "notifications_topic_arn" {
  type = string
}

variable "path_to_deployment_package" {
  type = string
}

variable "handler_name" {
  type = string
}

variable "restoration_notifications_table_name" {
  type = string
}

variable "restoration_notifications_table_arn" {
  type = string
}

variable "archive_bucket_arn" {
  type = string
}