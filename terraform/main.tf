module "archive_bucket" {
  source = "./archive_storage_bucket"
  app_name = var.app_name
  aws_region = var.aws_region
}

module "sns_setup" {
  source = "./sns"
  app_name = var.app_name
  aws_region = var.aws_region
  aws_account_id = var.aws_account_id
  developer_email_address = var.developer_email_address
  archive_bucket_arn = module.archive_bucket.archive_storage_bucket_arn
}

# provision lambda functions for cognito triggers
module "post_confirmation_cognito_trigger" {
  source = "./cognito_trigger"
  app_name = var.app_name
  aws_region = var.aws_region
  aws_account_id = var.aws_account_id
  error_notification_topic_arn = module.sns_setup.error_notification_topic_arn
  notifications_topic_arn = module.sns_setup.notifications_topic_arn
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
  notifications_topic_arn = module.sns_setup.notifications_topic_arn
}