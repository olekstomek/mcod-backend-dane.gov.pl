Feature: Resource comments list page in admin panel

  Scenario: Resource comments list page is not visible for NOT superuser
    Given admin's request logged user is editor user
    When admin's request method is GET
    And admin's page /suggestions/resourcecomment/ is requested
    Then admin's response status code is 403
    Then admin's response page not contains Uwagi do danych

  Scenario: Resource comments list page is visible for superuser
    Given admin's request logged user is admin user
    When admin's request method is GET
    And admin's page /suggestions/resourcecomment/ is requested
    Then admin's response status code is 200
    Then admin's response page contains Uwagi do danych

  Scenario: Resource comments list - Trash page is not visible for NOT superuser
    Given admin's request logged user is editor user
    When admin's request method is GET
    And admin's page /suggestions/resourcecommenttrash/ is requested
    Then admin's response status code is 403
    Then admin's response page not contains Uwagi do danych - Kosz

  Scenario: Resource comments list - Trash page is visible for superuser
    Given admin's request logged user is admin user
    When admin's request method is GET
    And admin's page /suggestions/resourcecommenttrash/ is requested
    Then admin's response status code is 200
    Then admin's response page contains Uwagi do danych - Kosz
