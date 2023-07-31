ARG ARCH=

# Pull base image
FROM ubuntu:latest

# Avoid warnings by switching to noninteractive
ARG DEBIAN_FRONTEND=noninteractive

# Labels
LABEL MAINTAINER="https://github.com/dbsqp/"

# Setup external package-sources
RUN apt-get update && apt-get install -y \
    git \
    cron \
    tzdata \
    python3 \
    python3-dev \
    python3-setuptools \
    python3-pip \
    python3-virtualenv \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/* 

# RUN pip install setuptools
RUN pip3 install pytz influxdb-client oauthlib requests requests-oauth requests_oauthlib typing_extensions arrow pydantic==1.10.12

# Environment vars
ENV PYTHONIOENCODING=utf-8

# submodule update
RUN git clone https://github.com/dbsqp/python_withings_api

# Copy files
COPY withings2influxdb.py /
COPY enterypoint.sh /

# Run
CMD ["/bin/bash","/enterypoint.sh"]
