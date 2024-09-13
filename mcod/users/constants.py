from enum import Enum

from django.conf import settings


class LOGINGOVPL_PROCESS(Enum):
    """The type of process related to linking/logging by the login.gov.pl service."""

    LOGIN = "LOGIN"
    LINK = "LINK"


class LOGINGOVPL_ACTION(Enum):
    """Actions about success/failure of linking to/unlinking from/login to
    the login.gov.pl service. The value is the URL built for the frontend needs.
    """

    LINK_SUCCESS = settings.FRONTEND_BASE_URL + "/user/dashboard/desktop" + "?logingovpl=link-success"
    LINK_ERROR = settings.FRONTEND_BASE_URL + "/user/dashboard/desktop" + "?logingovpl=link-error"
    UNLINK_SUCCESS = settings.FRONTEND_BASE_URL + "/user/dashboard/desktop" + "?logingovpl=unlink-success"
    UNLINK_ERROR = settings.FRONTEND_BASE_URL + "/user/dashboard/desktop" + "?logingovpl=unlink-error"
    LOGIN_SUCCESS = settings.FRONTEND_BASE_URL + "/user/dashboard/desktop" + "?logingovpl=login-success"
    LOGIN_ERROR = settings.FRONTEND_BASE_URL + "/user/logingovpl-error" + "?logingovpl=login-error"
    SWITCH_SUCCESS = settings.FRONTEND_BASE_URL + "/user/dashboard/desktop" + "?logingovpl=switch-success"
    SWITCH_ERROR = settings.FRONTEND_BASE_URL + "/user/dashboard/desktop" + "?logingovpl=switch-error"
    UNKNOWN = settings.FRONTEND_BASE_URL + "/idp-unknown-error"


LOGINGOVPL_REQUEST_ID_SEPARATOR = "-"
LOGINGOVPL_UNKNOWN_USER_IDENTIFIER = "UNKNOWN"
