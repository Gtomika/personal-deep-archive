resource "aws_s3_bucket" "archive_storage_bucket" {
  bucket = "${lower(var.app_name)}-archive-data-${var.aws_region}"
}

resource "aws_s3_bucket_versioning" "archival_versioning" {
  bucket = aws_s3_bucket.archive_storage_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "lifecycle_config" {
  bucket = aws_s3_bucket.archive_storage_bucket.id
  rule {
    id     = "restored-objects-expiration"
    status = "Enabled"
    filter {
      prefix = "restored/"
    }
    expiration {
      days = 10
    }
  }
}

locals {
  restoration_notifications_hash_key = "UserId"
}

# in this table it is stored how many ongoing restorations does a user have
resource "aws_dynamodb_table" "restoration_notifications_table" {
  name = "${var.app_name}-RestorationNotifications-${var.aws_region}"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = local.restoration_notifications_hash_key
  attribute {
    name = local.restoration_notifications_hash_key
    type = "S"
  }
}