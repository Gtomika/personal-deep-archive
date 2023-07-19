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

resource "aws_s3_bucket_accelerate_configuration" "archival_accelerate" {
  bucket = aws_s3_bucket.archive_storage_bucket.id
  status = "Enabled" //or "Suspended"
}

data "aws_iam_policy_document" "archive_bucket_policy_doc" {
  statement {
    sid = "DenyObjectDeletions"
    effect = "Deny"
    actions = ["s3:DeleteObject"]
    not_principals {
      type = "AWS"
      identifiers = ["arn:aws:iam::844933496707:user/gaspar-tamas-iam"]
    }
    resources = ["${aws_s3_bucket.archive_storage_bucket.arn}/*"]
  }
}

resource "aws_s3_bucket_policy" "archive_bucket_policy" {
  bucket = aws_s3_bucket.archive_storage_bucket.id
  policy = data.aws_iam_policy_document.archive_bucket_policy_doc.json
}

