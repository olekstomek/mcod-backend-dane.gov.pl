@elasticsearch
Feature: Showcase details admin
  Scenario: Showcase creation with auto slug
    When admin's request method is POST
    And admin's request posted showcase data is {"title": "Test with showcase title", "slug": "test-with-showcase-title"}
    And admin's page /showcases/showcase/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Test with showcase title</a>" zostało pomyślnie dodane.
    And latest showcase attribute slug is test-with-showcase-title

  Scenario: Showcase creation with manual slug
    When admin's request method is POST
    And admin's request posted showcase data is {"title": "Test with showcase title", "slug": "manual-name"}
    And admin's page /showcases/showcase/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Test with showcase title</a>" zostało pomyślnie dodane.
    And latest showcase attribute slug is manual-name

  Scenario: Showcase is not visible in API after adding to trash
    Given dataset with id 999
    And showcase created with params {"id": 999, "title": "Test showcase", "datasets": [999]}
    When admin's request method is POST
    And admin's request posted showcase data is {"post": "yes"}
    And admin's page /showcases/showcase/999/delete/ is requested
    Then admin's response status code is 200
    And admin's response page contains Ponowne wykorzystanie &quot;Test showcase&quot; usunięte pomyślnie.
    And api request path is /showcases/?id=999
    And send api request and fetch the response
    And api's response body field meta/count is 0
    And api request path is /showcases/999/datasets
    And send api request and fetch the response
    And api's response body field meta/count is 0

  Scenario: Showcase is visible in API after removing from trash
    Given dataset with id 999
    And showcase created with params {"id": 999, "title": "Test showcase in trash", "is_removed": true, "datasets": [999]}
    When admin's request method is POST
    And admin's request posted showcase data is {"is_removed": false}
    And admin's page /showcases/showcasetrash/999/change/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Test showcase in trash</a>" został pomyślnie zmieniony.
    And api request path is /showcases/?id=999
    And send api request and fetch the response
    And api's response body field data/[0]/id is 999
    And api's response body field data/[0]/relationships/datasets/meta/count is 1
    And api request path is /showcases/999/datasets
    And send api request and fetch the response
    And api's response body field data/[0]/id is 999
    And api's response body field meta/count is 1
