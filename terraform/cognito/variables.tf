variable "app_name" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "admin_invite_email_subject" {
  type = string
  default = "Gaspar Personal Deep Archive Invite"
}

# must contain {username} and {####}
variable "admin_invite_email_content" {
  type = string
  default = <<EOT
You have been invited to Gaspar Personal Deep Archive!

Your username: {username} (you can also use your email instead)
Your temporary password: {####}

It is required to change your default password. It is valid only for 1 day.
  EOT
}

variable "user_initializer_lambda_arn" {
  type = string
}

variable "archive_data_bucket_arn" {
  type = string
}
