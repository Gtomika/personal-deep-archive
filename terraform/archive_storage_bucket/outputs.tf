output "archive_storage_bucket_arn" {
  value = aws_s3_bucket.archive_storage_bucket.arn
}

output "archive_storage_bucket_name" {
  value = aws_s3_bucket.archive_storage_bucket.bucket
}

output "archive_storage_bucket_id" {
  value = aws_s3_bucket.archive_storage_bucket.id
}
