#!/bin/bash

# This script will be run prior to commiting any code

cp src/lamda_handler.py terraform/lambda/dev/lamda_handler.py
cd terraform/lambda/dev/
pip3 install -r ../../../requirements.txt -t emailer_trigger_code/
cd emailer_trigger_code
zip -r ../my-deployment-package.zip .
cd ../
zip -g my-deployment-package.zip lamda_handler.py
rm lamda_handler.py
