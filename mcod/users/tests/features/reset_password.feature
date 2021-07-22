Feature: Reset password

  Scenario Outline: Reset password is ok
    Given active user with email ActiveTestUser@dane.gov.pl and password pASSWORD!
    And list of sent emails is empty
    When api request method is POST
    And api request path is <request_path>
    And api request posted data is <req_post_data>
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field <resp_body_field> is <resp_body_value>
    And sent email contains To: ActiveTestUser@dane.gov.pl
    And valid reset link for ActiveTestUser@dane.gov.pl in mail content

    Examples:
    | request_path             | req_post_data                                                                     | resp_body_field                              | resp_body_value |
    | /1.0/auth/password/reset | {"email": "ActiveTestUser@dane.gov.pl"}                                           | result                                       | ok              |
    | /1.4/auth/password/reset | {"data": {"type": "user", "attributes": {"email": "ActiveTestUser@dane.gov.pl"}}} | data/attributes/is_password_reset_email_sent | True            |

  Scenario Outline: Reset password for wrong email format
    Given active user with email ActiveTestUser@dane.gov.pl and password pASSWORD!
    And list of sent emails is empty
    When api request method is POST
    And api request path is <request_path>
    And api request posted data is <req_post_data>
    And send api request and fetch the response
    Then api's response status code is 422

    Examples:
    | request_path             | req_post_data                                                              |
    | /1.0/auth/password/reset | {"email": "wrong_email_address"}                                           |
    | /1.4/auth/password/reset | {"data": {"type": "user", "attributes": {"email": "wrong_email_address"}}} |

  Scenario Outline: Reset password for non existing email
    Given active user with email ActiveTestUser@dane.gov.pl and password pASSWORD!
    And list of sent emails is empty
    When api request method is POST
    And api request path is <request_path>
    And api request posted data is <req_post_data>
    And send api request and fetch the response
    Then api's response status code is 404

    Examples:
    | request_path             | req_post_data                                                                   |
    | /1.0/auth/password/reset | {"email": "this_email@doesnotex.ist"}                                           |
    | /1.4/auth/password/reset | {"data": {"type": "user", "attributes": {"email": "this_email@doesnotex.ist"}}} |

  Scenario Outline: Reset password with send_mail exception raised
    Given active user with email ActiveTestUser@dane.gov.pl and password pASSWORD!
    And list of sent emails is empty
    When api request method is POST
    And api request path is <request_path>
    And api request posted data is <req_post_data>
    And send_mail will raise SMTPException
    And send api request and fetch the response
    Then api's response status code is 500

    Examples:
    | request_path             | req_post_data                                                                     |
    | /1.0/auth/password/reset | {"email": "ActiveTestUser@dane.gov.pl"}                                           |
    | /1.4/auth/password/reset | {"data": {"type": "user", "attributes": {"email": "ActiveTestUser@dane.gov.pl"}}} |
