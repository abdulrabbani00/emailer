provider "aws" {
  profile = "default"
  region  = "us-east-1"
}

data "terraform_remote_state" "emailer_volume" {
  backend = "s3"
  config = {
    bucket         = "terraform-state-emailer"
    key            = "${var.environment}/volume/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock-emailer"
    encrypt        = true
  }
}


data "terraform_remote_state" "iam_profile" {
  backend = "s3"
  config = {
    bucket         = "terraform-state-emailer"
    key            = "shared/iam/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock-emailer"
    encrypt        = true
  }
}

resource "aws_volume_attachment" "emailer_persistant_attachment" {
  device_name = "/dev/xvdb"
  volume_id   = data.terraform_remote_state.emailer_volume.outputs.emailer_persistant.id
  instance_id = aws_instance.emailer_instance.id
}

resource "aws_instance" "emailer_instance" {
  ami           = "ami-0b493722cea9f95f6" # us-west-2
  instance_type = var.instance_type
  #aiam = "ec2-read-role"
  iam_instance_profile = data.terraform_remote_state.iam_profile.outputs.iam_instance_profile.name
  availability_zone = "us-east-1a"
  key_name = "admin_emailer_rsa"
  vpc_security_group_ids = ["sg-00a0a79dd235057f6"]
  tags = {
    Name = var.name
    AUTO_DNS_ZONE = var.zone_id
    AUTO_DNS_NAME = "${var.name}.abdulrabbani.com"
  }

  root_block_device {
    volume_size = 15
  }
}

resource "aws_route53_record" "emailer_dns" {
  zone_id = var.zone_id
  name    = "${var.name}.abdulrabbani.com"
  type    = "A"
  ttl     = "300"
  records = [aws_instance.emailer_instance.public_ip]
  lifecycle {
    ignore_changes = [records]
  }

}

resource "null_resource" "ansible" {
  provisioner "local-exec" {
    command = "cd ../../../ansible/; sleep 90; ansible-playbook -i ${aws_route53_record.emailer_dns.name}, setup_emailer_instance.yml"
  }
}

output "volume_data" {
  value = data.terraform_remote_state.emailer_volume.outputs.emailer_persistant.id
}
