Feature: Datasets details API

  Scenario: Test dataset formats attribute contains format of related published resource
    Given dataset with id 999
    And resource created with params {"id": 999, "dataset_id": 999, "format": "csv"}
    When api request method is GET
    And api request path is /datasets/999
    Then send api request and fetch the response
    And api's response body field data/attributes has items {"formats": ["csv"]}

  Scenario: Test dataset formats attribute doesnt contains format of related draft resource
    Given dataset with id 999
    And resource created with params {"id": 999, "dataset_id": 999, "format": "csv", "status": "draft"}
    When api request method is GET
    And api request path is /datasets/999
    Then send api request and fetch the response
    And api's response body field data/attributes has items {"formats": []}
