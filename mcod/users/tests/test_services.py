# from logingovpl.objects import LoginGovPlUser

from mcod.users.services import LoginGovPlService


class TestLoginGovPlService:
    service = LoginGovPlService()

    @property
    def _saml(self):
        """Return saml example content."""
        with open("mcod/users/tests/data/saml.xml", "r") as f:
            return f.read()

    def test__get_status_code_from_saml(self):
        """Test if _get_status_code_from_saml method returns variables with specified types."""
        res = self.service._get_status_code_from_saml(self._saml)
        assert isinstance(res, tuple)
        assert isinstance(res[0], str)
        assert isinstance(res[1], str)

    def test_saml_assertion(self, mocker):
        """Test if method saml_assertion returns variables with specified types."""

        class TestRequest:
            content = self._saml

        mocker.patch(
            "mcod.users.services.LoginGovPlService.resolve_artifact",
            return_value=TestRequest(),
        )
        test_response = TestRequest()
        res = self.service.get_saml_assertion_status(test_response.content)
        assert len(res) == 2

        status_code, message = res
        assert isinstance(status_code, str)
        assert isinstance(message, str)

    # FIXME: test_services to be changed
    # def test_get_data_from_saml_art(self, mocker):
    #     """Test if method decode_saml_artifact returns variables with specified types."""
    #     logingovpl_user = LoginGovPlUser("first name", "last name", "birthday", "pesel")
    #     mocker.patch("mcod.users.services.decode_cipher_value", return_value="")
    #     mocker.patch("mcod.users.services.get_user", return_value=logingovpl_user)
    #     mocker.patch("mcod.users.services.get_name_id", return_value="")
    #     mocker.patch(
    #         "mcod.users.services.in_response_to", return_value="ID-1234-LOGIN-UNKNOWN"
    #     )
    #     mocker.patch("mcod.users.services.get_session_id", return_value="")

    #     res = self.service.get_data_from_saml_art("some_saml".encode())
    #     assert len(res) == 3

    #     logingovpl_user, name_id, in_response_to, session_id = res

    #     assert isinstance(logingovpl_user, LoginGovPlUser)
    #     assert isinstance(name_id, str)
    #     assert isinstance(in_response_to, str)
    #     assert isinstance(session_id, str)
