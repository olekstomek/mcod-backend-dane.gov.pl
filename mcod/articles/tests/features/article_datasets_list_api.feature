@elasticsearch
Feature: Article datasets list API
  Scenario: Test article datasets on list contain valid links to related items
    Given article with id 999 with 3 datasets
    When api request method is GET
    And api request path is /1.4/articles/999/datasets
    Then send api request and fetch the response
    And api's response status code is 200
    And api's response datasets contain valid links to related resources
