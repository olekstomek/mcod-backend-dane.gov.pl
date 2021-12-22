@elasticsearch
Feature: Showcase details admin
  Scenario: Showcase creation with auto slug
    When admin's request method is POST
    And admin's request posted showcase data is {"title": "Test with showcase title", "slug": "test-with-showcase-title"}
    And admin's page /showcases/showcase/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Test with showcase title</a>" została pomyślnie dodana.
    And latest showcase attribute slug is test-with-showcase-title

  Scenario: Showcase creation with manual slug
    When admin's request method is POST
    And admin's request posted showcase data is {"title": "Test with showcase title", "slug": "manual-name"}
    And admin's page /showcases/showcase/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Test with showcase title</a>" została pomyślnie dodana.
    And latest showcase attribute slug is manual-name
