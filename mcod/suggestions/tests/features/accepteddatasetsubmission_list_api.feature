@elasticsearch
Feature: Accepted dataset submission list API

  Scenario Outline: Test accepted dataset submission list endpoint is accessible by some user types
    Given logged <user_type>
    When api request method is GET
    And api request path is /submissions/accepted
    Then send api request and fetch the response
    And api's response status code is 200

    Examples:
    | user_type   |
    | editor user |
    | admin user  |
    | agent user  |

  Scenario Outline: Test accepted dataset submission list endpoint is not accessible for some user types
    Given logged <user_type>
    When api request method is GET
    And api request path is /submissions/accepted
    Then send api request and fetch the response
    And api's response status code is 403

    Examples:
    | user_type     |
    | active user   |
    | official user |

  Scenario Outline: Test public accepted dataset submission list endpoint is accessible by all user types
    Given logged <user_type>
    When api request method is GET
    And api request path is /submissions/accepted/public
    Then send api request and fetch the response
    And api's response status code is 200

    Examples:
    | user_type     |
    | editor user   |
    | admin user    |
    | agent user    |
    | active user   |
    | official user |
