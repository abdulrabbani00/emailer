provider "aws" {
  profile = "default"
  region  = "us-east-1"
}

data "terraform_remote_state" "emailer_volume" {
  backend = "s3"
  config = {
    bucket         = "terraform-state-emailer"
    key            = "dev/volume/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock-emailer"
    encrypt        = true
  }
}

resource "aws_iam_instance_profile" "iam_read_profile" {
  name  = "ec2-read-roleprofile"
  role = "ec2-role-read"
}

resource "aws_volume_attachment" "emailer_persistant_attachment" {
  device_name = "/dev/xvdb"
  volume_id   = data.terraform_remote_state.emailer_volume.outputs.emailer_persistant.id
  instance_id = aws_instance.emailer_instance.id
}

resource "aws_instance" "emailer_instance" {
  ami           = "ami-0b493722cea9f95f6" # us-west-2
  instance_type = "t2.micro"
  #aiam = "ec2-read-role"
  iam_instance_profile = aws_iam_instance_profile.iam_read_profile.name
  availability_zone = "us-east-1a"
  key_name = "admin_emailer_rsa"
  vpc_security_group_ids = ["sg-00a0a79dd235057f6"]
  tags = {
    Name = "emailer-instance-test-1"
  }

  root_block_device {
    volume_size = 30
  }
}

resource "null_resource" "ansible" {
  provisioner "local-exec" {
    command = "cd ../../../ansible/; sleep 30; ansible-playbook -i ${aws_instance.emailer_instance.public_dns}, setup_emailer_instance.yml"
  }
}

output "volume_data" {
  value = "${data.terraform_remote_state.emailer_volume.outputs.emailer_persistant.id}"
}
