Feature: User Account API
  Scenario: Get user account in API 1.0
    Given logged active user
    When api request method is GET
    And api request path is /1.0/auth/user
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body has field /data/id
    And api's response body field data/attributes has fields email,state,fullname
    And api's response body field data/attributes has no fields password1,password2
    And api's response body field /data/attributes/rodo_privacy_policy_opt_in is False
    And api's response body field /data/attributes/subscriptions_report_opt_in is False
    And api's response body field /data/attributes/state is active
    And api's response body has field /data/relationships/institutions

  Scenario: Get user account for not logged user
    When api request method is GET
    And api request path is /1.0/auth/user
    And send api request and fetch the response
    Then api's response status code is 401
    And api's response body field code is token_missing

  Scenario: Get user account for invalid token
    When api request method is GET
    And api request path is /1.0/auth/user
    And api request header Authorization is Bearer INVALIDiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjp7InNlc3Npb25fa2V5IjoiYjZkMXEwMzZmYXcyczlzZm1nenB3dWVxOWg0OHYyYmciLCJlbWFpbCI6Im1hcmNpbi5yb2dvd3NraUBicml0ZW5ldC5jb20ucGwiLCJyb2xlIjoiYWRtaW4ifSwiaWF0IjoxNTg5NTQyNjYxLCJuYmYiOjE1ODk1NDI2NjEsImV4cCI6MTU4OTU1NzA2MX0.rHU2Xt3JfgTUKsfQHM8NAIg29p3Z8OHSJ3QA9CNeVqF
    And send api request and fetch the response
    Then api's response status code is 401
    And api's response body field code is token_error

  Scenario Outline: Update user account is ok
    Given logged active user
    When api request method is PUT
    And api request path is <request_path>
    And api request posted data is <req_post_data>
    And send api request and fetch the response
    Then api's response status code is 200
    And api request method is GET
    And send api request and fetch the response
    And api's response body field /data/attributes/fullname is AAAA BBBB
    And api's response body field /data/attributes/rodo_privacy_policy_opt_in is True
    And api's response body field /data/attributes/subscriptions_report_opt_in is True

    Examples:
    | request_path   | req_post_data                                                                                                                                |
    | /1.0/auth/user | {"fullname": "AAAA BBBB", "rodo_privacy_policy_opt_in": true, "subscriptions_report_opt_in": true}                                           |
    | /1.4/auth/user | {"data": {"type": "user", "attributes": {"fullname": "AAAA BBBB", "rodo_privacy_policy_opt_in": true, "subscriptions_report_opt_in": true}}} |
