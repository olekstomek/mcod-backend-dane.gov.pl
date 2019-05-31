FROM vault:1.1.0

RUN apk --no-cache add shadow

COPY ./docker/vault/unlock.sh /usr/local/bin/unlock
COPY ./docker/vault/get-keys.sh /usr/local/bin/get-keys
RUN chmod +x /usr/local/bin/unlock
RUN chmod +x /usr/local/bin/get-keys

RUN mkdir -p /vault/secrets
RUN mkdir -p /vault/policies

VOLUME /vault/secrets
VOLUME /vault/policies

COPY ./docker/vault/policy.hcl /vault/policies/policy.hcl
COPY ./docker/vault/config.hcl /vault/config/config.hcl

HEALTHCHECK --interval=10s --timeout=3s CMD /usr/local/bin/unlock
