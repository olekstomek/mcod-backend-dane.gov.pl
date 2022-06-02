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

  @periodic_task
  Scenario: Auto data date with end date can be set on resource with type api
    Given dataset with id 990
    Given draft remote file resource of api type with id 986
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test", "description": "more than 20 characters", "dataset": 990, "status": "published", "is_manual_data_date": "False", "data_date": "22.05.2022","automatic_data_date_start": "22.05.2022", "data_date_update_period": "daily", "automatic_data_date_end": "24.05.2022"}
    And admin's page /resources/resource/986/change/ is requested
    Then admin's response status code is 200
    Then resource with id 986 has periodic task with interval schedule

  @periodic_task
  Scenario: Auto data date without end date can be set on resource with type api
    Given dataset with id 990
    Given draft remote file resource of api type with id 987
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test", "description": "more than 20 characters", "dataset": 990, "status": "published", "is_manual_data_date": "False", "data_date": "22.05.2022", "automatic_data_date_start": "22.05.2022", "data_date_update_period": "monthly", "endless_data_date_update": "True"}
    And admin's page /resources/resource/987/change/ is requested
    Then admin's response status code is 200
    Then resource with id 987 has periodic task with crontab schedule

  @periodic_task
  Scenario: Data date update can be canceled by is manual data date checkbox
    Given dataset with id 990
    Given resource with id 995 and status published and data date update periodic task
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test", "description": "more than 20 characters", "dataset": 990, "status": "published", "is_manual_data_date": "True", "data_date": "22.05.2022", "automatic_data_date_start": "22.05.2022", "data_date_update_period": "monthly", "endless_data_date_update": "True"}
    And admin's page /resources/resource/995/change/ is requested
    Then admin's response status code is 200
    Then resource with id 995 has no data date periodic task

  @periodic_task
  Scenario: Data date update can be canceled by setting status to draft
    Given dataset with id 990
    Given resource with id 997 and status published and data date update periodic task
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test", "description": "more than 20 characters", "dataset": 990, "status": "draft", "is_manual_data_date": "False", "data_date": "22.05.2022", "automatic_data_date_start": "22.05.2022", "data_date_update_period": "monthly", "endless_data_date_update": "True"}
    And admin's page /resources/resource/997/change/ is requested
    Then admin's response status code is 200
    Then resource with id 997 has no data date periodic task
