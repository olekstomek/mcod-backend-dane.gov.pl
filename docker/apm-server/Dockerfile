FROM docker.elastic.co/apm/apm-server:6.7.0
COPY ./docker/apm-server/apm-server.yml /usr/share/apm-server/apm-server.yml
USER root
RUN chown root:apm-server /usr/share/apm-server/apm-server.yml
RUN chmod go-w /usr/share/apm-server/apm-server.yml
USER apm-server