#Build ARGS
ARG ARCH=

# Pull base image
FROM python:3.10-slim-bullseye

# Labels
LABEL MAINTAINER="Ole Kristian Hoel <okhoel@gmail.com>"

# RUN pip install
RUN pip3 install requests python-dateutil influxdb influxdb_client yacron

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