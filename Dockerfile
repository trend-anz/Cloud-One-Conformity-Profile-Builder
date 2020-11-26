FROM ubuntu:18.04

RUN apt update
# Basics
RUN apt install -y vim

# Tools
## PYTHON
RUN apt install -y python-pip
RUN apt install -y python3-pip
## PYJQ deps
RUN apt install -y build-essential
RUN apt install -y automake autoconf libtool

ENV TOOL_PATH=/opt/cpb
COPY cpb ${TOOL_PATH}
COPY requirements.txt ${TOOL_PATH}/requirements.txt
RUN pip3 install -r ${TOOL_PATH}/requirements.txt
