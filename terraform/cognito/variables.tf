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
<h1>You have been invited to Gaspar Personal Deep Archive!</h1>
<ul>
<li>Your username: {username}</li>
<li>Your temporary password: {####}</li>
</ul>
Your temporary password is valid only for 1 day. When you log in the app for the first time you will be required to change it.
<p>
You can download the CLI app by following the instructions <a href="https://github.com/Gtomika/personal-deep-archive">here</a>.
EOT
}

variable "admin_invite_sms_message" {
  type = string
  default = "Invited to Gaspar Personal Deep Archive: your username is {username} and your temporary password is {####}"
}

variable "user_initializer_lambda_arn" {
  type = string
}

variable "archive_data_bucket_arn" {
  type = string
}

variable "notifications_topic_arn" {
  type = string
}