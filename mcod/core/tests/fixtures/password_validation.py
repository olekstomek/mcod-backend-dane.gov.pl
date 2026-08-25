import pytest

TEST_PASSWORD = "12345.AbcdeXyz@"


@pytest.fixture
def test_password() -> str:
    """Return a valid password meeting all validation requirements.

    Requirements:
    - At least 14 characters long
    - Contains at least one digit
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one special character
    """
    return TEST_PASSWORD
