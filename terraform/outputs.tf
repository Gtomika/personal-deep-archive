output "archive_bucket_arn" {
  value = module.archive_bucket.archive_storage_bucket_arn
}

output "user_pool_id" {
  value = module.cognito_setup.cognito_user_pool_id
}