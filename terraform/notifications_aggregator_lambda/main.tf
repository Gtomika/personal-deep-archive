locals {
  lambda_name = "${var.app_name}-NotificationsAggregator-${var.aws_region}"
}

resource "aws_cloudwatch_log_group" "function_log_group" {
  name = "/aws/lambda/${local.lambda_name}"
  retention_in_days = 365
}

data "aws_iam_policy_document" "lambda_trust_policy" {
  statement {
    sid = "AllowLambdaToAssume"
    effect = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "notification_aggregator_policy" {
  statement {
    sid = "Log"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }
  statement {
    sid = "PublishNotifications"
    effect = "Allow"
    actions = ["sns:Publish"]
    resources = [
      var.notifications_topic_arn,
      var.error_notification_topic_arn
    ]
  }
  statement {
    sid = "GetUpdateDynamodb"
    effect = "Allow"
    actions = ["dynamodb:Query", "dynamodb:GetItem", "dynamodb:UpdateItem"]
    resources = [var.restoration_notifications_table_arn]
  }
}

resource "aws_iam_role" "aggregator_lambda_role" {
  name = "${var.app_name}-NotificationAggregatorLambdaRole-${var.aws_region}"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
  inline_policy {
    name = "NotificationAggregatorPolicy"
    policy = data.aws_iam_policy_document.notification_aggregator_policy.json
  }
}

resource "aws_lambda_function" "notification_aggregator_function" {
  function_name = local.lambda_name
  role          = aws_iam_role.aggregator_lambda_role.arn

  handler = var.handler_name
  filename = var.path_to_deployment_package
  source_code_hash = filebase64sha256(var.path_to_deployment_package)
  runtime = "lambda3.9"
  memory_size = 256

  environment {
    variables = {
      ERROR_TOPIC_ARN = var.error_notification_topic_arn
      NOTIFICATION_TOPIC_ARN = var.notifications_topic_arn
      RESTORATION_NOTIFICATIONS_TABLE_NAME = var.restoration_notifications_table_name
    }
  }

  dead_letter_config {
    target_arn = var.error_notification_topic_arn
  }

  depends_on = [aws_cloudwatch_log_group.function_log_group]
}