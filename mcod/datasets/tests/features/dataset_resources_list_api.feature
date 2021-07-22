@elasticsearch
Feature: Dataset resources list API
  Scenario: Test dataset resources list is sorted by views_count ascendingly in API 1.0
    Given dataset with id 999 and 3 resources
    When api request method is GET
    And api request path is /1.0/datasets/999/resources
    Then api request param sort is views_count
    And send api request and fetch the response
    And api's response status code is 200
    And api's response list is sorted by views_count ascendingly

  Scenario: Test dataset resources list is sorted by views_count ascendingly in API 1.4
    Given dataset with id 999 and 3 resources
    When api request method is GET
    And api request path is /1.4/datasets/999/resources
    Then api request param sort is views_count
    And send api request and fetch the response
    And api's response status code is 200
    And api's response list is sorted by views_count ascendingly

  Scenario: Test dataset resources list is sorted by views_count descendingly in API 1.0
    Given dataset with id 999 and 3 resources
    When api request method is GET
    And api request path is /1.0/datasets/999/resources
    Then api request param sort is -views_count
    And send api request and fetch the response
    And api's response status code is 200
    And api's response list is sorted by views_count descendingly

  Scenario: Test dataset resources list is sorted by views_count descendingly in API 1.4
    Given dataset with id 999 and 3 resources
    When api request method is GET
    And api request path is /1.4/datasets/999/resources
    Then api request param sort is -views_count
    And send api request and fetch the response
    And api's response status code is 200
    And api's response list is sorted by views_count descendingly
