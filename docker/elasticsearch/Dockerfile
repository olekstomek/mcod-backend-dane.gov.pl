FROM docker.elastic.co/elasticsearch/elasticsearch:6.7.0

ADD ./docker/elasticsearch/stopwords.txt /usr/share/elasticsearch/config
RUN mkdir /usr/share/elasticsearch/config/hunspell

ADD ./docker/elasticsearch/hunspell /usr/share/elasticsearch/config/hunspell
RUN /usr/share/elasticsearch/bin/elasticsearch-plugin -s install analysis-stempel
RUN /usr/share/elasticsearch/bin/elasticsearch-plugin -s install analysis-icu

ADD ./docker/elasticsearch/setup-logging.sh /usr/local/bin/setup-logging
RUN chmod 755 /usr/local/bin/setup-logging

