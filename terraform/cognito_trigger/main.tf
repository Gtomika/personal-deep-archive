locals {
  trigger_lambda_name = "${var.app_name}-${var.trigger_name}-${var.aws_region}"
}

resource "aws_cloudwatch_log_group" "trigger_function_log_group" {
  name = "/aws/lambda/${local.trigger_lambda_name}"
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

data "aws_iam_policy_document" "trigger_lambda_policy" {
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
    sid = "SendErrorNotification"
    effect = "Allow"
    actions = ["sns:Publish"]
    resources = [var.error_notification_topic_arn]
  }
  statement {
    sid = "SubscribeUser"
    effect = "Allow"
    actions = ["sns:Subscribe"]
    resources = [var.notifications_topic_arn]
  }
}

resource "aws_iam_role" "trigger_lambda_role" {
  name = "${var.app_name}-${var.trigger_name}-${var.aws_region}"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
  inline_policy {
    name = "${var.trigger_name}Policy"
    policy = data.aws_iam_policy_document.trigger_lambda_policy.json
  }
}

resource "aws_lambda_function" "trigger_function" {
  function_name = local.trigger_lambda_name
  description = "Invoked by AWS Cognito (${var.trigger_name})"
  role          = aws_iam_role.trigger_lambda_role.arn

  # deployment package must exist before
  filename = var.path_to_deployment_package
  source_code_hash = filebase64sha256(var.path_to_deployment_package)

  memory_size = 256
  runtime = "python3.9"
  handler = var.handler_name

  environment {
    variables = {
      ERROR_TOPIC_ARN = var.error_notification_topic_arn
      NOTIFICATION_TOPIC_ARN = var.notifications_topic_arn
    }
  }

  dead_letter_config {
    target_arn = var.error_notification_topic_arn
  }

  depends_on = [aws_cloudwatch_log_group.trigger_function_log_group]
}

resource aws_lambda_permission cognito_invoke_permissions {
  function_name = aws_lambda_function.trigger_function.function_name
  statement_id = "AllowCognitoToInvokeTrigger"
  action = "lambda:InvokeFunction"
  principal = "cognito-idp.amazonaws.com"
  source_account = var.aws_account_id
  # source_arn = var.cognito_user_pool_arn -> not possible due to circular dependencies
}