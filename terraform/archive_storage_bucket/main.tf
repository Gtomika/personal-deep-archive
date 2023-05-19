resource "aws_s3_bucket" "archive_storage_bucket" {
  bucket = "${lower(var.app_name)}-archive-data-${var.aws_region}"
}

resource "aws_s3_bucket_versioning" "archival_versioning" {
  bucket = aws_s3_bucket.archive_storage_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}