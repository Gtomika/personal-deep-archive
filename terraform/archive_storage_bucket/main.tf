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