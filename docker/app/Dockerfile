FROM python:3.8.13

ARG UID=1000
ARG GID=1000
ARG UNAME=mcod

ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/usr/src/mcod_backend/venv

RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository "deb http://deb.debian.org/debian bullseye main contrib non-free"
RUN apt-get update && apt-get install -y --allow-unauthenticated gettext locales libarchive13 libmagickwand-dev libmagickcore-6.q16-3-extra curl dirmngr apt-transport-https lsb-release ca-certificates firefox-esr ffmpeg unrar

RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -

RUN apt-get install -y nodejs

RUN sed -i '/en_GB.UTF-8/s/^# //g' /etc/locale.gen
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen
RUN sed -i '/pl_PL.UTF-8/s/^# //g' /etc/locale.gen
RUN locale-gen

ENV LANG pl_PL.UTF-8
ENV LANGUAGE pl_PL:pl
ENV LC_ALL pl_PL.UTF-8

ENV OPENSSL_CONF /etc/ssl/

RUN npm install -g geckodriver --unsafe-perm

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV PYTHONPATH "${PYTHONPATH}:${VIRTUAL_ENV}:/usr/src/mcod_backend"

RUN groupadd -g $GID -o $UNAME
RUN useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME

WORKDIR /usr/src/mcod_backend

ADD . /usr/src/mcod_backend

COPY ./docker/wait-for-it.sh /usr/local/bin/wait-for-it
RUN chmod +x /usr/local/bin/wait-for-it

COPY ./docker/app/start-api.sh /usr/local/bin/start-api
RUN chmod +x /usr/local/bin/start-api

COPY ./docker/app/start-django.sh /usr/local/bin/start-django
RUN chmod +x /usr/local/bin/start-django

COPY ./docker/app/start-celery.sh /usr/local/bin/start-celery
RUN chmod +x /usr/local/bin/start-celery

RUN pip install -I 'setuptools<58'
RUN pip install -r requirements-common.txt

RUN python manage.py compilemessages --settings mcod.settings.test -v 3

EXPOSE 8001 5678
