provider "aws" {
  profile = "default"
  region  = "us-east-1"
}

resource "aws_ebs_volume" "emailer_persistant" {
  availability_zone = "us-east-1a"
  size              = 30

  tags = {
    Name = var.name,
    Snapshot = var.snapshot
  }
}

output "emailer_persistant" {
  value = aws_ebs_volume.emailer_persistant
}
