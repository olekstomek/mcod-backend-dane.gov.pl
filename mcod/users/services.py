import logging
from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import uuid4
from xml.etree.ElementTree import fromstring

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.cache import KEY_PREFIX
from django.core.cache import caches
from django.db.models import QuerySet
from logingovpl.mixins import ACSMixin, LogoutMixin
from logingovpl.objects import LoginGovPlUser
from logingovpl.services import decode_cipher_value
from logingovpl.statuses import SUCCESS
from logingovpl.utils import get_in_response_to, get_name_id, get_session_id, get_user, xml_ns

from mcod import settings
from mcod.lib.triggers import session_store
from mcod.users.constants import (
    LOGINGOVPL_PROCESS,
    LOGINGOVPL_REQUEST_ID_SEPARATOR,
    LOGINGOVPL_UNKNOWN_USER_IDENTIFIER,
)
from mcod.users.exceptions import SAMLArtException

User = get_user_model()
logger = logging.getLogger("mcod")


@dataclass
class LoginGovPlData:
    """Class representing data obtained from the login.gov.pl service."""

    user: LoginGovPlUser  # login.gov.pl user data
    name_id: str  # login.gov.pl user login
    in_response_to: str  # authn_request_id prepared and sent from the backend
    session_id: str  # login.gov.pl session identifier


class UserService:
    model = User

    def get_user_by_authn_request_id_or_none(self, authn_request_id: str) -> Optional[User]:
        """Get the user object from the authorization request id sent to
        the login.gov.pl service in the AuthnRequest.xml in the field `ID`.

        If user cannot be found in sessions, then return `None`.
        """
        logingovpl_user_id = authn_request_id.split(LOGINGOVPL_REQUEST_ID_SEPARATOR)[-1]
        session_caches = caches[settings.SESSION_CACHE_ALIAS]
        for session_cache in session_caches.keys("*"):
            session_key = session_cache[len(KEY_PREFIX) :]
            session_items = list(session_store(session_key).items())
            if session_items:
                session_user_id = session_items[0][1]
                if session_user_id == logingovpl_user_id:
                    return self.model.objects.get(pk=int(session_user_id))
        return None

    def get_last_user_by_pesel_or_none(self, pesel: str) -> Optional[User]:
        """Get the last created active user (not blocked or permanently blocked) by
        the given PESEL number.

        If user cannot found, then return `None`.
        """
        users: QuerySet = self.model.objects.filter(
            pesel=pesel,
            state="active",
            is_active=True,
            is_removed=False,
            is_permanently_removed=False,
        ).order_by("created")
        if not users:
            return None

        return users.last()

    @staticmethod
    def link_to_logingovpl(user: User, pesel: str) -> None:
        """Update user fields due to the process of linking to the login.gov.pl service."""
        user.pesel = pesel
        user._pesel = pesel
        user.save()
        logger.info(f"Updated PESEL for user `{user.email}`.")

    @staticmethod
    def unlink_from_logingovpl(user: User) -> None:
        """Remove pesel from the user due to the process of unlinking from the login.gov.pl service."""
        user.pesel = None
        user.save()
        logger.info(f"Pesel from user `{user}` has been removed.")

    @staticmethod
    def get_user_to_switch_or_none(actual_user: User, email_to_switch: str) -> Optional[User]:
        """Get user object with the given `email_to_switch`, connected with the given `actual_user.`

        If new user cannot be find, than return `None`.
        """
        new_user = [obj for obj in actual_user.connected_gov_users if obj.email == email_to_switch]
        if not new_user:
            return None
        return new_user[0]


class LoginGovPlService(ACSMixin, LogoutMixin):
    """Logingovpl service."""

    @staticmethod
    def _get_status_code_from_saml(content: str) -> Tuple[str, str]:
        """Parse SAML content and get status code and message from it."""
        tree = fromstring(content)
        try:
            elem_status_code = tree.find(".//saml2p:ArtifactResponse/saml2p:Status/saml2p:StatusCode", xml_ns)
            status_code = elem_status_code.attrib.get("Value")
        except AttributeError:
            elem_status_code = tree.find(".//saml2p:Status/saml2p:StatusCode", xml_ns)
            status_code = elem_status_code.attrib.get("Value")

        elem_status_message = tree.find(".//saml2p:Status/saml2p:StatusMessage", xml_ns)
        status_message = elem_status_message.text if elem_status_message is not None else None
        return status_code, status_message

    def prepare_authn_request_id(self, user_id: Optional[int] = None) -> str:
        """Prepare the authorization request identifier to the login.gov.pl service.

        If the frontend requests with the user set in session and apiauthtoken cookies, we assume that
        it is a process of a linking to the login.gov.pl service from the logged user account.
        Otherwise, we assume that we are in the logging process of a new user.

        Example of the identifier: "ID-971bc12f-972d-4648-995d-3254b12ddd47-LINK-50765"
        """

        logingovpl_process = LOGINGOVPL_PROCESS.LOGIN.value if user_id is None else LOGINGOVPL_PROCESS.LINK.value
        user_identifier = LOGINGOVPL_UNKNOWN_USER_IDENTIFIER if user_id is None else str(user_id)
        return (
            "ID"
            + LOGINGOVPL_REQUEST_ID_SEPARATOR
            + str(uuid4())
            + LOGINGOVPL_REQUEST_ID_SEPARATOR
            + logingovpl_process
            + LOGINGOVPL_REQUEST_ID_SEPARATOR
            + user_identifier
        )

    @staticmethod
    def get_process_or_none_from_authn_request_id(
        authn_request_id: str,
    ) -> Optional[LOGINGOVPL_PROCESS]:
        """Get the logingovpl process type from the `InResponseTo` field of the SAML artifact
        response (LOGIN/LINK), which is previously prepared during preparing SAML artifact to
        the login.gov.pl service.

        If found process text not exists in the `LOGINGOVPL_PROCESS` constant, return `None`.
        """

        process_text = authn_request_id.split(LOGINGOVPL_REQUEST_ID_SEPARATOR)[-2]
        try:
            process = LOGINGOVPL_PROCESS(process_text)
        except ValueError:
            logger.error(f"Logingovpl process not found in authn_request_id `{authn_request_id}`.")
            return None
        return process

    def get_saml_assertion_status(self, content: str) -> Tuple[str, str]:
        """SAML assertion method. Gets status code and message from logingovpl response."""
        status_code: str
        message: str
        status_code, message = self._get_status_code_from_saml(content)

        return status_code, message

    @staticmethod
    def get_data_from_saml_art(saml_art: bytes) -> LoginGovPlData:
        """Get decoded data from the SAML Artifact Response of the login.gov.pl serviece."""
        decoded_content = decode_cipher_value(saml_art)

        return LoginGovPlData(
            user=get_user(decoded_content),
            name_id=get_name_id(decoded_content),
            in_response_to=get_in_response_to(decoded_content),
            session_id=get_session_id(decoded_content),
        )

    def logout_session(self, session_id: str, name_id: str) -> None:
        self.login_gov_logout(session_id, name_id)

    def get_logingovpl_data_and_logout(self, request_data: dict, is_logingovpl_mocked: bool) -> LoginGovPlData:
        """Get data from the login.gov.pl POST request to the endpoint /idp,
        and logout from the login.gov.pl service.

        If `is_logingovpl_mocked` is `True`,
        then request data are from the template mocking the login.gov.pl service.

        Raises `SAMLArtException` in case of not obtaining user data from
        the ArtifactResolve response.
        """

        if is_logingovpl_mocked:

            return LoginGovPlData(
                user=LoginGovPlUser(
                    request_data["first_name"],
                    request_data["last_name"],
                    request_data["dob"],
                    request_data["pesel"],
                ),
                name_id=request_data["in_response_to"],
                in_response_to=request_data["in_response_to"],
                session_id="test_logingovpl_ID_session",
            )

        response = self.resolve_artifact(request_data["SAMLart"])
        status_code, message = self._get_status_code_from_saml(response.content)

        if status_code != SUCCESS:
            logger.error(f"SAML Artifact not resolved: `{status_code}` `{message}`")
            raise SAMLArtException(message)

        decoded_content = decode_cipher_value(response.content)
        logingovpl_user = get_user(decoded_content)
        name_id = get_name_id(decoded_content)
        in_response_to = get_in_response_to(decoded_content)
        session_id = get_session_id(decoded_content)

        self.logout_session(session_id, name_id)
        return LoginGovPlData(user=logingovpl_user, name_id=name_id, in_response_to=in_response_to, session_id=session_id)


logingovpl_service: LoginGovPlService = LoginGovPlService()
user_service: UserService = UserService()
