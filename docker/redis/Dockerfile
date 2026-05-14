FROM redis:8.4.2-trixie

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
 CMD redis-cli ping | grep PONG || exit 1
