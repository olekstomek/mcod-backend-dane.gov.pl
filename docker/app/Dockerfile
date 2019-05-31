FROM python:3.6

ARG REQ_FILE=requirements-common.txt
ARG UID=1000
ARG GID=1000
ARG UNAME=mcod

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/usr/src/mcod_backend"

RUN groupadd -g $GID -o $UNAME
RUN useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME

WORKDIR /usr/src/mcod_backend

ADD . /usr/src/mcod_backend

RUN apt-get update && apt-get install -y --allow-unauthenticated gettext phantomjs libarchive13

COPY ./docker/wait-for-it.sh /usr/local/bin/wait-for-it
RUN chmod +x /usr/local/bin/wait-for-it

COPY ./docker/app/start-api.sh /usr/local/bin/start-api
RUN chmod +x /usr/local/bin/start-api

COPY ./docker/app/start-admin.sh /usr/local/bin/start-admin
RUN chmod +x /usr/local/bin/start-admin

COPY ./docker/app/start-celery.sh /usr/local/bin/start-celery
RUN chmod +x /usr/local/bin/start-celery

COPY ./docker/app/run-tests.sh /usr/local/bin/run-tests
RUN chmod +x /usr/local/bin/run-tests

RUN pip install -r ${REQ_FILE}

RUN python manage.py compilemessages --settings mcod.settings.test -v 3

EXPOSE 8000 8001
