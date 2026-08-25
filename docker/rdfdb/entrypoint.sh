#!/bin/bash
set -euo pipefail

umask 077

mkdir -p "$FUSEKI_BASE"

: "${SPARQL_USER:?}"
: "${SPARQL_PASSWORD:?}"

PASSWD_FILE="$FUSEKI_BASE/passwd"
echo "${SPARQL_USER}:${SPARQL_PASSWORD}" > "$PASSWD_FILE"

echo "Start Fuseki..."
exec "$FUSEKI_HOME/fuseki-server" \
      --passwd="$PASSWD_FILE" \
      "$@"
