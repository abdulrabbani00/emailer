# Emailer

This project will allow users to send a formatted email to a specified Gmail account, which contains a body of code.
This application will then parse the email, extract the code, run the code, and respond with an ouput.
There will be full support for the following languages:
- Python
- C
- C++
- Rust
- Bash
- Golang

# Infrastructure
The infrastructure seen in this repository is used creating Terraform. Users can easily fork the code and stand up their own infrastructure as well.
More instructions on how to do this will be provided soon.

# CI/CD
This code is integrated with Travis. The code will automatically be tested with each commit. It will also be deployed to a Lambda function on AWS. Furthermore, a bash script will be called on the server that is hosting this code.