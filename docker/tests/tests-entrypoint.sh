#!/usr/bin/env sh
set -exf

find . -name '*.pyc' -delete

: "${COMPONENT:?COMPONENT environment variable is required}"
: "${PYTEST_MARKERS:?PYTEST_MARKERS environment variable is required}"

python manage.py compilemessages --settings mcod.settings.test -v 3
python manage.py makemigrations --check --settings mcod.settings.test

exec pytest -m "$PYTEST_MARKERS" "$@"
