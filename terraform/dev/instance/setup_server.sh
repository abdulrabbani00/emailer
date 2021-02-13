#!/bin/bash

# Make this all ansible
# use ansible vault for secrets

useradd -m abdulrab

apt-get update && apt-get install -y git vim

mkdir /home/abdulrab/.ssh/ && chmod 700 /home/abdulrab/.ssh/

touch /home/abdulrab/test

# Mount the ebs disk

# Get user abdulrab set up
# Add AWS credentials
#/bin/su -c "/path/to/backup_db.sh /tmp/test" - postgres



#aws s3 cp some_tar_ball /home/abdulrab/some_tar_ball
#tar -xzvf /home/abdulrab/some_tar_ball
#
#/home/abdulrab/do_the_rest.sh
#
#COPY --chown=abdulrab docker/config /home/abdulrab/.ssh/config
#COPY --chown=abdulrab docker/id_rsa.pub /home/abdulrab/.ssh/authorized_keys
#COPY --chown=abdulrab id_rsa /home/abdulrab/.ssh/id_rsa
#RUN chmod 400 /home/abdulrab/.ssh/id_rsa
#
#COPY --chown=abdulrab docker/bashrc /home/abdulrab/.bashrc
#
#RUN git clone --depth=1 https://github.com/amix/vimrc.git ~/.vim_runtime
#RUN sh ~/.vim_runtime/install_awesome_vimrc.sh
#
#RUN pip3 install --upgrade pip && \
#    pip3 install --no-cache-dir pandas
#
#########################
##   Clone Application  #
#########################
#
#RUN mkdir /home/abdulrab/emailer
#RUN git clone --branch develop git@github.com:abdulrabbani00/emailer.git /home/abdulrab/emailer
