FROM python:slim-buster

########################
#  User Set Up         #
########################
RUN useradd -m abdulrab

RUN apt-get update && apt-get install -y \
    git \
    vim

USER abdulrab

RUN mkdir /home/abdulrab/.ssh/ && chmod 700 /home/abdulrab/.ssh/

COPY --chown=abdulrab docker/config /home/abdulrab/.ssh/config
COPY --chown=abdulrab docker/id_rsa.pub /home/abdulrab/.ssh/authorized_keys
COPY --chown=abdulrab id_rsa /home/abdulrab/.ssh/id_rsa
RUN chmod 400 /home/abdulrab/.ssh/id_rsa

COPY --chown=abdulrab docker/bashrc /home/abdulrab/.bashrc

RUN git clone --depth=1 https://github.com/amix/vimrc.git ~/.vim_runtime
RUN sh ~/.vim_runtime/install_awesome_vimrc.sh

RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir pandas

########################
#   Clone Application  #
########################

RUN mkdir /home/abdulrab/emailer
RUN git clone --branch develop git@github.com:abdulrabbani00/emailer.git /home/abdulrab/emailer
