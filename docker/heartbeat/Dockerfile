FROM docker.elastic.co/beats/heartbeat:6.7.0
COPY ./docker/heartbeat/heartbeat.yml /usr/share/heartbeat/heartbeat.yml
USER root
RUN chown root:heartbeat /usr/share/heartbeat/heartbeat.yml
RUN chmod go-w /usr/share/heartbeat/heartbeat.yml

COPY ./docker/heartbeat/monitors/urls_check.yml /usr/share/heartbeat/monitors.d
COPY ./docker/heartbeat/monitors/containers_check.yml /usr/share/heartbeat/monitors.d
COPY ./docker/heartbeat/monitors/frontend_check.yml /usr/share/heartbeat/monitors.d

RUN chown -R root:heartbeat /usr/share/heartbeat/
RUN chmod go-w /usr/share/heartbeat/monitors.d/*

USER heartbeat