Feature: Showcases list admin
  Scenario: Removed showcase is not on showcases list
    Given removed showcase with id 999
    When admin's request method is GET
    And admin's page /showcases/showcase/ is requested
    Then admin's response page not contains /showcases/showcase/999/change/
