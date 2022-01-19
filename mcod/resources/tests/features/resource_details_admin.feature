@elasticsearch
Feature: Resource details page in admin panel

  Scenario: Imported resource is not editable in admin panel
    Given resource with id 999 imported from ckan named Test Source with url http://example.com
    When admin's page /resources/resource/999/change/ is requested
    Then admin's response page is not editable

  Scenario: Forced file type checkbox is hidden for imported api resource
    Given resource with id 999 imported from ckan named Test Source with url http://example.com and type api
    When admin's page /resources/resource/999/change/ is requested
    Then admin's response page not contains forced_file_type
