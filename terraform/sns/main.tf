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

data "aws_iam_policy_document" "notifications_topic_policy" {
  statement {
    sid = "AllowS3ToPublish"
    effect = "Allow"
    actions = ["sns:Publish"],
    resources = [aws_sns_topic.notifications_topic.arn],
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.aws_account_id]
    }
    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [var.archive_bucket_arn]
    }
  }
}

resource "aws_sns_topic_policy" "notifications_topic_policy_attachment" {
  arn    = aws_sns_topic.notifications_topic.arn
  policy = data.aws_iam_policy_document.notifications_topic_policy.json
}