@elasticsearch
Feature: Organization details page in admin panel

  Scenario: Organization creation is ok when already existing slug is used
    Given institution created with params {"id": 999, "slug": "test-institution-slug"}
    When admin's request method is POST
    And admin's request posted institution data is {"title": "Test dodania instytucji z istniejącym slugiem", "slug": "test-institution-slug"}
    And admin's page /organizations/organization/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains Test dodania instytucji z istniejącym slugiem</a>" został pomyślnie dodany.

  Scenario: Organization creation is ok even if abbreviation is empty
    Given institution created with params {"id": 999, "slug": "test-institution-slug"}
    When admin's request method is POST
    And admin's request posted institution data is {"title": "Test dodania instytucji bez skrótu", "abbreviation": ""}
    And admin's page /organizations/organization/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains Test dodania instytucji bez skrótu</a>" został pomyślnie dodany.

  Scenario: Organization creation returns error when no tag in related dataset
    When admin's request method is POST
    And admin's request posted institution data is {"title": "Test dodania instytucji ze zbiorem bez tagów", "datasets-2-TOTAL_FORMS": "1"}
    And admin's page /organizations/organization/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains <label class="required" for="id_datasets-2-0-tags_pl">Słowa kluczowe (PL):<span>(pole wymagane)</span></label></div><div class="controls"><div class="inline error errors">

    Scenario: Dataset title on inline list redirects to dataset admin edit page
    Given dataset with id 998 and title Title as link ds and institution 999
    When admin's request method is GET
    And admin's page /organizations/organization/999/change/#datasets is requested
    Then admin's response page contains <a href="/datasets/dataset/998/change/">Title as link ds</a>
