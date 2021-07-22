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
    And admin's request posted resource data is {"title": "test", "description": "more than 20 characters", "switcher": "link", "file": "", "link": "http://test.to.resource.pl/1.xls", "dataset": 999, "data_date": "22.05.2020", "status": "published"}
    And admin's page /resources/resource/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains /change/">test</a>" został pomyślnie dodany.

  Scenario: Resource creation fails without title in form
    Given dataset with id 999
    When admin's request method is POST
    And admin's request posted resource data is {"title": "", "description": "Opis zasobu", "switcher": "link", "file": "", "link": "http://test.to.resource.pl/1.xls", "dataset": 999, "data_date": "22.05.2020", "status": "published"}
    And admin's page /resources/resource/add/ is requested
    Then admin's response status code is 200
    And admin's response page contains required id="id_title"></textarea><span class="help-inline"><ul class="errorlist"><li>To pole jest obowiązkowe.</li></ul>
