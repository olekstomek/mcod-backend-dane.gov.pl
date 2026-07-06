FROM rabbitmq:4.2.5-management-alpine

COPY docker/rabbitmq/rabbitmq.conf /etc/rabbitmq/rabbitmq.conf

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD rabbitmq-diagnostics -q ping || exit 1
