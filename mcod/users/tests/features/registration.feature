Feature: Registration

  Scenario Outline: Registration is ok
    When api request method is POST
    And api request path is <request_path>
    And api request posted data is <req_post_data>
    And send api request and fetch the response
    Then api's response status code is 201
    And api's response body has field data/id
    And api's response body has field data/attributes
    And api's response body field data/attributes/state is pending
    And api's response body field data/attributes has fields email,state
    And api's response body field data/attributes has no fields password1,password2,phone,phone_internal

    Examples:
    | request_path           | req_post_data                                                                                                                 |
#    | /1.0/auth/registration | {"email": "tester@mc.gov.pl", "password1": "123!A!b!c!", "password2": "123!A!b!c!"}                                           |
    | /1.4/auth/registration | {"data": {"type": "user", "attributes": {"email": "tester@mc.gov.pl", "password1": "123!A!b!c!", "password2": "123!A!b!c!"}}} |

  Scenario Outline: Registration with fullname is ok
    Given list of sent emails is empty
    When api request method is POST
    And api request path is <request_path>
    And api request posted data is <req_post_data>
    And send api request and fetch the response
    Then api's response status code is 201
    And api's response body has field data/id
    And api's response body has field data/attributes
    And api's response body field data/attributes/state is pending
    And api's response body field data/attributes/fullname is Test User 2
    And api's response body field data/attributes has fields email,state
    And api's response body field data/attributes has no fields password1,password2,phone,phone_internal
    And sent email contains To: tester2@mc.gov.pl
    And valid confirmation link for tester2@mc.gov.pl in mail content

    Examples:
    | request_path           | req_post_data                                                                                                                                             |
#    | /1.0/auth/registration | {"email": "tester2@mc.gov.pl", "fullname": "Test User 2", "password1": "123!A!b!c!", "password2": "123!A!b!c!"}                                           |
    | /1.4/auth/registration | {"data": {"type": "user", "attributes": {"email": "tester2@mc.gov.pl", "fullname": "Test User 2", "password1": "123!A!b!c!", "password2": "123!A!b!c!"}}} |

  Scenario: Registration without required fields
    When api request method is POST
    And api request path is /1.0/auth/registration
    And api request posted data is {"fullname": "Test User"}
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field code is entity_error
    And api's response body field errors/email is ['Brak danych w wymaganym polu.']
    And api's response body field errors/password1 is ['Brak danych w wymaganym polu.']
    And api's response body field errors/password2 is ['Brak danych w wymaganym polu.']

  Scenario Outline: Registration without required fields in API 1.4
    When api request method is POST
    And api request language is <lang_code>
    And api request path is /1.4/auth/registration
    And api request posted data is {"data": {"type": "user", "attributes": {"fullname": "Test User"}}}
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field errors/[0]/code is 422_unprocessable_entity
    And api's response body field <resp_body_field> is <resp_body_value>
    And api's response body field errors/[0]/source/pointer is /data/attributes/email
    And api's response body field errors/[1]/source/pointer is /data/attributes/password1
    And api's response body field errors/[2]/source/pointer is /data/attributes/password2

    Examples:
    | lang_code | resp_body_field   | resp_body_value                  |
    | pl        | errors/[0]/detail | Brak danych w wymaganym polu.    |
    | en        | errors/[0]/detail | Missing data for required field. |

  Scenario: Registration with invalid email
    When api request method is POST
    And api request path is /1.0/auth/registration
    And api request posted data is {"email": "not_valid@email", "password1": "123!a!b!c!", "password2": "123!a!b!c!"}
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field code is entity_error
    And api's response body field errors/email is ['Nieważny adres email.']

  Scenario: Registration with too short password
    When api request method is POST
    And api request path is /1.0/auth/registration
    And api request posted data is {"email": "test@mc.gov.pl", "password1": "123.aBc", "password2": "123.aBc"}
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field code is entity_error
    And api's response body field errors/password1 is ['To hasło jest za krótkie. Musi zawierać co najmniej %(min_length)d znaków.']
    And api's response body has no field errors/password2

  Scenario: Registration with different new passwords
    When api request method is POST
    And api request path is /1.0/auth/registration
    And api request posted data is {"email": "test@mc.gov.pl", "password1": "12.34a.bCd!", "password2": "12.34a.bCd!!"}
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field code is entity_error
    And api's response body field errors/password1 is ['Hasła nie pasują']
    And api's response body has no field errors/password2

  Scenario: Registration account already exists
    Given active user with email tester@mc.gov.pl and password 123!a!B!c!
    When api request method is POST
    And api request path is /1.0/auth/registration
    And api request posted data is {"email": "tester@mc.gov.pl", "password1": "123!a!B!c!", "password2": "123!a!B!c!"}
    And send api request and fetch the response
    Then api's response status code is 403

  Scenario: Registration cannot change user state
    When api request method is POST
    And api request path is /1.0/auth/registration
    And api request posted data is {"email": "tester@mc.gov.pl", "password1": "123!a!B!c!", "password2": "123!a!B!c!", "state": "active"}
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field data/attributes/state is pending
    And user with email tester@mc.gov.pl state is pending

  Scenario Outline: Cannot register same user twice with different case of letter
    Given active user with email tester@mc.gov.pl and password 123!a!B!c!
    When api request method is POST
    And api request path is <request_path>
    And api request posted data is <req_post_data>
    And send api request and fetch the response
    Then api's response status code is 403

    Examples:
    | request_path           | req_post_data                                                                                                                 |
    | /1.0/auth/registration | {"email": "TESTER@MC.GOV.PL", "password1": "123!a!B!c!", "password2": "123!a!B!c!", "state": "active"}                        |
    | /1.4/auth/registration | {"data": {"type": "user", "attributes": {"email": "TESTER@MC.GOV.PL", "password1": "123!a!B!c!", "password2": "123!a!B!c!"}}} |
