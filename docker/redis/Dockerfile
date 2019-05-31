FROM redis:3.2

RUN mkdir /var/log/redis

COPY ./docker/redis/redis.conf /usr/local/etc/redis.conf
CMD [ "redis-server", "/usr/local/etc/redis.conf" ]