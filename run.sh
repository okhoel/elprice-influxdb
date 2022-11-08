#!/bin/bash

if [ -z "$PRICE_DATE$PRICE_WEEK$PRICE_MONTH" ];
then
    echo "Setting up scheduled run of elprice.py"
    yacron -c /crontab.yaml
else
    echo "Starting one time run of elprice.py"
    python3 /elprice.py
fi

if [ "${DEBUG,,}" = "true" ]; #DEBUG converted to lowercase
then
    echo "Keep container from stopping while debugging"
    while :
        do
            sleep 60
        done
fi
