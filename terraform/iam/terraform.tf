terraform {
  backend "s3" {
    # Replace this with your bucket name!
    bucket         = "terraform-state-emailer"
    key            = "shared/iam/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock-emailer"
    encrypt        = true
  }
}
