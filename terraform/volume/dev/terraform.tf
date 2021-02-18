terraform {
  backend "s3" {
    # Replace this with your bucket name!
    bucket         = "terraform-state-emailer"
    key            = "dev/volume/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock-emailer"
    encrypt        = true
  }
}
