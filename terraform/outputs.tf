output "vault_notifications_topic_arn" {
  value = aws_sns_topic.glacier_vault_notifications_topic.arn
}

output "vault_arn" {
  value = aws_glacier_vault.deep_archive_vault.arn
}