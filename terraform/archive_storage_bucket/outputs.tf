output "archive_storage_bucket_arn" {
  value = aws_s3_bucket.archive_storage_bucket.arn
}

output "archive_storage_bucket_name" {
  value = aws_s3_bucket.archive_storage_bucket.bucket
}

output "restoration_notifications_table_name" {
  value = aws_dynamodb_table.restoration_notifications_table.name
}

output "restoration_notifications_table_arn" {
  value = aws_dynamodb_table.restoration_notifications_table.arn
}