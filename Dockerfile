# Pull base image
FROM python:3.10-slim-bullseye as base

# Labels
LABEL MAINTAINER="Ole Kristian Hoel <okhoel@gmail.com>"

#Build ARGS
ARG TARGETARCH
RUN echo "Arch: $TARGETARCH"

# Install gcc for arm
FROM base as install-arm
RUN apt-get update && apt-get install python3-dev gcc -y --no-install-recommends && rm -rf /var/lib/apt/lists/*

# No special installation for amd64
FROM base as install-amd64

#Install python modules
FROM install-${TARGETARCH} as final
RUN pip3 install requests python-dateutil influxdb_client --no-cache-dir
RUN pip3 install yacron --no-cache-dir

# Copy files
ADD elprice.py /
ADD crontab.yaml /
ADD run.sh / 

# Chmod
RUN chmod 755 /run.sh
RUN chmod 755 /elprice.py
RUN chmod 644 /crontab.yaml

# Environment vars
ENV PYTHONIOENCODING=utf-8

# Run
CMD ["/bin/bash","/run.sh"]