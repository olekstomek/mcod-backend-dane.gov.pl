FROM alpine:3.22.4 AS verify

ENV GNUPGHOME=/tmp/gnupg

RUN set -euxo pipefail \
    && apk add --no-cache gnupg curl \
    && mkdir -p "$GNUPGHOME" \
    && chmod 700 "$GNUPGHOME" \
    && curl -fsSL https://downloads.apache.org/jena/KEYS | gpg --batch --import

WORKDIR /usr/src

COPY ./docker/rdfdb/fuseki/dist/apache-jena-fuseki-6.2.0.tar.gz .
COPY ./docker/rdfdb/fuseki/dist/apache-jena-fuseki-6.2.0.tar.gz.asc .
COPY ./docker/rdfdb/fuseki/dist/apache-jena-fuseki-6.2.0.tar.gz.sha512 .

RUN set -euxo pipefail \
    && sha512sum -c apache-jena-fuseki-6.2.0.tar.gz.sha512 \
    && gpg --verify apache-jena-fuseki-6.2.0.tar.gz.asc apache-jena-fuseki-6.2.0.tar.gz \
    && mkdir -p dist \
    && tar -xzf apache-jena-fuseki-6.2.0.tar.gz -C dist --strip-components=1

FROM eclipse-temurin:21-jre AS runner

ENV FUSEKI_HOME=/opt/fuseki
ENV FUSEKI_BASE=/var/lib/fuseki

RUN useradd -u 10001 -r -s /bin/nologin fuseki

WORKDIR $FUSEKI_HOME

COPY --from=verify /usr/src/dist .

RUN chown -R root:root $FUSEKI_HOME \
    && chmod -R 755 $FUSEKI_HOME

RUN mkdir -p $FUSEKI_BASE/configuration \
    && chown -R fuseki:fuseki $FUSEKI_BASE

COPY ./docker/rdfdb/fuseki/configuration $FUSEKI_BASE/configuration
COPY ./docker/rdfdb/entrypoint.sh /entrypoint.sh

RUN chmod a+x /entrypoint.sh

USER fuseki

ENTRYPOINT ["/entrypoint.sh"]
