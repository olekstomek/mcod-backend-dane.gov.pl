@elasticsearch
Feature: Datasets list page in admin panel

  Scenario: Imported datasets are visible on list in admin panel
    Given dataset for data {"id": 999, "title": "CKAN Imported Dataset"} imported from ckan named Test Source with url http://example.com
    When admin's request method is GET
    And admin's page /datasets/dataset/ is requested
    Then admin's response page contains CKAN Imported Dataset
