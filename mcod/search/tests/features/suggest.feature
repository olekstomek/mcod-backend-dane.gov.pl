@elasticsearch
Feature: Search suggestions

  Scenario: Invalid value of max_length parameter returns proper error message in response
    Given article with id 999 and title is Test search suggestion article 999
    And another article with id 998 and title is Test search suggestion article 998
    When api request method is GET
    And api request path is /search/suggest/?q=suggestion&models=article&per_model=2&max_length=101
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field errors/[0]/detail is Invalid maximum list length

  Scenario: Invalid value of models parameter returns proper error message in response
    Given article with id 999 and title is test
    When api request method is GET
    And api request path is /search/suggest/?models=INVALID
    And send api request and fetch the response
    Then api's response status code is 422
    And api's response body field errors/[0]/detail is Wprowadzony model - INVALID, nie jest wspierany
