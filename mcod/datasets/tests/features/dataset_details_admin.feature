@elasticsearch
Feature: Dataset details page in admin panel

  Scenario: Imported dataset is not editable in admin panel
    Given dataset for data {"id": 999} imported from ckan named Test Source with url http://example.com
    When admin's request method is GET
    And admin's page /datasets/dataset/999/change/ is requested
    Then admin's response page is not editable
