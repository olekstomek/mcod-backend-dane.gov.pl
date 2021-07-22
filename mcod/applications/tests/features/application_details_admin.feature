@elasticsearch
Feature: Application details admin
  Scenario: Application creation with auto slug
    When admin's request method is POST
    And admin's request posted application data is {"title": "Test with application title", "slug": "test-with-application-title"}
    And admin's page /applications/application/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Test with application title</a>" została pomyślnie dodana.
    And latest application attribute slug is test-with-application-title

  Scenario: Application creation with manual slug
    When admin's request method is POST
    And admin's request posted application data is {"title": "Test with application title", "slug": "manual-name"}
    And admin's page /applications/application/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Test with application title</a>" została pomyślnie dodana.
    And latest application attribute slug is manual-name
