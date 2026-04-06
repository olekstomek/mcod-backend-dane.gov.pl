import logging
import uuid

import requests
from django.conf import settings
from django.template.loader import render_to_string

from .services import add_sign
from .utils import get_issue_instant

requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ":HIGH:!DH:!aNULL"

try:
    requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ":HIGH:!DH:!aNULL"
except AttributeError:
    # no pyopenssl support used / needed / available
    pass

logger = logging.getLogger(__name__)


class ACSMixin:
    def resolve_artifact(self, saml_art):
        xml = render_to_string(
            "ArtifactResolve.xml",
            {
                "artifact_resolve_issue_instant": get_issue_instant(),
                "artifact_resolve_artifact": saml_art,
                "issuer": settings.LOGINGOVPL_ISSUER,
            },
        )

        signed = add_sign(
            xml,
            settings.LOGINGOVPL_ENC_KEY,
            settings.LOGINGOVPL_ENC_CERT,
        )

        try:
            response = requests.post(
                settings.LOGINGOVPL_ARTIFACT_RESOLVE_URL,
                data=signed,
                timeout=settings.LOGINGOVPL_TIMEOUT,
            )
        except requests.RequestException:
            logger.exception("ArtifactResolve service request failed:")
            raise

        return response


class LogoutMixin:
    def get_signed_logout_request(self, session_id, name_id):
        xml = render_to_string(
            "AuthnLogoutRequest.xml",
            {
                "session_id": session_id,
                "name_id": name_id,
                "authn_request_id": "ID-{}".format(uuid.uuid4()),
                "authn_request_issue_instant": get_issue_instant(),
                "issuer": settings.LOGINGOVPL_ISSUER,
                "sl_url": settings.LOGINGOVPL_SL_URL,
            },
        )
        return add_sign(
            xml,
            settings.LOGINGOVPL_ENC_KEY,
            settings.LOGINGOVPL_ENC_CERT,
        )

    def login_gov_logout(self, session_id, name_id):
        request_body = self.get_signed_logout_request(session_id, name_id)
        headers = {"content-type": "text/xml"}
        url = settings.LOGINGOVPL_SL_URL
        try:
            response = requests.post(url, data=request_body, headers=headers)
        except Exception:
            logger.exception("SingleLogout service request failed:")
            raise
        return response
