Feature: User Login
  User can login using API

  Scenario: Login with API 1.4
    Given logged active user
    #And logged active user with email piotrek@mc.gov.pl and password 1234.Abcde
    #And second logged active user with email tomek@mc.gov.pl and password 1234.Abcde
    When api request method is GET
    And api request path is /auth/subscriptions
    And send api request and fetch the response
    Then api's response status code is 200

  Scenario: Login active user
    Given logged out active user with email test@example.com and password 123
    When api request method is POST
    And api request path is /auth/login
    And api request posted data is {"data": {"type": "user", "attributes": {"email": "test@example.com", "password": "123"}}}
    Then send api request and fetch the response
    And api's response status code is 201
    And api's response body field data/attributes/email is test@example.com

  Scenario: Login pending user
    Given logged out pending user with email test@example.com and password 123
    When api request method is POST
    And api request path is /auth/login
    And api request posted data is {"data": {"type": "user", "attributes": {"email": "test@example.com", "password": "123"}}}
    Then send api request and fetch the response
    And api's response status code is 403
    And api's response body field errors/[0]/code is 403_forbidden
    And api's response body field errors/[0]/detail is Adres email nie został potwierdzony
    And api's response body field errors/[0]/title is 403 Forbidden
    And api's response body field errors/[0]/status is 403 Forbidden

  Scenario: Login blocked user
    Given logged out blocked user with email test@example.com and password 123
    When api request method is POST
    And api request path is /auth/login
    And api request posted data is {"data": {"type": "user", "attributes": {"email": "test@example.com", "password": "123"}}}
    Then send api request and fetch the response
    And api's response status code is 401
    And api's response body field errors/[0]/code is 401_unauthorized
    And api's response body field errors/[0]/detail is Konto jest zablokowane
    And api's response body field errors/[0]/title is 401 Unauthorized
    And api's response body field errors/[0]/status is 401 Unauthorized

  Scenario: Login email is case insensitive
    Given logged out active user with email test@example.com and password 123
    When api request method is POST
    And api request path is /auth/login
    And api request posted data is {"data": {"type": "user", "attributes": {"email": "TEST@EXAMPLE.COM", "password": "123"}}}
    Then send api request and fetch the response
    And api's response status code is 201
    And api's response body field data/attributes/email is test@example.com

  Scenario: Login when email is missing
    Given logged out active user with email test@example.com and password 123
    When api request method is POST
    And api request path is /auth/login
    And api request posted data is {"data": {"type": "user", "attributes": {"password": "123"}}}
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field errors/[0]/title is Błąd pola
    And api's response body field errors/[0]/detail is Brak danych w wymaganym polu.
    And api's response body field errors/[0]/source/pointer is /data/attributes/email

  Scenario: Login when password is missing
    Given logged out active user with email test@example.com and password 123
    When api request method is POST
    And api request path is /auth/login
    And api request posted data is {"data": {"type": "user", "attributes": {"email": "test@example.com"}}}
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field errors/[0]/title is Błąd pola
    And api's response body field errors/[0]/detail is Brak danych w wymaganym polu.
    And api's response body field errors/[0]/source/pointer is /data/attributes/password

  Scenario: Login when email format is not valid
    When api request method is POST
    And api request path is /auth/login
    And api request posted data is {"data": {"type": "user", "attributes": {"email": "aaa@aaa", "password": "123"}}}
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field errors/[0]/code is 422_unprocessable_entity
    And api's response body field errors/[0]/detail is Nieważny adres email.
    And api's response body field errors/[0]/title is Błąd pola
    And api's response body field errors/[0]/status is 422 Unprocessable Entity
    And api's response body field errors/[0]/source/pointer is /data/attributes/email

  Scenario: Login when email is wrong
    When api request method is POST
    And api request path is /auth/login
    And api request posted data is {"data": {"type": "user", "attributes": {"email": "doesnotexist@example.com", "password": "INVALID!@#"}}}
    And send api request and fetch the response
    Then api's response status code is 401
    And api's response body field errors/[0]/code is 401_unauthorized
    And api's response body field errors/[0]/title is 401 Unauthorized
    And api's response body field errors/[0]/detail is Niepoprawny email lub hasło

  Scenario: Login when password is wrong
    Given logged out active user with email test@example.com and password 123
    When api request method is POST
    And api request path is /auth/login
    And api request posted data is {"data": {"type": "user", "attributes": {"email": "test@example.com", "password": "INVALID!@#"}}}
    And send api request and fetch the response
    Then api's response status code is 401
    And api's response body field errors/[0]/code is 401_unauthorized
    And api's response body field errors/[0]/title is 401 Unauthorized
    And api's response body field errors/[0]/detail is Niepoprawny email lub hasło

  Scenario: Login when body is wrong
    When api request method is POST
    And api request path is /auth/login
    And api request posted data is {"data": {"type": "user", "attributes": {}}}
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field errors/[0]/code is 422_unprocessable_entity
    And api's response body field errors/[0]/detail is Brak danych w wymaganym polu.
    And api's response body field errors/[0]/status is 422 Unprocessable Entity
    And api's response body field errors/[0]/title is Błąd pola
