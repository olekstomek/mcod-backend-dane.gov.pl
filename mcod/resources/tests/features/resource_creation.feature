@elasticsearch
Feature: Resource from link creation

# Testy wywalają się losowo za każdym razem inny mimo że mają tą samą strukturę. Czasem nie tworzy się zasób.
#  Scenario: Creation of resource with link to html content
#    Given resource is created for link http://example.com/index.html with html content
#    Then admin's response status code is 200
#    And resource field link is http://example.com/index.html
#    And resource field type is website
#
#  Scenario: Creation of resource with link to file content
#    Given resource is created for link http://example.com/index.php with zip content
#    Then admin's response status code is 200
#    And resource field link is http://example.com/index.php
#    And resource field type is file
#
#  Scenario: Creation of resource with link to xml content
#    Given resource is created for link http://example.com/index.xml with xml content
#    Then admin's response status code is 200
#    And resource field link is http://example.com/index.xml
#    And resource field type is file
#
#  Scenario: Creation of resource with link to json content
#    Given resource is created for link http://example.com/index.json with json content
#    Then admin's response status code is 200
#    And resource field link is http://example.com/index.json
#    And resource field type is file
#
#  Scenario: Creation of resource with link to xls content
#    Given resource is created for link http://example.com/index.xls with xls content
#    Then admin's response status code is 200
#    And resource field link is http://example.com/index.xls
#    And resource field type is file

  Scenario: Resource creation is ok
    Given dataset with id 999
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test", "description": "more than 20 characters", "switcher": "link", "file": "", "link": "https://test.to.resource.pl/1.xls", "dataset": 999, "data_date": "22.05.2020", "status": "published"}
    And admin's page /resources/resource/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">test</a>" został pomyślnie dodany.

  Scenario: Resource creation with docx supplement file is ok
    Given dataset with id 999
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test supplements", "description": "more than 20 characters", "switcher": "link", "file": "", "link": "https://test.to.resource.pl/1.xls", "dataset": 999, "data_date": "22.05.2020", "status": "published", "supplements-TOTAL_FORMS": "1", "supplements-0-id": "", "supplements-0-name": "test", "supplements-0-name_en": "", "supplements-0-resource": "", "supplements-0-order": "0"}
    And admin's request posted files {"supplements-0-file": "doc_img.docx"}
    And admin's page /resources/resource/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">test supplements</a>" został pomyślnie dodany.
    And latest supplement attribute name is test

  Scenario: Resource creation with odt supplement file is ok
    Given dataset with id 999
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test supplements", "description": "more than 20 characters", "switcher": "link", "file": "", "link": "https://test.to.resource.pl/1.xls", "dataset": 999, "data_date": "22.05.2020", "status": "published", "supplements-TOTAL_FORMS": "1", "supplements-0-id": "", "supplements-0-name": "test", "supplements-0-name_en": "", "supplements-0-resource": "", "supplements-0-order": "0"}
    And admin's request posted files {"supplements-0-file": "example_odt_file.odt"}
    And admin's page /resources/resource/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">test supplements</a>" został pomyślnie dodany.
    And latest supplement attribute name is test

  Scenario: Resource creation with pdf supplement file is ok
    Given dataset with id 999
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test supplements", "description": "more than 20 characters", "switcher": "link", "file": "", "link": "https://test.to.resource.pl/1.xls", "dataset": 999, "data_date": "22.05.2020", "status": "published", "supplements-TOTAL_FORMS": "1", "supplements-0-id": "", "supplements-0-name": "test", "supplements-0-name_en": "", "supplements-0-resource": "", "supplements-0-order": "0"}
    And admin's request posted files {"supplements-0-file": "example.pdf"}
    And admin's page /resources/resource/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">test supplements</a>" został pomyślnie dodany.
    And latest supplement attribute name is test

  Scenario: Resource creation with txt supplement file is ok
    Given dataset with id 999
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test supplements", "description": "more than 20 characters", "switcher": "link", "file": "", "link": "https://test.to.resource.pl/1.xls", "dataset": 999, "data_date": "22.05.2020", "status": "published", "supplements-TOTAL_FORMS": "1", "supplements-0-id": "", "supplements-0-name": "test", "supplements-0-name_en": "", "supplements-0-resource": "", "supplements-0-order": "0"}
    And admin's request posted files {"supplements-0-file": "example.txt"}
    And admin's page /resources/resource/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">test supplements</a>" został pomyślnie dodany.
    And latest supplement attribute name is test

  Scenario: Adding of supplement to resource is visible in history
    Given resource with id 999
    And supplement created with params {"id": 999, "resource_id": 999, "file": "example.txt", "name": "supplement 999 added to resource 999"}
    When admin's page /resources/resource/999/history is requested
    Then admin's response page contains supplement 999 added to resource 999
    And admin's response page contains example.txt

  Scenario: Resource creation with invalid supplement file
    Given dataset with id 999
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test supplements", "description": "more than 20 characters", "switcher": "link", "file": "", "link": "https://test.to.resource.pl/1.xls", "dataset": 999, "data_date": "22.05.2020", "status": "published", "supplements-TOTAL_FORMS": "1", "supplements-0-id": "", "supplements-0-name": "test", "supplements-0-name_en": "", "supplements-0-resource": "", "supplements-0-order": "0"}
    And admin's request posted files {"supplements-0-file": "simple.csv"}
    And admin's page /resources/resource/add/ is requested
    Then admin's response page contains Dokonano wyboru niewłaściwego formatu dokumentu!

  Scenario: Resource creation fails if provided link starts with http:
    Given dataset with id 999
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test", "description": "more than 20 characters", "switcher": "link", "file": "", "link": "http://test.to.resource.pl/1.xls", "dataset": 999, "data_date": "22.05.2020", "status": "published"}
    And admin's page /resources/resource/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains Wymagany format protokołu to https://

  Scenario: Resource creation fails without title in form
    Given dataset with id 999
    When admin's request method is POST
    And admin's request posted resource data is {"title": "", "description": "Opis zasobu", "switcher": "link", "file": "", "link": "https://test.to.resource.pl/1.xls", "dataset": 999, "data_date": "22.05.2020", "status": "published"}
    And admin's page /resources/resource/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains required id="id_title"></textarea><span class="help-inline"><ul class="errorlist"><li>To pole jest obowiązkowe.</li></ul>

  Scenario: Restored draft api resource doesnt validate local file
    Given draft remote file resource of api type with id 998
    Then set status to published on resource with id 998
    And resource with id 998 attributes are equal {"file_tasks_last_status": "", "link_tasks_last_status": "SUCCESS", "type": "api"}

  Scenario: Resource creation with regions is ok and regions are imported from api
    Given dataset with id 999
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test", "description": "more than 20 characters", "switcher": "link", "file": "", "link": "https://test.to.resource.pl/1.xls", "dataset": 999, "data_date": "22.05.2020", "status": "published", "regions": [101752777, 1309742673]}
    And admin's page with mocked geo api /resources/resource/add/ is requested
    Then admin's response status code is 200
    And resource has assigned main and additional regions
    And admin's response page contains /change/">test</a>" został pomyślnie dodany.

  Scenario: No Copy to new resource button creation page
    Given admin's request logged user is active user
    When admin's page /resources/resource/add/ is requested
    Then admin's response status code is 200
    And admin's response page not contains Kopiuj do nowego
    And admin's response page not contains <a href="/resources/resource/add/?from_id=

@elasticsearch
Feature: Resource with file creation
  Scenario: Resource with file creation is ok
    Given dataset with id 999
    When admin's request method is POST
    And admin's request posted resource data is {"title": "test resource title", "description": "more than 20 characters", "switcher": "file", "link": "", "dataset": 999, "data_date": "22.05.2020", "status": "published"}
    And request resource posted data contains simple file
    And admin's page /resources/resource/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">test resource title</a>" został pomyślnie dodany.
    And resource has assigned file
