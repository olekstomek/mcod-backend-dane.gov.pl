import datetime
import random
import string

from defusedxml.lxml import fromstring

from .objects import LoginGovPlUser

xml_ns = {"saml2": "urn:oasis:names:tc:SAML:2.0:assertion", "saml2p": "urn:oasis:names:tc:SAML:2.0:protocol"}


def get_issue_instant():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def get_relay_state(size=16):
    allowed_chars = string.ascii_letters + string.digits
    return "".join(random.choice(allowed_chars) for x in range(size))  # noqa


def get_status_code(content):
    tree = fromstring(content)
    try:
        elem_attrib = tree.find(".//saml2p:Response/saml2p:Status/saml2p:StatusCode/saml2p:StatusCode", xml_ns).attrib  # noqa
    except AttributeError:
        elem_attrib = tree.find(".//saml2p:Response/saml2p:Status/saml2p:StatusCode", xml_ns).attrib  # noqa
    finally:
        status_code = elem_attrib.get("Value")

    return status_code


def get_user(content):
    """Return LoginGovPlUser instance based on ArtifactResponse.

    Args:
        content (str): decoded cipher value

    Returns:
        LoginGovPlUser: user object

    """
    tree = fromstring(content)
    SAML = "{urn:oasis:names:tc:SAML:2.0:assertion}"
    XSI = "{http://www.w3.org/2001/XMLSchema-instance}"
    first_name = tree.find(f'.//{SAML}AttributeValue[@{XSI}type="naturalperson:CurrentGivenNameType"]').text  # noqa
    last_name = tree.find(f'.//{SAML}AttributeValue[@{XSI}type="naturalperson:CurrentFamilyNameType"]').text  # noqa
    date_of_birth = tree.find('.//{SAML}AttributeValue[@{XSI}type="naturalperson:DateOfBirthType"]').text  # noqa
    pesel = tree.find('.//{SAML}AttributeValue[@{XSI}type="naturalperson:PersonIdentifierType"]').text  # noqa

    return LoginGovPlUser(first_name, last_name, date_of_birth, pesel)


def get_in_response_to(content):
    """Return InResponseTo value.

    Args:
        content (str): decoded cipher value

    Returns:
        str: AuthnRequest id

    """
    tree = fromstring(content)

    elem = tree.find(".//saml2:SubjectConfirmationData", xml_ns)

    in_response_to = elem.attrib.get("InResponseTo")

    return in_response_to


def get_name_id(content):
    """Return NameID value.

    Args:
        content (str): decoded cipher value

    Returns:
        str: NameID value
    """

    tree = fromstring(content)
    return tree.find("saml2:Subject/saml2:NameID", xml_ns).text


def get_session_id(content):
    """Return AuthnStatement session index value.

    Args:
        content (str): decoded cipher value

    Returns:
        str: session index value
    """

    tree = fromstring(content)
    return tree.find("saml2:AuthnStatement", xml_ns).attrib.get("SessionIndex")
