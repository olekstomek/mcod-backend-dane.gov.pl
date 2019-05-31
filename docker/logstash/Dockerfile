FROM docker.elastic.co/logstash/logstash:6.7.0
USER root
RUN rm -f /usr/share/logstash/pipeline/logstash.conf
ADD ./docker/logstash/pipeline/ /usr/share/logstash/pipeline/
ADD ./docker/logstash/config/ /usr/share/logstash/config/
RUN chown -R logstash:logstash /usr/share/logstash

USER logstash
RUN /usr/share/logstash/bin/logstash-plugin install logstash-input-udp
RUN /usr/share/logstash/bin/logstash-plugin install logstash-filter-drop