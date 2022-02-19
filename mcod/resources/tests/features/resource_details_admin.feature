@elasticsearch
Feature: Resource details page in admin panel

  Scenario: Change resource
    Given dataset with id 999
    And resource created with params {"id": 999, "dataset_id": 999}
    When admin's request method is POST
    And admin's request posted resource data is {"title": "title changed in form", "description": "<p>more than 20 characters</p>", "dataset": [999], "status": "published", "data_date": "2021-05-04"}
    And admin's page /resources/resource/999/change/ is requested
    Then admin's response status code is 200
    And admin's response page contains title changed in form
    And admin's response resolved url name is resources_resource_changelist

  Scenario: Imported resource is not editable in admin panel
    Given resource with id 999 imported from ckan named Test Source with url http://example.com
    When admin's page /resources/resource/999/change/ is requested
    Then admin's response page is not editable

  Scenario: Forced file type checkbox is hidden for imported api resource
    Given resource with id 999 imported from ckan named Test Source with url http://example.com and type api
    When admin's page /resources/resource/999/change/ is requested
    Then admin's response page not contains forced_file_type
