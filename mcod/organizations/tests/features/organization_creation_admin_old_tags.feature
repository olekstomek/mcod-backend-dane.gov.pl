@elasticsearch
Feature: Organization creation in admin panel

  Scenario: Organization creation returns error when no tag in related dataset
    When admin's request method is POST
    And admin's request posted institution data is {"title": "Test dodania instytucji ze zbiorem bez tagów", "datasets-2-TOTAL_FORMS": "1", "datasets-2-0-tags": []}
    And admin's page /organizations/organization/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains <label class="required" for="id_datasets-2-0-tags">Słowo kluczowe:<span>(pole wymagane)</span></label></div><div class="controls"><div class="inline error errors">
