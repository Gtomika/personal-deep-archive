terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {} # set dynamically
}

provider "aws" {
  # these credentials do not allow access: for that role must be assumed
  access_key = var.aws_key_id
  secret_key = var.aws_secret_key
  region = var.aws_region

  assume_role {
    role_arn = var.aws_terraform_role_arn
    external_id = var.aws_assume_role_external_id
    duration = "1h"
    session_name = "TerraformSessionPersonalDeepArchive"
  }

  default_tags {
    tags = {
      application = "PersonalDeepArchive"
      managed_by = "Terraform"
      repository = "https://github.com/Gtomika/personal-deep-archive"
      owner = "Tamas Gaspar"
    }
  }
}