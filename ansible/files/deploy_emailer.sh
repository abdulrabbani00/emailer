#!/bin/bash

cd /home/abdulrab

branch=$1

if [ -z $branch ];
then
    branch=develop
fi

if [ -d "emailer" ]
then
    cd emailer
    git pull origin $branch
else
    git clone --branch $branch git@github.com:abdulrabbani00/emailer.git /home/abdulrab/emailer
fi

pip3 install -r /home/abdulrab/emailer/requirements.txt
