@elasticsearch
Feature: Change resource in admin panel

  Scenario: Change of resource regions updates regions in db
    Given dataset with id 998
    And resource with id 999 dataset id 998 and single main region
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test", "description": "more than 20 characters", "dataset": 998, "data_date": "22.05.2020", "status": "published", "regions": [101752777, 1309742673], "_continue":""}
    And admin's page with mocked geo api /resources/resource/999/change/ is requested
    Then admin's response status code is 200
    And resource has assigned main and additional regions
    And admin's response page form contains Warszawa and Wólka Kosowska
