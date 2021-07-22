@elasticsearch
Feature: Resources list in admin panel

  Scenario: Admin can see resources on list
    Given resource created with params {"id": 999, "title": "Test widoczności zasobu na liście"}
    When admin's request method is GET
    And admin's page /resources/resource/ is requested
    Then admin's response status code is 200
    And admin's response page contains Test widoczności zasobu na liście

  Scenario: Admin shouldnt see deleted resources on list
    Given resource created with params {"id": 999, "title": "Test widoczności zasobu na liście", "is_removed": true}
    When admin's request method is GET
    And admin's page /resources/resource/ is requested
    Then admin's response status code is 200
    And admin's response page not contains Test widoczności zasobu na liście
