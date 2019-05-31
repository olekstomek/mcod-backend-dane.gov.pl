#!/usr/bin/env bash

set -e

flag=0
retries=0
max_retries=2
sleep_time=3
while [ $flag -eq 0 ]; do
    if [ $retries -eq $max_retries ]; then
        echo Executed $retries retries, aborting
        exit 1
    fi
    sleep $sleep_time
    if [ "$POSTGRES_HOST_TYPE" == "machine" ]; then
        gunicorn mcod.wsgi --bind 0.0.0.0:8001 --reload --env PYTHONUNBUFFERED=1 -k gevent
    else
        wait-for-it mcod-db:5432 -s --timeout=30 -- gunicorn mcod.wsgi --bind 0.0.0.0:8001 --reload --env PYTHONUNBUFFERED=1 -k gevent
    fi

    if [ $? -eq 0 ]; then
        flag=1
    else
        echo "Cannot start admin panel, retrying in $sleep_time seconds..."
        let retries++
    fi
done
