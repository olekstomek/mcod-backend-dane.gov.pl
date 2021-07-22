@elasticsearch
Feature: Articles list

  Scenario: Removed article is not on articles list
    Given article created with params {"id": 999, "is_removed": true, "title": "Removed article is not on articles list test"}
    When admin's request method is GET
    And admin's page /articles/article/ is requested
    Then admin's response page not contains Removed article is not on articles list test
    And admin's response page not contains /articles/article/999/change
