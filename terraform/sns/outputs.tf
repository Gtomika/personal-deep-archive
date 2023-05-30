output "notifications_topic_arn" {
  value = aws_sns_topic.notifications_topic.arn
}

output "error_notification_topic_arn" {
  value = aws_sns_topic.error_notification_topic.arn
}