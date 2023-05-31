# create a topic for errors and subscribe the developer to it
resource "aws_sns_topic" "error_notification_topic" {
  name = "${var.app_name}-ErrorNotifications-${var.aws_region}"
}

resource "aws_sns_topic_subscription" "developer_error_notification_subscription" {
  protocol  = "email"
  endpoint  = var.developer_email_address # must be confirmed on previsioning
  topic_arn = aws_sns_topic.error_notification_topic.arn
}

resource "aws_sns_topic" "notifications_topic" {
  name = "${var.app_name}-Notifications-${var.aws_region}"
}
