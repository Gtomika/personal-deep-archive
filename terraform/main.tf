# create a topic for errors and subscribe the developer to it
resource "aws_sns_topic" "error_notification_topic" {
  name = "${var.app_name}-ErrorNotifications-${var.aws_region}"
}

resource "aws_sns_topic_subscription" "developer_error_notification_subscription" {
  protocol  = "email"
  endpoint  = var.developer_email_address # must be confirmed on previsioning
  topic_arn = aws_sns_topic.error_notification_topic.arn
}

module "archive_bucket" {
  source = "./archive_storage_bucket"
  app_name = var.app_name
  aws_region = var.aws_region
}

# provision lambda functions for cognito triggers
module "post_confirmation_cognito_trigger" {
  source = "./cognito_trigger"
  app_name = var.app_name
  aws_region = var.aws_region
  error_notification_topic_arn = aws_sns_topic.error_notification_topic.arn
  handler_name = "lambda_function.lambda_handler"
  path_to_deployment_package = "${path.module}/../post_confirmation_trigger.zip"
  trigger_name = "PostConfirmation"
}

# provision cognito user and identity pools
module "cognito_setup" {
  source = "./cognito"
  app_name = var.app_name
  aws_region = var.aws_region
  user_initializer_lambda_arn = module.post_confirmation_cognito_trigger.trigger_lambda_arn
  archive_data_bucket_arn = module.archive_bucket.archive_storage_bucket_arn
}