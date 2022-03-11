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

  Scenario: Adding tags to application
    Given tag created with params {"id": 999, "language": "pl", "name": "test application tag"}
    When admin's request method is POST
    And admin's request posted application data is {"title": "Test with application title", "slug": "manual-name", "tags_pl": [999]}
    And admin's page /applications/application/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Test with application title</a>" została pomyślnie dodana.
    And latest application attribute keywords_list is [{'name': 'test application tag', 'language': 'pl'}]

  Scenario: Application is not visible in API after adding to trash
    Given dataset with id 999
    And application created with params {"id": 999, "title": "Test application", "datasets": [999]}
    When admin's request method is POST
    And admin's request posted application data is {"post": "yes"}
    And admin's page /applications/application/999/delete/ is requested
    Then admin's response status code is 200
    And admin's response page contains Aplikacja &quot;Test application&quot; usunięta pomyślnie.
    And api request path is /applications/?id=999
    And send api request and fetch the response
    And api's response body field meta/count is 0
    And api request path is /applications/999/datasets
    And send api request and fetch the response
    And api's response body field meta/count is 0

  Scenario: Application is visible in API after removing from trash
    Given dataset with id 999
    And application created with params {"id": 999, "title": "Test application in trash", "is_removed": true, "datasets": [999]}
    When admin's request method is POST
    And admin's request posted application data is {"is_removed": false}
    And admin's page /applications/applicationtrash/999/change/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">Test application in trash</a>" został pomyślnie zmieniony.
    And api request path is /applications/?id=999
    And send api request and fetch the response
    And api's response body field data/[0]/id is 999
    And api's response body field data/[0]/relationships/datasets/meta/count is 1
    And api request path is /applications/999/datasets
    And send api request and fetch the response
    And api's response body field data/[0]/id is 999
    And api's response body field meta/count is 1
