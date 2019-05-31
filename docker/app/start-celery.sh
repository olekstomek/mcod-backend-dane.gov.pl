#!/usr/bin/env bash

set -e

flag=0
retries=0
max_retries=2
sleep_time=3

concurency=${CELERY_CONCURENCY:-2}

while [ $flag -eq 0 ]; do
    if [ $retries -eq $max_retries ]; then
        echo Executed $retries retries, aborting
        exit 1
    fi
    sleep $sleep_time
    wait-for-it mcod-rabbitmq:5672 -s --timeout=30 -- celery --app=mcod.celeryapp:app worker -B -l INFO --concurrency=$concurency
    if [ $? -eq 0 ]; then
        flag=1
    else
        echo "Cannot start celery, retrying in $sleep_time seconds..."
        let retries++
    fi
done
