#  BSD 3-Clause License
#
#  Copyright (c) 2019, Elasticsearch BV
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  * Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import logging
from functools import partial

from django.apps import AppConfig
from django.conf import settings as django_settings
from elasticapm.conf import constants
from elasticapm.utils.disttracing import TraceParent

from mcod.apm.client import get_client

logger = logging.getLogger("elasticapm.traces")

ERROR_DISPATCH_UID = "elasticapm-exceptions"
REQUEST_START_DISPATCH_UID = "elasticapm-request-start"
REQUEST_FINISH_DISPATCH_UID = "elasticapm-request-stop"

TRACEPARENT_HEADER_NAME_WSGI = "HTTP_" + constants.TRACEPARENT_HEADER_NAME.upper().replace("-", "_")


class ElasticAPMConfig(AppConfig):
    name = "mcod.apm"
    label = "mcod.apm"
    verbose_name = "ElasticAPM"

    def __init__(self, *args, **kwargs):
        super(ElasticAPMConfig, self).__init__(*args, **kwargs)
        self.client = None

    def ready(self):
        self.client = get_client()
        register_handlers(self.client)
        if self.client.config.instrument:
            instrument(self.client)
        else:
            self.client.logger.debug("Skipping instrumentation. INSTRUMENT is set to False.")


def register_handlers(client):
    from django.core.signals import got_request_exception, request_started, request_finished
    from mcod.apm.handlers import exception_handler

    # Connect to Django's internal signal handlers
    got_request_exception.disconnect(dispatch_uid=ERROR_DISPATCH_UID)
    got_request_exception.connect(partial(exception_handler, client), dispatch_uid=ERROR_DISPATCH_UID, weak=False)

    request_started.disconnect(dispatch_uid=REQUEST_START_DISPATCH_UID)
    request_started.connect(
        partial(_request_started_handler, client), dispatch_uid=REQUEST_START_DISPATCH_UID, weak=False
    )

    request_finished.disconnect(dispatch_uid=REQUEST_FINISH_DISPATCH_UID)
    request_finished.connect(
        lambda sender, **kwargs: client.end_transaction() if _should_start_transaction(client) else None,
        dispatch_uid=REQUEST_FINISH_DISPATCH_UID,
        weak=False,
    )


def _request_started_handler(client, sender, *args, **kwargs):
    if not _should_start_transaction(client):
        return
    # try to find trace id
    traceparent_header = None
    if "environ" in kwargs:
        traceparent_header = kwargs["environ"].get(TRACEPARENT_HEADER_NAME_WSGI)
    elif "scope" in kwargs:
        # TODO handle Django Channels
        traceparent_header = None
    if traceparent_header:
        trace_parent = TraceParent.from_string(traceparent_header)
        logger.debug("Read traceparent header %s", traceparent_header)
    else:
        trace_parent = None
    client.begin_transaction("request", trace_parent=trace_parent)


def instrument(client):
    """
    Auto-instruments code to get nice spans
    """
    from elasticapm.instrumentation.control import instrument

    instrument()


def _should_start_transaction(client):
    middleware_attr = "MIDDLEWARE" if getattr(django_settings, "MIDDLEWARE", None) is not None else "MIDDLEWARE_CLASSES"
    middleware = getattr(django_settings, middleware_attr)
    return (
            (not django_settings.DEBUG or client.config.debug)
            and middleware
            and "mcod.apm.middleware.TracingMiddleware" in middleware
    )