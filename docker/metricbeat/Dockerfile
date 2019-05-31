FROM docker.elastic.co/beats/metricbeat:6.7.0
COPY ./docker/metricbeat/metricbeat.yml /usr/share/metricbeat/metricbeat.yml
USER root
RUN mkdir /hostfs
RUN chown root:metricbeat /usr/share/metricbeat/metricbeat.yml
RUN chmod go-w /usr/share/metricbeat/metricbeat.yml

RUN metricbeat modules enable system
RUN metricbeat modules enable redis
RUN metricbeat modules enable elasticsearch
RUN metricbeat modules enable postgresql
RUN metricbeat modules enable rabbitmq
RUN metricbeat modules enable logstash

COPY ./docker/metricbeat/modules/system.yml /usr/share/metricbeat/modules.d
COPY ./docker/metricbeat/modules/redis.yml /usr/share/metricbeat/modules.d
COPY ./docker/metricbeat/modules/elasticsearch.yml /usr/share/metricbeat/modules.d
COPY ./docker/metricbeat/modules/postgresql.yml /usr/share/metricbeat/modules.d
COPY ./docker/metricbeat/modules/rabbitmq.yml /usr/share/metricbeat/modules.d
COPY ./docker/metricbeat/modules/logstash.yml /usr/share/metricbeat/modules.d

RUN chown -R root:metricbeat /usr/share/metricbeat/
RUN chmod go-w /usr/share/metricbeat/modules.d/*
