Feature: Datasets details API

  Scenario: Dataset details api returns license conditions description
    Given institution created with params {"id": 1000, "slug": "test-institution-slug", "institution_type": "local"}
    And dataset with id 999 and organization_id is 1000 and license_condition_cc40_responsibilities is True
    When api request path is /1.4/datasets/999
    And send api request and fetch the response
    Then api's response status code is 200
    And api's response body field data/attributes/current_condition_descriptions/license_condition_cc40_responsibilities endswith Zakres odpowiedzialności podmiotu udostępniającego informacje sektora publicznego (dostawcy) za  udostępniane dane zgodny z warunkami licencji CC BY 4.0

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
