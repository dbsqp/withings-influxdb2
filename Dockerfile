ARG ARCH=

# Pull base image
FROM ubuntu:latest

# Labels
LABEL MAINTAINER="https://github.com/dbsqp/"

# Setup external package-sources
RUN apt-get update && apt-get install -y \
    tzdata \
    python3 \
    python3-dev \
    python3-setuptools \
    python3-pip \
    python3-virtualenv \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/* 

# RUN pip install setuptools
#RUN pip3 install pytz influxdb-client oauthlib requests requests-oauth requests_oauthlib typing_extensions arrow withings-api
RUN pip3 install pytz influxdb-client oauthlib requests requests-oauth requests_oauthlib typing_extensions arrow pydantic

# Environment vars
ENV PYTHONIOENCODING=utf-8

# Copy files
RUN mkdir /python_withings_api/
ADD python_withings_api /python_withings_api/
ADD withings2influxdb.py /
ADD get.sh /

# Run
CMD ["/bin/bash","/get.sh"]
