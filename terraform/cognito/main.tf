resource "aws_cognito_user_pool" "personal_archive_user_pool" {
  name = "${var.app_name}-UserPool-${var.aws_region}"
  deletion_protection = "ACTIVE"

  # specify that email can be user to sign in as well
  username_attributes = ["email"]

  # it is auto verified, because admin selects it
  auto_verified_attributes = ["email"]

  # only admin can invite new users
  admin_create_user_config {
    allow_admin_create_user_only = true
    invite_message_template {
      email_subject = var.admin_invite_email_subject
      email_message = var.admin_invite_email_content
      sms_message = "" # seems to be required
    }
  }

  # recover accounts be email or admin action
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
    recovery_mechanism {
      name     = "admin_only"
      priority = 2
    }
  }

  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  password_policy {
    minimum_length = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers = true
    require_symbols = false
    temporary_password_validity_days = 1
  }

  lambda_config {
    post_confirmation = var.user_initializer_lambda_arn
  }
}

# a client represents an application used to access cognito user pool (with log in screen)
resource "aws_cognito_user_pool_client" "web_client" {
  name         = "${var.app_name}-WebClient-${var.aws_region}"
  user_pool_id = aws_cognito_user_pool.personal_archive_user_pool.id

  prevent_user_existence_errors = "ENABLED"
  generate_secret = false
  refresh_token_validity = 90

  # these actions will be enabled in the client
  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH"
  ]

  supported_identity_providers = ["COGNITO"]
}

locals {
  cognito_user_pool_provider_name = "cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.personal_archive_user_pool.id}"
}

resource "aws_cognito_identity_pool" "personal_archive_identity_pool" {
  identity_pool_name = "${var.app_name}-IdentityPool-${var.aws_region}"
  allow_unauthenticated_identities = false
  allow_classic_flow               = false

  # allow users from the user pool to request credentials from this identity pool
  cognito_identity_providers {
    client_id = aws_cognito_user_pool_client.web_client.id
    provider_name = local.cognito_user_pool_provider_name
    server_side_token_check = false
  }
}

data "aws_iam_policy_document" "cognito_user_trust_policy" {
  statement {
    sid = "AllowToBeAssumedByCognitoUser"
    effect = "Allow"
    principals {
      type = "Federated"
      identifiers = ["cognito-identity.amazonaws.com"]
    }
    actions = ["sts:AssumeRoleWithWebIdentity"]
    condition {
      test     = "StringEquals"
      variable = "cognito-identity.amazonaws.com:aud"
      values   = [aws_cognito_identity_pool.personal_archive_identity_pool.id]
    }
    condition {
      test     = "ForAnyValue:StringLike"
      variable = "cognito-identity.amazonaws.com:amr"
      values   = ["authenticated"]
    }
  }
}

# define what a logged in user can do
data "aws_iam_policy_document" "cognito_user_policy" {
  statement {
    sid = "AllowGetOwnObjects"
    effect = "Allow"
    actions = ["s3:GetObject"]
    resources = ["${var.archive_data_bucket_arn}/&{cognito-identity.amazonaws.com:sub}/*"]
  }
  statement {
    sid = "AllowAPutOwnObjectGlacier"
    effect = "Allow"
    actions = ["s3:PutObject"]
    resources = ["${var.archive_data_bucket_arn}/&{cognito-identity.amazonaws.com:sub}/*"]
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-storage-class"
      values   = ["DEEP_ARCHIVE"]
    }
  }
  statement {
    sid = "AllowListOwnS3Prefix"
    effect = "Allow"
    actions = ["s3:ListBucket"]
    resources = [var.archive_data_bucket_arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["&{cognito-identity.amazonaws.com:sub}/*"]
    }
  }
}

resource "aws_iam_role" "authenticated_user_role" {
  name = "${var.app_name}-CognitoUserRole"
  assume_role_policy = data.aws_iam_policy_document.cognito_user_trust_policy.json
}

resource "aws_iam_role_policy" "authenticated_user_role_policy" {
  name = "${var.app_name}-CognitoUserPolicy"
  policy = data.aws_iam_policy_document.cognito_user_policy.json
  role   = aws_iam_role.authenticated_user_role.id
}

resource "aws_cognito_identity_pool_roles_attachment" "cognito_user_role_attachment" {
  identity_pool_id = aws_cognito_identity_pool.personal_archive_identity_pool.id
  # all users get this role
  roles = {
    "authenticated" = aws_iam_role.authenticated_user_role.arn
  }
}

# https://docs.aws.amazon.com/cognito/latest/developerguide/iam-roles.html
# https://stackoverflow.com/questions/62192959/amazon-cognito-identity-id-sub-s3-bucket-name