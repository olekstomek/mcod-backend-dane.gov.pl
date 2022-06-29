Feature: Applications that are displayed on main page.
  Scenario: Featured applications
    Given featured applications
    When api request path is /1.4/applications
    And api request param is_featured is true
    Then send api request and fetch the response
    And api's response status code is 200
    And 4 featured applications are returned
