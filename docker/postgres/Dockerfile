FROM postgres:17-trixie

ADD ./docker/postgres/postgresql.conf /etc/postgresql
RUN chmod 644 /etc/postgresql/postgresql.conf

CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
