Feature: Datasource import

  Scenario: CKAN resources are properly imported
    Given active ckan_datasource with id 100 for data {"portal_url": "http://mock-portal.pl", "api_url": "http://api.mock-portal.pl/items"}
    When ckan datasource with id 100 finishes importing objects
    Then ckan datasource with id 100 created all data in db

  Scenario: XML resources are properly imported
    Given active xml_datasource with id 101 for data {"xml_url": "http://api.mock-portal.pl/some-xml.xml"}
    When xml datasource with id 101 of version 1.2 finishes importing objects
    Then xml datasource with id 101 of version 1.2 created all data in db

  Scenario: XML resources are properly imported
    Given active xml_datasource with id 102 for data {"xml_url": "http://api.mock-portal.pl/some-xml.xml"}
    When xml datasource with id 102 of version 1.5 finishes importing objects
    Then xml datasource with id 102 of version 1.5 created all data in db

  Scenario: DCAT resources are properly imported
    Given active dcat_datasource with id 101 for data {"api_url": "http://api.mock-portal.pl/dcat/endpoint"}
    When dcat datasource with id 101 finishes importing objects
    Then dcat datasource with id 101 created all data in db
