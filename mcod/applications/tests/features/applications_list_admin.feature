@elasticsearch
Feature: Applications list admin
  Scenario: Removed application is not on applications list
    Given removed application with id 999
    When admin's request method is GET
    And admin's page /applications/application/ is requested
    Then admin's response page not contains /applications/application/999/change/
