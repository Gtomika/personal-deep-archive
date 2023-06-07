resource "aws_s3_bucket" "archive_storage_bucket" {
  bucket = "${lower(var.app_name)}-archive-data-${var.aws_region}"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "archival_versioning" {
  bucket = aws_s3_bucket.archive_storage_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

data "aws_iam_policy_document" "archive_bucket_policy_doc" {
  statement {
    sid = "DenyObjectDeletions"
    effect = "Deny"
    actions = ["s3:DeleteObject"]
    principals {
      type = "*"
      identifiers = ["*"]
    }
    resources = ["${aws_s3_bucket.archive_storage_bucket.arn}/*"]
  }
}

resource "aws_s3_bucket_policy" "archive_bucket_policy" {
  bucket = aws_s3_bucket.archive_storage_bucket.id
  policy = data.aws_iam_policy_document.archive_bucket_policy_doc.json
}

