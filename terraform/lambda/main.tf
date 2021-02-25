provider "aws" {
  profile = "default"
  region  = "us-east-1"
}

data "terraform_remote_state" "lambda_role" {
  backend = "s3"
  config = {
    bucket         = "terraform-state-emailer"
    key            = "shared/iam/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock-emailer"
    encrypt        = true
  }
}

resource "aws_lambda_function" "lamda_trigger_emailer" {
  filename      = "my-deployment-package.zip"
  function_name = "${var.environment}_emailer_trigger"
  role = data.terraform_remote_state.lambda_role.outputs.iam_for_lambda.arn
  handler       = "emailer.lambda_handler"

  # The filebase64sha256() function is available in Terraform 0.11.12 and later
  # For Terraform 0.11.11 and earlier, use the base64sha256() function and the file() function:
  # source_code_hash = "${base64sha256(file("lambda_function_payload.zip"))}"
  #source_code_hash = filebase64sha256("emailer_trigger_code")

  runtime = "python3.7"

  environment {
    variables = {
      foo = "bar"
    }
  }
}
