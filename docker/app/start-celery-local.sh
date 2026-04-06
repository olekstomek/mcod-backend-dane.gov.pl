#!/usr/bin/env bash
# Celery entrypoint for local environment, adding certificate management.
set -exf

flag=0
retries=0
max_retries=2
sleep_time=3

opts=${CELERY_OPTS}
concurrency=${CELERY_CONCURRENCY:-2}
queues=${CELERY_QUEUES:-default,resources,indexing,indexing_data,periodic,newsletter,notifications,search_history,watchers,harvester,history,graphs,datasets,archiving,reports,discourse,showcases}
rabbitmq_host=${RABBITMQ_HOST:-mcod-rabbitmq:5672}

install_certs=${CELERY_INSTALL_CERTIFICATES:-0}
certs_path=${CELERY_INSTALL_CERTIFICATES_PATH:-"/usr/src/mcod_backend/mcod.local.pem"}
if [ $install_certs -eq 1 ]; then
  echo "Installing local SSL certificates for Celery->API communication"
  python manage.py configure_nginx_certs $certs_path
fi


while [ $flag -eq 0 ]; do
    if [ $retries -eq $max_retries ]; then
        echo Executed $retries retries, aborting
        exit 1
    fi
    sleep $sleep_time
    wait-for-it $rabbitmq_host -s --timeout=30 -- celery --app=mcod.celeryapp:app worker -l INFO -Q $queues --concurrency=$concurrency $opts
    if [ $? -eq 0 ]; then
        flag=1
    else
        echo "Cannot start celery, retrying in $sleep_time seconds..."
        let retries++
    fi
done
