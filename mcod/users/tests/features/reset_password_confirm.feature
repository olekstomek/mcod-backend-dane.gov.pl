Feature: Reset password confirm

  Scenario Outline: Reset password confirm with invalid token
    Given active user with email ActiveTestUser@dane.gov.pl and password pASSWORD!qweQWE
    When api request method is POST
    And api request path is <request_path>
    And api request posted data is {"data": {"type": "user", "attributes": {"new_password1": "123.4.bcEqweQWE", "new_password2": "123.4.bcEqweQWE"}}}
    And send api request and fetch the response
    Then api's response status code is 404

    Examples:
    | request_path                                                  |
    | /1.0/auth/password/reset/abcdedfg                             |
    | /1.4/auth/password/reset/abcdedfg                             |
    | /1.0/auth/password/reset/8c37fd0c-5600-4277-a13a-67ced4a61e66 |
    | /1.4/auth/password/reset/8c37fd0c-5600-4277-a13a-67ced4a61e66 |

  Scenario: Reset password creates new token and expires previous one
    Given active user with email ActiveTestUser@dane.gov.pl and password pASSWORD!
    When api request method is POST
    And api request path is <request_path>
    And api request posted data is {"data": {"type": "user", "attributes": {"email": "ActiveTestUser@dane.gov.pl"}}}
    And send api request and fetch the response
    Then api's response status code is 200
    And password reset token is created for user with email ActiveTestUser@dane.gov.pl
    When api request method is POST
    And api request path is <request_path>
    And api request posted data is {"data": {"type": "user", "attributes": {"email": "ActiveTestUser@dane.gov.pl"}}}
    And send api request and fetch the response
    Then api's response status code is 200
    And password reset token is created for user with email ActiveTestUser@dane.gov.pl
    Then previous password reset token is invalid for user with email ActiveTestUser@dane.gov.pl
    And latest password reset token is valid for user with email ActiveTestUser@dane.gov.pl

    Examples:
    | request_path             |
    | /1.0/auth/password/reset |
    | /1.4/auth/password/reset |

  Scenario: Verify valid password reset token
    Given active user with email ActiveTestUser@dane.gov.pl and password pASSWORD!
    And valid password reset token 12345678-1234-1234-1234-123456789012 exists for user with email ActiveTestUser@dane.gov.pl
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/attributes/is_valid is True

    Examples:
    | request_path                                                         |
    | /1.0/auth/password/verify-token/12345678-1234-1234-1234-123456789012 |
    | /1.4/auth/password/verify-token/12345678-1234-1234-1234-123456789012 |

  Scenario: Verify expired password reset token
    Given active user with email ActiveTestUser@dane.gov.pl and password pASSWORD!
    And expired password reset token 12345678-1234-1234-1234-123456789012 exists for user with email ActiveTestUser@dane.gov.pl
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/attributes/is_valid is False

    Examples:
    | request_path                                                         |
    | /1.0/auth/password/verify-token/12345678-1234-1234-1234-123456789012 |
    | /1.4/auth/password/verify-token/12345678-1234-1234-1234-123456789012 |

  Scenario: Verify non existing valid password reset token
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field /data/attributes/is_valid is False

    Examples:
    | request_path                                                         |
    | /1.0/auth/password/verify-token/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee |
    | /1.4/auth/password/verify-token/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee |

  Scenario: Verify invalid password reset token
    When api request method is GET
    And api request path is <request_path>
    And send api request and fetch the response
    Then api's response status code is 404
    And api's response body field errors/[0]/status is 404 Not Found
    And api's response body field errors/[0]/code is 404_not_found
    And api's response body field errors/[0]/title is 404 Not Found
    And api's response body field errors/[0]/detail is The requested resource could not be found

    Examples:
    | request_path                                           |
    | /1.0/auth/password/verify-token/not-uuid-invalid-token |
    | /1.4/auth/password/verify-token/not-uuid-invalid-token |
