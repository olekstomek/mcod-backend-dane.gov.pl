@elasticsearch
Feature: Applications list admin
  Scenario: Removed application is not on applications list
    Given removed application with id 999
    When admin's request method is GET
    And admin's page /applications/application/ is requested
    Then admin's response page not contains /applications/application/999/change/

  Scenario: Admin see applications on main page
    Given logged admin user
    When admin's page / is requested
    Then admin's response status code is 200
    And admin's response page contains /applications/

  Scenario: Admin can go to applications page
    Given logged admin user
    When admin's page /applications/ is requested
    Then admin's response status code is 200

  Scenario: Editor doesnt see applications on main page
    Given logged editor user
    When admin's page / is requested
    Then admin's response status code is 200
    And admin's response page not contains /applications/

  Scenario: Editor cant go to applications page
    Given logged editor user
    When admin's page /applications/ is requested
    Then admin's response status code is 404
